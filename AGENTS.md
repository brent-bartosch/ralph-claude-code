# Ralph for Claude Code - Agent Instructions

## What is Ralph?

Ralph is an autonomous AI agent loop that implements Geoffrey Huntley's "Ralph pattern" - spawning fresh AI instances to work through a PRD until all requirements are complete.

## Directory Structure

```
ralph/
├── ralph.sh           # Main loop script
├── prompt.md          # Instructions for each iteration
├── prd.json           # Current PRD being worked on
├── prd.json.example   # Template for new PRDs
├── progress.txt       # Learnings and progress log
├── archive/           # Previous PRD runs
└── skills/
    ├── prd/           # PRD generator skill
    └── ralph/         # PRD converter skill
```

## How It Works

1. **ralph.sh** spawns a Claude Code instance with `prompt.md`
2. Claude reads `prd.json` and `progress.txt`
3. Claude implements ONE user story
4. Claude updates `prd.json` (marks story complete) and `progress.txt`
5. Claude commits the work
6. Loop repeats until all stories pass

## Key Files

### prd.json
The source of truth for what needs to be done. Contains:
- `userStories[]` - Each story has `passes: true/false`
- Stories are worked in priority order
- Only modify to mark stories complete or add notes

### progress.txt
Persistent memory across iterations. Contains:
- **Codebase Patterns** section at top - critical learnings
- Chronological log of completed work
- Must be updated EVERY iteration

### prompt.md
Instructions given to each fresh Claude instance. Don't modify unless changing the overall workflow.

## Critical Patterns

### One Story Per Iteration
Never attempt multiple stories. Context windows are limited. One focused story = higher success rate.

### Never Commit Broken Code
All quality checks (typecheck, lint, test) must pass before committing. Broken commits compound across iterations.

### Update Progress First
Before ending an iteration, always update `progress.txt`. Future iterations depend on this knowledge.

### Check AGENTS.md Files
Before modifying files in a directory, check for AGENTS.md with patterns and gotchas specific to that code.

## Running Ralph

```bash
# Default (10 iterations)
./ralph/ralph.sh

# More iterations
./ralph/ralph.sh 25

# Check progress
cat ralph/progress.txt

# Check remaining stories
jq '[.userStories[] | select(.passes == false)]' ralph/prd.json
```

## Creating a New PRD

1. Use the PRD skill: "Create a PRD for [feature]"
2. Review `tasks/prd-[feature].md`
3. Convert with ralph skill: "/ralph-convert"
4. Run `./ralph/ralph.sh`

## Troubleshooting

### "Max iterations reached"
- Check `progress.txt` for what's blocking
- Stories may be too large - split them
- Quality checks may be failing - fix manually

### "Story too complex"
- Edit `prd.json` to split the story
- Reset `passes: false` on the split stories
- Continue with `./ralph/ralph.sh`

### "Stuck in loop"
- Check git status for uncommitted changes
- Check if quality checks are failing
- Add learnings to progress.txt manually
