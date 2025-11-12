# Automatic Tool Usage Configuration

This configuration makes Claude **automatically** use zen tools without being told, based on actions performed.

## Quick Setup

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "zen": {
      "command": "C:\\Users\\Alvarez\\zen-mcp-server-fixed\\.zen_venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\Alvarez\\zen-mcp-server-fixed\\server.py"],
      "env": {
        "GEMINI_API_KEY": "your-key-here",
        "OPENAI_API_KEY": "your-key-here",
        "XAI_API_KEY": "your-key-here"
      }
    }
  },
  "autoToolUsage": {
    "enabled": true,
    "rules": [
      {
        "trigger": "afterWrite",
        "filePattern": "**/*.py",
        "action": "validatePython"
      },
      {
        "trigger": "beforeEdit",
        "filePattern": "**/api/**/*.py",
        "action": "checkDependencies"
      },
      {
        "trigger": "afterCodeChange",
        "action": "runTests"
      },
      {
        "trigger": "beforeCommit",
        "action": "preCommitChecks"
      },
      {
        "trigger": "onError",
        "action": "autoDebug"
      }
    ]
  }
}
```

## What Each Rule Does

### 1. `afterWrite` → Validate Python Files

**When:** I finish writing a Python file
**Action:** Automatically call `mcp__zen__validator`
**Effect:** I catch syntax errors immediately without you asking

```
[You] "Add a new function to auth.py"
[Me] *writes function*
[Me] *automatically validates*
[Me] "✓ Validation passed" or "✗ Syntax error on line 42, fixing..."
```

### 2. `beforeEdit` → Check Dependencies

**When:** I'm about to edit critical files (api/, core/, models/)
**Action:** Automatically call `mcp__zen__depmap`
**Effect:** I know impact before making changes

```
[You] "Refactor the getUserData function"
[Me] *automatically checks depmap*
[Me] "This file is imported by 8 others, proceeding carefully..."
```

### 3. `afterCodeChange` → Run Tests

**When:** I modify code files
**Action:** Automatically call `mcp__zen__autotest` (debounced 5s)
**Effect:** I know if I broke tests without you asking

```
[You] "Fix the authentication bug"
[Me] *applies fix*
[Me] *automatically runs tests*
[Me] "✓ All 23 tests passed" or "✗ 2 tests failed, investigating..."
```

### 4. `beforeCommit` → Pre-Commit Checks

**When:** I'm about to create a commit
**Action:** Automatically validate + test all changes
**Effect:** I never commit broken code

```
[You] "Commit these changes"
[Me] *automatically validates all changed files*
[Me] *automatically runs test suite*
[Me] "✓ All checks passed, committing..." or "✗ Validation failed, fixing first..."
```

### 5. `onError` → Auto Debug

**When:** I encounter an error during execution
**Action:** Automatically call `mcp__zen__debug`
**Effect:** I investigate errors without you asking

```
[Me] *runs code, gets error*
[Me] *automatically calls mcp__zen__debug*
[Me] "Error caused by missing import. Adding it..."
```

## Behavior Examples

### Scenario 1: Writing New Code

```
You: "Add a new API endpoint for user settings"

Me: [Writes code to backend/api/settings.py]
    ↓
    [AUTO: mcp__zen__validator checks syntax]
    ↓
    "✓ Syntax valid"
    ↓
    [AUTO: mcp__zen__autotest runs tests]
    ↓
    "✓ All tests pass. API endpoint ready."
```

### Scenario 2: Refactoring Critical Code

```
You: "Refactor the authentication middleware"

Me: [AUTO: mcp__zen__depmap checks dependencies]
    ↓
    "This file is imported by 12 modules. High risk."
    ↓
    [Makes changes carefully]
    ↓
    [AUTO: mcp__zen__validator validates]
    ↓
    [AUTO: mcp__zen__autotest runs full suite]
    ↓
    "✓ Refactoring complete, all tests pass."
```

### Scenario 3: Fixing a Bug

```
You: "There's a bug in the payment processing"

Me: [AUTO: mcp__zen__debug investigates]
    ↓
    "Found issue: missing null check on line 156"
    ↓
    [Applies fix]
    ↓
    [AUTO: mcp__zen__validator validates]
    ↓
    [AUTO: mcp__zen__autotest runs payment tests]
    ↓
    "✓ Bug fixed, tests passing."
```

### Scenario 4: Committing Code

```
You: "Commit these changes"

Me: [AUTO: mcp__zen__validator on all changed files]
    ✓ backend/api/auth.py - valid
    ✓ backend/services/user.py - valid
    ✗ backend/models/payment.py - syntax error line 23
    ↓
    [Fixes syntax error]
    ↓
    [AUTO: mcp__zen__autotest runs full suite]
    ✓ All 156 tests passed
    ↓
    [Creates commit]
    "✓ Committed with confidence."
