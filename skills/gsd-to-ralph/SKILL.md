# GSD-to-Ralph Converter

Convert GSD (Get Shit Done) phase plans to Ralph's prd.json format for autonomous execution.

## When to Use

After running GSD planning commands:
1. `/gsd:new-project` - Created PROJECT.md, REQUIREMENTS.md
2. `/gsd:create-roadmap` - Created ROADMAP.md with phases
3. `/gsd:plan-phase N` - Created PLAN.md files for phase N

Run this skill to convert the plans into Ralph's execution format.

## Usage

```
/gsd-to-ralph [phase-number]
```

Examples:
- `/gsd-to-ralph 1` - Convert Phase 1 plans to prd.json
- `/gsd-to-ralph 2` - Convert Phase 2 plans to prd.json
- `/gsd-to-ralph` - Convert all planned (uncompleted) phases

## What This Skill Does

1. **Reads GSD artifacts:**
   - `.planning/PROJECT.md` - Project name and description
   - `.planning/ROADMAP.md` - Phase goals and success criteria
   - `.planning/phases/{phase}/` - PLAN.md files with tasks

2. **Converts to Ralph format:**
   - GSD Phase → Ralph project context
   - GSD Plan → Group of related stories
   - GSD Task → Ralph user story
   - GSD `<done>` criteria → Ralph acceptance criteria
   - GSD `<verify>` commands → Ralph tests array
   - GSD `must_haves.truths` → Additional acceptance criteria

3. **Generates:**
   - `ralph/prd.json` - Task list for Ralph execution
   - `ralph/progress.txt` - Initialized with GSD context

## Mapping Reference

| GSD Field | Ralph Field |
|-----------|-------------|
| `phase` | Project context in description |
| `plan` | Story grouping (US-{phase}{plan}-{task}) |
| `task.name` | `story.title` |
| `task.action` | `story.description` |
| `task.done` | `story.acceptanceCriteria[]` |
| `task.verify` | `story.tests[]` |
| `task.files` | Mentioned in description |
| `must_haves.truths` | Additional acceptance criteria |
| `must_haves.artifacts` | File existence criteria |
| `wave` | `story.priority` (wave 1 = highest) |

## Process

### Step 1: Read GSD Artifacts

```bash
# Check for required GSD files
ls .planning/PROJECT.md .planning/ROADMAP.md .planning/phases/
```

### Step 2: Parse Phase Plans

For each PLAN.md in the target phase:
1. Extract frontmatter (phase, plan, wave, must_haves)
2. Parse XML tasks (name, files, action, verify, done)
3. Convert to user stories

### Step 3: Generate prd.json

Create Ralph's prd.json with:
- Project name from PROJECT.md
- Branch name from phase (e.g., `ralph/phase-01-foundation`)
- User stories from tasks
- Priority based on wave number
- Tests from verify commands
- Acceptance criteria from done + must_haves.truths

### Step 4: Initialize progress.txt

Create progress.txt with:
- GSD project context
- Phase description
- Codebase patterns from existing code (if any)

## Example Conversion

**GSD PLAN.md:**
```yaml
---
phase: 01-foundation
plan: 01
wave: 1
must_haves:
  truths:
    - "User model exists with required fields"
    - "Database migrations run successfully"
---

<task type="auto">
  <name>Task 1: Create User Model</name>
  <files>src/models/user.ts, prisma/schema.prisma</files>
  <action>Create User model with id, email, name, createdAt fields. Add to Prisma schema.</action>
  <verify>npx prisma validate && npx prisma generate</verify>
  <done>User model exists with all required fields, Prisma client generated</done>
</task>
```

**Ralph prd.json:**
```json
{
  "project": "Project Name (Phase 1: Foundation)",
  "branchName": "ralph/phase-01-foundation",
  "userStories": [
    {
      "id": "US-0101-01",
      "title": "Create User Model",
      "priority": 1,
      "description": "Create User model with id, email, name, createdAt fields. Add to Prisma schema.\n\nFiles: src/models/user.ts, prisma/schema.prisma",
      "acceptanceCriteria": [
        "User model exists with all required fields, Prisma client generated",
        "User model exists with required fields",
        "Database migrations run successfully"
      ],
      "tests": [
        "npx prisma validate",
        "npx prisma generate"
      ],
      "passes": false,
      "blocked": false
    }
  ]
}
```

## Integration with Ralph Workflow

After conversion:
1. Review generated `ralph/prd.json`
2. Adjust acceptance criteria if needed
3. Run `./ralph/ralph.sh --auto` to execute

Ralph's Skip & Document pattern handles any tasks that get stuck, creating documentation for human review.

## Notes

- GSD checkpoints (`checkpoint:human-verify`) map to stories that Ralph may mark as blocked for verification
- GSD's wave-based parallelism is converted to priority ordering (Ralph executes sequentially by priority)
- GSD's file ownership tracking helps identify potential conflicts in acceptance criteria
