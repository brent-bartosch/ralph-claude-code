# Ralph for Claude Code

Autonomous AI agent loop adapted from [snarktank/ralph](https://github.com/snarktank/ralph) for Claude Code CLI.

## Quick Start

```bash
# 1. Create a PRD (in Claude Code conversation)
"Create a PRD for adding user authentication"

# 2. Convert PRD to ralph format
"/ralph-convert"

# 3. Run autonomous implementation
./ralph/ralph.sh

# 4. Monitor progress
tail -f ralph/progress.txt
```

## How It Works

Ralph spawns fresh Claude Code instances in a loop, each working on ONE user story until all requirements are complete. Memory persists through:

- **Git** - Completed work
- **progress.txt** - Learnings and patterns
- **prd.json** - Task completion status

## Files

| File | Purpose |
|------|---------|
| `ralph.sh` | Main loop script |
| `prompt.md` | Instructions for each iteration |
| `prd.json` | Current task list |
| `progress.txt` | Memory across iterations |
| `skills/prd/` | PRD generator skill |
| `skills/ralph/` | PRD converter skill |

## Usage

```bash
# Interactive mode (will prompt for permissions)
./ralph/ralph.sh

# More iterations
./ralph/ralph.sh 25

# FULLY AUTONOMOUS (skips all permission prompts)
./ralph/ralph.sh --auto

# Autonomous with more iterations
./ralph/ralph.sh --auto 25

# Check which stories remain
jq '.userStories[] | select(.passes == false) | .title' ralph/prd.json
```

**Warning**: `--auto` mode uses `--dangerously-skip-permissions`. Use with caution.

## Creating Good PRDs

Stories must be **small enough to complete in one iteration**:

**Good:**
- Add database column
- Create API endpoint
- Build single component

**Bad (split these):**
- Build entire dashboard
- Implement authentication
- Create data pipeline

## Differences from Original Ralph

| Feature | Original (Amp) | This Version (Claude Code) |
|---------|---------------|---------------------------|
| CLI | `amp` | `claude` |
| Auto mode | `--dangerously-allow-all` | `--auto` flag (uses `--dangerously-skip-permissions`) |
| Skills | `skills/*/SKILL.md` | Same format, works with Claude Code |

## Testing and Quality Framework

Ralph includes a comprehensive testing and validation framework to prevent AI failure modes. Key features:

- **Story-level tests**: Add `tests` array to stories for executable validation
- **Skip & Document pattern**: After 2-3 failures, Ralph blocks the story with documentation instead of degrading the solution
- **Blocked story tracking**: Stories can be marked `blocked: true` for human review

See **[Testing and Limitations Documentation](docs/TESTING_AND_LIMITATIONS.md)** for the complete framework.

### Handling Blocked Stories

```bash
# Check for blocked stories
jq '[.userStories[] | select(.blocked == true)] | .[] | {id, title, blockedReason}' ralph/prd.json

# Unblock after resolving the issue
jq '(.userStories[] | select(.id == "US-XXX") | .blocked) = false' ralph/prd.json > tmp.json && mv tmp.json ralph/prd.json
```

## Tips

1. **Start small** - Begin with a 3-5 story PRD to test the workflow
2. **Check progress.txt** - This is Ralph's memory
3. **Keep stories atomic** - One focused change per story
4. **Don't skip quality checks** - Broken code compounds
5. **Review blocked stories promptly** - Don't let them accumulate
6. **Add executable tests** - Use the `tests` array in prd.json
