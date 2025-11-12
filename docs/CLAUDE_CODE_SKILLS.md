# Useful Claude Code Skills for Zen MCP Tools

Skills are reusable workflow templates that combine multiple tools and actions into efficient sequences.

## What Are Skills?

Skills in Claude Code are pre-defined workflows that I can execute automatically. They combine tool calls, code analysis, and best practices into repeatable processes.

## Installation

Skills are defined in your `.claude/skills/` directory as markdown files.

## Recommended Skills

### 1. Quick Debug Skill

**File:** `.claude/skills/quick-debug.md`

```markdown
# Quick Debug

When the user reports a bug or error:

1. Use mcp__zen__debug to analyze the issue:
   - Set working_directory to project root
   - Use model: gemini-2.5-pro for deep analysis
   - Set thinking_mode: high

2. Once root cause identified:
   - Apply the fix
   - Use mcp__zen__validator to verify syntax
   - Use mcp__zen__autotest to run tests

3. Report results:
   - What was broken
   - What was fixed
   - Test results

Always validate before committing the fix.
```

### 2. Safe Refactor Skill

**File:** `.claude/skills/safe-refactor.md`

```markdown
# Safe Refactor

When the user asks to refactor code:

1. Analyze dependencies first:
   - Use mcp__zen__depmap on target file
   - Identify all files that import it
   - Assess risk level

2. Plan refactoring:
   - Use mcp__zen__refactor for analysis
   - Get user approval if high-risk

3. Apply changes:
   - Make modifications
   - Use mcp__zen__validator to check syntax
   - Use mcp__zen__autotest to verify tests pass

4. Verify no breakage:
   - Check all dependent files still work
   - Run full test suite if critical

Never refactor without checking dependencies first.
```

### 3. Feature Development Skill

**File:** `.claude/skills/feature-dev.md`

```markdown
# Feature Development

When adding a new feature:

1. Planning phase:
   - Use mcp__zen__planner to break down the feature
   - Identify affected files with mcp__zen__depmap
   - Get user approval on plan

2. Implementation phase:
   - Write feature code
   - Use mcp__zen__validator after each file
   - Keep tests passing throughout

3. Testing phase:
   - Use mcp__zen__testgen to create comprehensive tests
   - Use mcp__zen__autotest to run test suite
   - Verify coverage of edge cases

4. Documentation phase:
   - Use mcp__zen__docgen for code documentation
   - Update README if needed
   - Add usage examples

Always validate and test before marking feature complete.
```

### 4. Pre-Commit Check Skill

**File:** `.claude/skills/pre-commit.md`

```markdown
# Pre-Commit Check

Before committing code:

1. Validation checks:
   - Use mcp__zen__validator on all changed Python files
   - Check for syntax errors and import issues
   - Fix any validation errors immediately

2. Dependency analysis:
   - Use mcp__zen__depmap on modified files
   - Verify no circular dependencies introduced
   - Check impact on dependent files

3. Test verification:
   - Use mcp__zen__autotest to run full test suite
   - Ensure all tests pass
   - Fix any failing tests before commit

4. Security check (if applicable):
   - Use mcp__zen__secaudit for security-sensitive changes
   - Review any critical findings
   - Address high-severity issues

Only commit if all checks pass.
```

### 5. Bug Investigation Skill

**File:** `.claude/skills/investigate-bug.md`

```markdown
# Bug Investigation

When investigating a mysterious bug:

1. Initial analysis:
   - Use mcp__zen__debug with thinking_mode: max
   - Gather evidence from logs/errors
   - Form hypothesis about root cause

2. Dependency tracing:
   - Use mcp__zen__depmap on suspected files
   - Use mcp__zen__tracer to trace execution flow
   - Identify all code paths involved

3. Validation:
   - Use mcp__zen__validator to check for subtle errors
   - Look for type mismatches
   - Check import resolution issues

4. Fix and verify:
   - Apply targeted fix
   - Use mcp__zen__autotest to verify
   - Ensure fix doesn't break other code

Document findings for future reference.
```

### 6. Code Review Skill

**File:** `.claude/skills/code-review.md`

```markdown
# Code Review

When reviewing code (PR or local changes):

1. Comprehensive review:
   - Use mcp__zen__codereview with review_type: full
   - Use model: gemini-2.5-pro for thorough analysis
   - Set thinking_mode: high

2. Dependency analysis:
   - Use mcp__zen__depmap on changed files
   - Verify dependency graph makes sense
   - Check for unnecessary coupling

3. Validation:
   - Use mcp__zen__validator on all changed files
   - Use mcp__zen__autotest to run tests
   - Verify no regressions

4. Security check:
   - Use mcp__zen__secaudit if touching auth/data/API
   - Review security findings carefully
   - Flag any critical vulnerabilities

Provide actionable feedback with specific line references.
```

### 7. Performance Optimization Skill

