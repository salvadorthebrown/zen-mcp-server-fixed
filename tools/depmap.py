"""
Dependency Mapper Tool - Visualizes import relationships for files

Shows what a file imports and what files import it, helping understand
code dependencies and potential breakage when making changes.
"""

import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from pydantic import Field

if TYPE_CHECKING:
    from providers.shared import ModelCapabilities
    from tools.models import ToolModelCategory

from config import TEMPERATURE_BALANCED
from tools.shared.base_models import COMMON_FIELD_DESCRIPTIONS, ToolRequest

from .simple.base import SimpleTool

logger = logging.getLogger(__name__)


class DepMapRequest(ToolRequest):
    """Request model for DepMap tool"""

    target_file: str = Field(..., description="Absolute path to the file to analyze")
    working_directory: str = Field(..., description="Absolute path to the project root directory")
    depth: Optional[int] = Field(
        default=1,
        description="How many levels deep to trace (1=direct only, 2=includes dependencies of dependencies)",
    )


class DepMapTool(SimpleTool):
    """
    Maps import dependencies for a given file.

    Shows what the file imports and what other files import it,
    helping you understand potential impacts when making changes.
    """

    def __init__(self) -> None:
        super().__init__()
        self._last_recordable_response: Optional[str] = None

    def get_name(self) -> str:
        return "depmap"

    def get_description(self) -> str:
        return (
            "Maps import dependencies for Python files. "
            "Shows what a file imports (outgoing) and what imports it (incoming). "
            "Helps identify potential breakage when modifying code."
        )

    def get_annotations(self) -> Optional[dict[str, Any]]:
        return {"readOnlyHint": True}

    def get_system_prompt(self) -> str:
        return """You are a dependency analysis assistant. Your job is to:
1. Analyze import statements in the target file
2. Find all files that import the target file
3. Present a clear dependency map showing relationships
4. Highlight high-risk changes (many incoming dependencies)

Be concise but thorough. Focus on actionable insights.
"""

    def get_capability_system_prompts(self, capabilities: Optional["ModelCapabilities"]) -> list[str]:
        return list(super().get_capability_system_prompts(capabilities))

    def get_default_temperature(self) -> float:
        return TEMPERATURE_BALANCED

    def get_model_category(self) -> "ToolModelCategory":
        from tools.models import ToolModelCategory

        return ToolModelCategory.FAST_RESPONSE

    def get_request_model(self):
        return DepMapRequest

    def get_input_schema(self) -> dict[str, Any]:
        required_fields = ["target_file", "working_directory"]
        if self.is_effective_auto_mode():
            required_fields.append("model")

        schema = {
            "type": "object",
            "properties": {
                "target_file": {
                    "type": "string",
                    "description": "Absolute path to the file to analyze",
                },
                "working_directory": {
                    "type": "string",
                    "description": "Absolute path to the project root directory",
                },
                "depth": {
                    "type": "integer",
                    "description": "Dependency depth (1=direct, 2=includes deps of deps)",
                    "default": 1,
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
            "target_file": {
                "type": "string",
                "description": "Absolute path to the file to analyze",
            },
            "working_directory": {
                "type": "string",
                "description": "Absolute path to the project root directory",
            },
            "depth": {
                "type": "integer",
                "description": "Dependency depth (default: 1)",
            },
        }

    def get_required_fields(self) -> list[str]:
        return ["target_file", "working_directory"]

    async def prepare_prompt(self, request: DepMapRequest) -> str:
        """
        Prepare the prompt by:
        1. Analyzing imports in the target file
        2. Finding all files that import the target
        3. Formatting results for the model to analyze
        """

        target_file = Path(request.target_file)
        working_dir = Path(request.working_directory)

        if not target_file.exists():
            return f"Error: Target file does not exist: {target_file}"

        if not working_dir.exists():
            return f"Error: Working directory does not exist: {working_dir}"

        # Get relative path for cleaner output
        try:
            rel_path = target_file.relative_to(working_dir)
        except ValueError:
            rel_path = target_file

        # Analyze outgoing dependencies (what this file imports)
        outgoing = self._analyze_imports(target_file)

        # Analyze incoming dependencies (what imports this file)
        incoming = self._find_importers(target_file, working_dir)

        # Format results
        prompt = f"""
DEPENDENCY MAP FOR: {rel_path}
{'=' * 80}

OUTGOING DEPENDENCIES (What this file imports):
{self._format_dependencies(outgoing, "  ")}

INCOMING DEPENDENCIES (What imports this file):
{self._format_dependencies(incoming, "  ")}

{'=' * 80}

Analyze this dependency map and provide:
1. Summary of dependency complexity
2. Risk assessment (how many files would break if this changes?)
3. Suggestions for safe refactoring
4. Any circular dependencies detected
"""

        return prompt

    def _analyze_imports(self, file_path: Path) -> list[dict[str, str]]:
        """Extract import statements from a Python file"""
        imports = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Pattern 1: import module
            for match in re.finditer(r"^import\s+([\w.]+)", content, re.MULTILINE):
                imports.append({"type": "import", "module": match.group(1), "items": None})

            # Pattern 2: from module import item1, item2
            for match in re.finditer(r"^from\s+([\w.]+)\s+import\s+(.+)", content, re.MULTILINE):
                module = match.group(1)
                items = match.group(2).strip()
                imports.append({"type": "from", "module": module, "items": items})

        except Exception as e:
            logger.error(f"Error analyzing imports in {file_path}: {e}")

        return imports

    def _find_importers(self, target_file: Path, working_dir: Path) -> list[dict[str, Any]]:
        """Find all Python files that import the target file"""
        importers = []

        try:
            # Get module name from file path
            rel_path = target_file.relative_to(working_dir)
            module_path = str(rel_path.with_suffix("")).replace(os.sep, ".")

            # Also check for __init__.py cases
            if target_file.name == "__init__.py":
                module_path = str(rel_path.parent).replace(os.sep, ".")

            # Search all Python files
            for py_file in working_dir.rglob("*.py"):
                if py_file == target_file:
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Check for imports of this module
                    patterns = [
                        rf"^import\s+{re.escape(module_path)}\b",
                        rf"^from\s+{re.escape(module_path)}\s+import",
                        # Also check for relative imports if in same package
                        rf"^from\s+\.+{re.escape(target_file.stem)}\s+import",
                    ]

                    for pattern in patterns:
                        if re.search(pattern, content, re.MULTILINE):
                            rel_importer = py_file.relative_to(working_dir)
                            importers.append({"file": str(rel_importer), "type": "direct"})
                            break

                except Exception as e:
                    logger.debug(f"Error reading {py_file}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error finding importers: {e}")

        return importers

    def _format_dependencies(self, deps: list[dict], indent: str) -> str:
        """Format dependency list for output"""
        if not deps:
            return f"{indent}(none)"

        lines = []
        for dep in deps:
            if "module" in dep:
                # Outgoing dependency
                if dep["type"] == "import":
                    lines.append(f"{indent}• import {dep['module']}")
                else:
                    lines.append(f"{indent}• from {dep['module']} import {dep['items']}")
            elif "file" in dep:
                # Incoming dependency
                lines.append(f"{indent}• {dep['file']}")

        return "\n".join(lines)
