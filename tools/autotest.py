"""
Auto-Test Runner Tool - Automatically runs relevant tests for changed files

This tool detects which files have been modified and runs the related test suite,
helping catch bugs immediately before committing code.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from pydantic import Field

if TYPE_CHECKING:
    from providers.shared import ModelCapabilities
    from tools.models import ToolModelCategory

from config import TEMPERATURE_BALANCED
from systemprompts import CHAT_PROMPT
from tools.shared.base_models import COMMON_FIELD_DESCRIPTIONS, ToolRequest

from .simple.base import SimpleTool

logger = logging.getLogger(__name__)


class AutoTestRequest(ToolRequest):
    """Request model for AutoTest tool"""

    working_directory: str = Field(..., description="Absolute path to the project root directory")
    changed_files: Optional[list[str]] = Field(
        default=None,
        description="Optional list of files that were changed (if not provided, will detect via git)",
    )
    test_framework: Optional[str] = Field(
        default="pytest",
        description="Test framework to use (pytest, unittest, etc.)",
    )


class AutoTestTool(SimpleTool):
    """
    Automatically runs relevant tests for recently changed files.

    This tool helps catch bugs early by running tests immediately after code changes,
    before committing or deploying.
    """

    def __init__(self) -> None:
        super().__init__()
        self._last_recordable_response: Optional[str] = None

    def get_name(self) -> str:
        return "autotest"

    def get_description(self) -> str:
        return (
            "Automatically runs relevant tests for changed files. "
            "Detects modified files via git and runs their test suites. "
            "Shows pass/fail results immediately so you can fix issues before committing."
        )

    def get_annotations(self) -> Optional[dict[str, Any]]:
        return {"readOnlyHint": True}

    def get_system_prompt(self) -> str:
        return """You are an auto-test assistant. Your job is to:
1. Detect which files have been changed
2. Find relevant test files for those changes
3. Run the tests and report results clearly
4. Highlight any failures with actionable suggestions

Be concise but thorough. Focus on FAILED tests first, then show summary.
"""

    def get_capability_system_prompts(self, capabilities: Optional["ModelCapabilities"]) -> list[str]:
        return list(super().get_capability_system_prompts(capabilities))

    def get_default_temperature(self) -> float:
        return TEMPERATURE_BALANCED

    def get_model_category(self) -> "ToolModelCategory":
        from tools.models import ToolModelCategory

        return ToolModelCategory.FAST_RESPONSE

    def get_request_model(self):
        return AutoTestRequest

    def get_input_schema(self) -> dict[str, Any]:
        required_fields = ["working_directory"]
        if self.is_effective_auto_mode():
            required_fields.append("model")

        schema = {
            "type": "object",
            "properties": {
                "working_directory": {
                    "type": "string",
                    "description": "Absolute path to the project root directory",
                },
                "changed_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of changed files (auto-detects via git if not provided)",
                },
                "test_framework": {
                    "type": "string",
                    "description": "Test framework to use (default: pytest)",
                },
                "model": self.get_model_field_schema(),
                "temperature": {
                    "type": "number",
                    "description": COMMON_FIELD_DESCRIPTIONS["temperature"],
                    "minimum": 0,
                    "maximum": 1,
                },
                "thinking_mode": {
                    "type": "string",
                    "enum": ["minimal", "low", "medium", "high", "max"],
                    "description": COMMON_FIELD_DESCRIPTIONS["thinking_mode"],
                },
                "continuation_id": {
                    "type": "string",
                    "description": COMMON_FIELD_DESCRIPTIONS["continuation_id"],
                },
            },
            "required": required_fields,
            "additionalProperties": False,
        }

        return schema

    def get_tool_fields(self) -> dict[str, dict[str, Any]]:
        return {
            "working_directory": {
                "type": "string",
                "description": "Absolute path to the project root directory",
            },
            "changed_files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of changed files",
            },
            "test_framework": {
                "type": "string",
                "description": "Test framework to use (default: pytest)",
            },
        }

    def get_required_fields(self) -> list[str]:
        return ["working_directory"]

    async def prepare_prompt(self, request: AutoTestRequest) -> str:
        """
        Prepare the prompt by:
        1. Detecting changed files (via git or explicit list)
        2. Finding relevant test files
        3. Running the tests
        4. Formatting results for the model to analyze
        """

        working_dir = Path(request.working_directory)
        if not working_dir.exists():
            return f"Error: Working directory does not exist: {working_dir}"

        # Get changed files
        if request.changed_files:
            changed_files = request.changed_files
            logger.info(f"Using provided changed files: {changed_files}")
        else:
            # Auto-detect via git
            changed_files = self._get_git_changed_files(working_dir)
            logger.info(f"Auto-detected changed files: {changed_files}")

        if not changed_files:
            return "No changed files detected. Make some changes or specify files explicitly."

        # Find relevant test files
        test_files = self._find_relevant_tests(working_dir, changed_files, request.test_framework)

        if not test_files:
            return f"No test files found for changed files: {changed_files}"

        # Run tests
        test_results = self._run_tests(working_dir, test_files, request.test_framework)

        # Format results for model
        prompt = f"""