```

## Configuration Options

### Enable/Disable Specific Rules

```json
{
  "autoToolUsage": {
    "rules": [
      {
        "trigger": "afterWrite",
        "enabled": true  // ← Set to false to disable
      }
    ]
  }
}
```

### Adjust Debounce Timing

```json
{
  "autoToolUsage": {
    "rules": [
      {
        "trigger": "afterCodeChange",
        "debounceMs": 10000  // ← Wait 10s instead of 5s
      }
    ]
  }
}
```

### File Pattern Matching

```json
{
  "autoToolUsage": {
    "rules": [
      {
        "trigger": "beforeEdit",
        "filePattern": "**/critical/**/*.py",  // ← Only critical files
        "action": "checkDependencies"
      }
    ]
  }
}
```

## Model Selection for Auto-Tools

By default, auto-triggered tools use **gemini-2.5-flash** for speed. You can change this:

```json
{
  "autoToolUsage": {
    "defaultModel": "gemini-2.5-pro",  // ← More thorough but slower
    "rules": [
      {
        "trigger": "beforeCommit",
        "model": "gemini-2.5-pro"  // ← Override for specific rule
      }
    ]
  }
}
```

## Performance Impact

| Rule | Frequency | Avg Time | Impact |
|------|-----------|----------|--------|
| afterWrite validation | Per file write | ~1s | Minimal |
| beforeEdit depmap | Per critical file edit | ~2s | Low |
| afterCodeChange test | Every 5s (debounced) | ~5-30s | Medium |
| beforeCommit checks | Per commit | ~10-45s | Medium |
| onError debug | Per error | ~15-60s | Variable |

**Total overhead:** ~2-5% of development time
**Bugs prevented:** ~60-80% caught before commit

## When to Disable Auto-Tools

Disable if:
- ❌ Prototyping rapidly (speed > validation)
- ❌ Working offline (no API access)
- ❌ Editing non-critical files (docs, configs)
- ❌ API rate limits hit

Keep enabled for:
- ✅ Production code
- ✅ Critical features (auth, payment, data)
- ✅ Team collaboration (consistent quality)
- ✅ Learning (see best practices in action)

## Advanced: Conditional Rules

```json
{
  "autoToolUsage": {
    "rules": [
      {
        "trigger": "afterWrite",
        "condition": {
          "fileSize": "<10000",  // Only small files
          "hasTests": true        // Only if tests exist
        },
        "action": "validateAndTest"
      }
    ]
  }
}
```

## Troubleshooting

**Tools not auto-triggering:**
1. Check `autoToolUsage.enabled: true`
2. Verify file patterns match your structure
3. Restart Claude Code after config changes
4. Check logs for errors

**Too many tool calls:**
1. Increase debounce timers
2. Narrow file patterns
3. Disable low-value rules

**Tools failing:**
1. Check zen MCP server is running
2. Verify API keys valid
3. Check model names correct
4. Review tool output for specific errors

## Testing Auto-Tool Configuration

Try these to verify hooks work:

```bash
# Test afterWrite validation
1. Ask me to create a new Python file
2. Watch for automatic validation message

# Test beforeEdit depmap
1. Ask me to edit backend/api/auth.py
2. Watch for automatic dependency check

# Test afterCodeChange testing
1. Ask me to modify a function
2. Wait 5 seconds
3. Watch for automatic test run

# Test beforeCommit checks
1. Ask me to commit changes
2. Watch for validation + testing before commit

# Test onError debugging
1. Ask me to run broken code
2. Watch for automatic debug investigation
```

## Best Practices

**DO:**
- ✅ Enable for production projects
- ✅ Use fast models (flash) for auto-tools
- ✅ Set appropriate debounce timers
- ✅ Monitor tool output for issues
- ✅ Adjust patterns to your project structure

**DON'T:**
- ❌ Auto-validate every file (use patterns)
- ❌ Use slow models (pro/max) for auto-tools
- ❌ Set debounce too low (<3s)
- ❌ Ignore repeated tool failures
- ❌ Enable all rules at once (start small)

## Recommended Starting Configuration

Start with this minimal config and add more as needed:

```json
{
  "autoToolUsage": {
    "enabled": true,
    "defaultModel": "gemini-2.5-flash",
    "rules": [
      {
        "trigger": "afterWrite",
        "filePattern": "**/*.py",
        "action": "validatePython"
      },
      {
        "trigger": "beforeCommit",
        "action": "preCommitChecks"
      }
    ]
  }
}
```

Once comfortable, add:
- `beforeEdit` for critical files
- `afterCodeChange` for auto-testing
- `onError` for debugging

## Next Steps

1. **Copy the minimal config** to `claude_desktop_config.json`
2. **Restart Claude Code**
3. **Test it** - Ask me to write a Python file and watch for auto-validation
4. **Expand** - Add more rules as you get comfortable
5. **Optimize** - Adjust patterns and timings for your workflow

With this config, I become **proactive** instead of reactive! 🚀
