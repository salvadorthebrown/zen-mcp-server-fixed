"""
Live Validation Tool - Validates code syntax and imports without execution

Checks Python files for syntax errors, import issues, and common problems
before running code, helping catch errors early in development.
"""

import ast
import importlib.util
import logging
import os
import sys
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


class ValidatorRequest(ToolRequest):
    """Request model for Validator tool"""

    target_file: str = Field(..., description="Absolute path to the file to validate")
    check_imports: Optional[bool] = Field(
        default=True,
        description="Whether to verify imports can be resolved (default: True)",
    )
    check_types: Optional[bool] = Field(
        default=False,
        description="Whether to perform basic type checking (default: False)",
    )


class ValidatorTool(SimpleTool):
    """
    Validates Python code syntax and imports without execution.

    Catches errors early by checking:
    - Syntax errors (compile check)
    - Import resolution
    - Unused imports
    - Basic type consistency (if enabled)
    """

    def __init__(self) -> None:
        super().__init__()
        self._last_recordable_response: Optional[str] = None

    def get_name(self) -> str:
        return "validator"

    def get_description(self) -> str:
        return (
            "Validates Python code syntax and imports without execution. "
            "Checks for syntax errors, unresolvable imports, and common issues. "
            "Helps catch errors before running code."
        )

    def get_annotations(self) -> Optional[dict[str, Any]]:
        return {"readOnlyHint": True}

    def get_system_prompt(self) -> str:
        return """You are a code validation assistant. Your job is to:
1. Check Python syntax for errors
2. Verify all imports can be resolved
3. Identify unused imports and variables
4. Report issues with clear explanations and line numbers

Be concise but thorough. Prioritize errors over warnings.
"""

    def get_capability_system_prompts(self, capabilities: Optional["ModelCapabilities"]) -> list[str]:
        return list(super().get_capability_system_prompts(capabilities))

    def get_default_temperature(self) -> float:
        return TEMPERATURE_BALANCED

    def get_model_category(self) -> "ToolModelCategory":
        from tools.models import ToolModelCategory

        return ToolModelCategory.FAST_RESPONSE

    def get_request_model(self):
        return ValidatorRequest

    def get_input_schema(self) -> dict[str, Any]:
        required_fields = ["target_file"]
        if self.is_effective_auto_mode():
            required_fields.append("model")

        schema = {
            "type": "object",
            "properties": {
                "target_file": {
                    "type": "string",
                    "description": "Absolute path to the file to validate",
                },
                "check_imports": {
                    "type": "boolean",
                    "description": "Verify imports can be resolved (default: True)",
                },
                "check_types": {
                    "type": "boolean",
                    "description": "Perform basic type checking (default: False)",
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
                "description": "Absolute path to the file to validate",
            },
            "check_imports": {
                "type": "boolean",
                "description": "Verify imports can be resolved",
            },
            "check_types": {
                "type": "boolean",
                "description": "Perform basic type checking",
            },
        }

    def get_required_fields(self) -> list[str]:
        return ["target_file"]

    async def prepare_prompt(self, request: ValidatorRequest) -> str:
        """
        Prepare the prompt by:
        1. Checking Python syntax
        2. Verifying imports (if enabled)
        3. Looking for unused imports
        4. Checking types (if enabled)
        """

        target_file = Path(request.target_file)

        if not target_file.exists():
            return f"Error: Target file does not exist: {target_file}"

        if not target_file.suffix == ".py":
            return f"Error: Target file must be a Python file (.py): {target_file}"

        # Read file content
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            return f"Error reading file: {e}"

        # Collect validation results
        issues = []
        warnings = []

        # 1. Syntax check
        syntax_result = self._check_syntax(code, target_file)
        if syntax_result:
            issues.append(syntax_result)

        # Only continue if syntax is valid
        if not issues:
            # 2. Import validation
            if request.check_imports:
                import_issues = self._check_imports(code, target_file)
                issues.extend(import_issues)

            # 3. Unused imports check
            unused = self._check_unused_imports(code)
            if unused:
                warnings.append(f"Unused imports: {', '.join(unused)}")

            # 4. Type checking (basic)
            if request.check_types:
                type_issues = self._check_types(code)
                warnings.extend(type_issues)

        # Format results
        status = "✗ INVALID" if issues else "✓ VALID"
        prompt = f"""
CODE VALIDATION RESULT: {status}
{'=' * 80}

File: {target_file}

"""

        if issues:
            prompt += "ERRORS:\n"
            for issue in issues:
                prompt += f"  ✗ {issue}\n"
            prompt += "\n"

        if warnings:
            prompt += "WARNINGS:\n"
            for warning in warnings:
                prompt += f"  ⚠ {warning}\n"
            prompt += "\n"

        if not issues and not warnings:
            prompt += "✓ No issues found. Code passes all validation checks.\n\n"

        prompt += f"""
{'=' * 80}

Analyze these validation results and provide:
1. Summary of critical issues (if any)
2. Explanation of each error with fix suggestions
3. Priority order for addressing issues
4. Any patterns or best practices to apply
"""

        return prompt

    def _check_syntax(self, code: str, file_path: Path) -> Optional[str]:
        """Check Python syntax by compiling"""
        try:
            compile(code, str(file_path), "exec")
            return None
        except SyntaxError as e:
            return f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return f"Compilation error: {str(e)}"

    def _check_imports(self, code: str, file_path: Path) -> list[str]:
        """Verify all imports can be resolved"""
        issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return issues  # Syntax errors already caught

        # Add file's directory to sys.path temporarily
        file_dir = str(file_path.parent)
        old_path = sys.path.copy()
        if file_dir not in sys.path:
            sys.path.insert(0, file_dir)

        try:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._can_import(alias.name):
                            issues.append(f"Cannot resolve import: {alias.name} (line {node.lineno})")

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if not self._can_import(module):
                        issues.append(f"Cannot resolve import: from {module} ... (line {node.lineno})")

        finally:
            sys.path = old_path

        return issues

    def _can_import(self, module_name: str) -> bool:
        """Check if a module can be imported"""
        if not module_name:
            return True

        try:
            # Try to find the module spec
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            return False
        except Exception:
            # Some modules raise other exceptions when checking
            return True  # Assume it's valid to avoid false positives

    def _check_unused_imports(self, code: str) -> list[str]:
        """Find imports that are never used"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        # Collect all imported names
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported.add(name)

        # Collect all used names (simplified check)
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)

        # Find unused
        unused = imported - used

        # Filter out common false positives
        # (imports used in type hints, docstrings, etc.)
        return [u for u in unused if not u.startswith("_")]

    def _check_types(self, code: str) -> list[str]:
        """Basic type consistency checking"""
        warnings = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return warnings

        # Check for functions with partial type hints
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_hints = any(
                    arg.annotation is not None for arg in node.args.args
                ) or node.returns is not None

                all_hinted = all(
                    arg.annotation is not None for arg in node.args.args
                ) and node.returns is not None

                if has_hints and not all_hinted:
                    warnings.append(
                        f"Function '{node.name}' (line {node.lineno}) has partial type hints - "
                        "consider adding hints to all parameters and return"
                    )

        return warnings