TEST RESULTS FOR CHANGED FILES
================================

Changed Files:
{chr(10).join(f"  - {f}" for f in changed_files)}

Test Files Run:
{chr(10).join(f"  - {f}" for f in test_files)}

Test Output:
{test_results}

================================

Analyze these test results and provide:
1. Summary (X passed, Y failed)
2. Failed tests with specific error details
3. Suggestions to fix failures
4. Any warnings or issues to address
"""

        return prompt

    def _get_git_changed_files(self, working_dir: Path) -> list[str]:
        """Detect changed files via git status"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                logger.warning(f"Git diff failed: {result.stderr}")
                return []

            files = [f.strip() for f in result.stdout.split("\n") if f.strip()]

            # Also get unstaged changes
            result2 = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result2.returncode == 0:
                unstaged = [f.strip() for f in result2.stdout.split("\n") if f.strip()]
                files.extend(unstaged)

            # Remove duplicates
            return list(set(files))

        except Exception as e:
            logger.error(f"Error detecting git changes: {e}")
            return []

    def _find_relevant_tests(self, working_dir: Path, changed_files: list[str], framework: str) -> list[str]:
        """Find test files related to changed source files"""
        test_files = set()

        for changed_file in changed_files:
            file_path = Path(changed_file)

            # If it's already a test file, include it
            if "test" in file_path.name or file_path.parts and "test" in file_path.parts[0]:
                test_files.add(changed_file)
                continue

            # Try to find corresponding test file
            # Pattern 1: test_<filename>.py in tests/ dir
            test_name = f"test_{file_path.stem}.py"
            test_path = working_dir / "tests" / test_name
            if test_path.exists():
                test_files.add(str(test_path.relative_to(working_dir)))

            # Pattern 2: test_<filename>.py in same directory
            test_path2 = file_path.parent / test_name
            if test_path2.exists():
                test_files.add(str(test_path2.relative_to(working_dir)))

        # If no specific tests found, run all tests
        if not test_files:
            logger.info("No specific test files found, will run full test suite")
            if (working_dir / "tests").exists():
                test_files.add("tests/")

        return list(test_files)

    def _run_tests(self, working_dir: Path, test_files: list[str], framework: str) -> str:
        """Run tests and capture output"""
        try:
            if framework == "pytest":
                cmd = ["pytest", "-v", "--tb=short"] + test_files
            elif framework == "unittest":
                cmd = ["python", "-m", "unittest"] + test_files
            else:
                return f"Unsupported test framework: {framework}"

            logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            output = result.stdout + "\n" + result.stderr

            # Limit output size
            if len(output) > 10000:
                output = output[:10000] + "\n\n[Output truncated - too long]"

            return output

        except subprocess.TimeoutExpired:
            return "ERROR: Tests timed out after 5 minutes"
        except Exception as e:
            return f"ERROR running tests: {str(e)}"