**File:** `.claude/skills/optimize-performance.md`

```markdown
# Performance Optimization

When optimizing code for performance:

1. Analysis:
   - Use mcp__zen__analyze with analysis_type: performance
   - Use mcp__zen__tracer to map execution paths
   - Identify bottlenecks

2. Dependency check:
   - Use mcp__zen__depmap to understand call patterns
   - Find frequently-called functions
   - Identify caching opportunities

3. Optimization:
   - Apply performance improvements
   - Use mcp__zen__validator to verify correctness
   - Use mcp__zen__autotest to ensure behavior unchanged

4. Measurement:
   - Run performance benchmarks
   - Compare before/after metrics
   - Document improvements

Never sacrifice correctness for performance.
```

## How to Use Skills

Once skills are installed, you can invoke them by:

1. **Direct invocation:** "Use the quick-debug skill to fix this error"
2. **Implicit trigger:** I'll automatically use appropriate skill when I detect the pattern
3. **Chained skills:** "Use feature-dev skill then pre-commit skill"

## Skill Best Practices

### When to Use Skills

✅ **Do use skills for:**
- Repetitive workflows (debug, refactor, review)
- Complex multi-step processes (feature development)
- Safety-critical operations (pre-commit checks)
- Consistency across team (everyone follows same process)

❌ **Don't use skills for:**
- One-off tasks
- Simple single-tool operations
- Highly customized workflows
- Exploratory work

### Customizing Skills

You can modify these skills to match your workflow:

```markdown
# My Custom Feature Dev Skill

1. Run my custom pre-checks:
   - Verify API keys in .env
   - Check database migrations

2. Use standard feature-dev skill

3. Run my custom post-checks:
   - Update changelog
   - Notify team in Slack
```

### Skill Composition

Skills can call other skills:

```markdown
# Full Release Skill

1. Use safe-refactor skill if code changes
2. Use feature-dev skill for new features
3. Use pre-commit skill before pushing
4. Use code-review skill on final PR
```

## Awareness and Discovery

**Q: Will you (Claude) automatically know these skills exist?**

A: Yes! When skills are in `.claude/skills/`, I can:
- See them in my available tools
- Suggest them when appropriate
- Use them automatically for matching patterns
- Combine them for complex workflows

**Q: How do you know when to use a skill?**

A: I match your request pattern:
- "debug this" → quick-debug skill
- "refactor X" → safe-refactor skill
- "add feature Y" → feature-dev skill
- "review this PR" → code-review skill

## Testing Your Skills

Try these commands to test skills:

```
# Test quick-debug skill
"There's a bug in auth.py line 45, use quick-debug skill"

# Test safe-refactor skill
"Refactor the getUserData function using safe-refactor skill"

# Test pre-commit skill
"I'm about to commit, run pre-commit skill"
```

## Skill Performance

| Skill | Avg Time | Tools Used | Blocking |
|-------|----------|------------|----------|
| quick-debug | 30-60s | debug, validator, autotest | Yes |
| safe-refactor | 45-90s | depmap, refactor, validator, autotest | Yes |
| feature-dev | 2-5min | planner, validator, testgen, autotest | No |
| pre-commit | 30-45s | validator, depmap, autotest | Yes |
| investigate-bug | 60-120s | debug, depmap, tracer, validator | Yes |
| code-review | 60-90s | codereview, depmap, validator | Yes |

## Troubleshooting

**Skill not recognized:**
- Check `.claude/skills/` directory exists
- Verify markdown file has correct format
- Restart Claude Code

**Skill fails midway:**
- Check tool availability (zen MCP server running)
- Verify model names are valid
- Review logs for specific error

**Skill too slow:**
- Use faster models (gemini-2.5-flash instead of pro)
- Reduce thinking_mode from max to medium
- Skip optional validation steps

## Advanced: Conditional Skills

Skills can have conditional logic:

```markdown
# Smart Test Skill

When running tests:

1. Check file type:
   - If Python: use mcp__zen__autotest with pytest
   - If JavaScript: use npm test
   - If Go: use go test

2. If tests fail:
   - Use mcp__zen__debug to investigate
   - Fix issues
   - Re-run tests

3. If tests pass:
   - Use mcp__zen__validator for final check
   - Ready to commit
```

## Integration with Hooks

Skills work great with hooks:

**Hook triggers skill:**
```json
{
  "beforeCommit": {
    "command": "echo 'Triggering pre-commit skill'",
    "triggerSkill": "pre-commit"
  }
}
```

**Skill uses hook results:**
```markdown
# My Skill

1. Check if pre-commit hook passed
2. If failed, use mcp__zen__validator to diagnose
3. Fix and retry
```

## Next Steps

1. **Install these skills** in `.claude/skills/`
2. **Try them out** with simple tasks
3. **Customize** to match your workflow
4. **Create new skills** for your specific needs

Skills make me more efficient and consistent!
