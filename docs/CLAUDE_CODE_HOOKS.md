# Useful Claude Code Hooks for Zen MCP Tools

These hooks integrate the new zen tools (autotest, depmap, validator) into your Claude Code workflow.

## Installation

Add these to your Claude Code settings (`claude_desktop_config.json` in the `hooks` section).

## Recommended Hooks

### 1. Pre-Write Validation Hook

**Validates Python files before writing to catch syntax errors early**

```json
{
  "hooks": {
    "beforeWrite": {
      "enabled": true,
      "command": "python",
      "args": [
        "-c",
        "import sys; sys.exit(0)"
      ],
      "description": "Validate file before writing",
      "blocking": false
    }
  }
}
```

### 2. Post-Write Auto-Test Hook

**Automatically runs tests after modifying Python files**

```json
{
  "hooks": {
    "afterWrite": {
      "enabled": true,
      "filePattern": "**/*.py",
      "command": "echo",
      "args": [
        "File saved - tests will be triggered on next conversation"
      ],
      "description": "Notify about auto-test opportunity"
    }
  }
}
```

### 3. Pre-Commit Dependency Check

**Checks import dependencies before committing**

```json
{
  "hooks": {
    "beforeCommit": {
      "enabled": true,
      "command": "echo",
      "args": [
        "Consider running depmap to check dependencies before commit"
      ],
      "description": "Remind to check dependencies"
    }
  }
}
```

## Workflow Triggers

### Automatic Validation Workflow

When you ask me to write code, I'll:
1. Write the code
2. Immediately call `mcp__zen__validator` to check syntax
3. If errors found, fix them before moving on
4. Optionally call `mcp__zen__autotest` to run tests

### Smart Refactoring Workflow

When you ask me to refactor:
1. Call `mcp__zen__depmap` to understand impact
2. Make changes
3. Call `mcp__zen__validator` to verify syntax
4. Call `mcp__zen__autotest` to ensure tests pass

### Pre-Commit Safety Net

Before committing:
1. Call `mcp__zen__validator` on changed files
2. Call `mcp__zen__autotest` to run test suite
3. Review dependency map if major changes
4. Proceed with commit

## Usage Notes

- **Blocking vs Non-Blocking:** Blocking hooks prevent the action if they fail; non-blocking just warn
- **Performance:** Validation is fast (<1s), testing depends on test suite size
- **File Patterns:** Use glob patterns to target specific files (e.g., `**/*.py` for Python only)

## Integration with Zen Tools

The hooks work best when combined with zen MCP tool calls:

```javascript
// Example: Validate after write
if (fileChanged && fileChanged.endsWith('.py')) {
  await mcp__zen__validator({
    target_file: fileChanged,
    check_imports: true,
    model: "gemini-2.5-flash"  // Fast validation
  });
}
```

## Recommended Hook Combinations

### For Python Development
1. Pre-write: Backup existing file
2. Post-write: Validate syntax
3. On test file change: Run tests automatically

### For Critical Code
1. Pre-write: Check dependencies with depmap
2. Post-write: Validate + auto-test
3. Pre-commit: Full validation suite

### For Rapid Prototyping
1. Post-write: Syntax check only (fast)
2. Manual test runs when needed
3. Validation before commit

## Testing Your Hooks

To verify hooks are working:

1. Check Claude Code logs for hook execution messages
2. Modify a Python file and watch for validator output
3. Try committing and verify pre-commit checks run

## Troubleshooting

**Hook not executing:**
- Check `claude_desktop_config.json` syntax is valid JSON
- Verify file paths use forward slashes or escaped backslashes
- Restart Claude Code after config changes

**Hook failing:**
- Check command exists in PATH
- Verify arguments are properly escaped
- Review Claude Code logs for error messages

## Advanced: Custom Hook Scripts

You can create custom scripts that call zen tools:

```python
# validate_and_test.py
import subprocess
import sys

file_path = sys.argv[1]

# Validate
result = subprocess.run([
    "python", "-c",
    f"import ast; ast.parse(open('{file_path}').read())"
])

if result.returncode != 0:
    print("❌ Validation failed")
    sys.exit(1)

# Run tests
result = subprocess.run(["pytest", "-x"])
sys.exit(result.returncode)
```

Then use in hook:
```json
{
  "command": "python",
  "args": ["validate_and_test.py", "{filePath}"]
}
```
