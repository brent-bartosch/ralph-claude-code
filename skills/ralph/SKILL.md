# Ralph PRD Converter Skill

Use this skill to convert a markdown PRD into `prd.json` format for Ralph autonomous execution.

## Trigger Phrases
- "/ralph-convert"
- "Convert PRD to ralph format"
- "Prepare PRD for ralph"

## The Core Principle

**Each story must be completable in ONE Ralph iteration (one context window).**

Stories that are too large cause the AI to run out of context and produce broken code.

### Right-Sized Stories (GOOD)
- Add a database column with migration
- Create a single UI component
- Add one API endpoint
- Implement a utility function
- Update configuration for a specific behavior

### Oversized Stories (BAD - must be split)
- "Build the entire dashboard"
- "Implement user authentication"
- "Create the data pipeline"

Split large features into: schema → backend → UI components → integration

## Conversion Process

### Step 1: Find the PRD

```bash
ls tasks/prd-*.md
```

If multiple PRDs exist, ask which one to convert.

### Step 2: Analyze Stories

Read the PRD and identify all user stories. For each story, verify:
- [ ] Fits in one context window
- [ ] Has concrete acceptance criteria
- [ ] Criteria are verifiable (not vague)

### Step 3: Order by Dependency

Stories must be ordered so earlier stories don't depend on later ones:

1. **Schema/Database** - Tables, columns, migrations
2. **Backend Logic** - Server actions, API endpoints, services
3. **UI Components** - Components that use backend
4. **Integration** - Features combining multiple pieces
5. **Polish** - Final touches, edge cases

### Step 4: Validate Acceptance Criteria

Every story needs:
- At least one concrete, verifiable criterion
- "Typecheck passes" as a criterion
- "Tests pass" for logic-heavy stories
- "Verify in browser" for UI stories

Fix vague criteria:
- BAD: "Works correctly" → GOOD: "Returns 200 status with user object"
- BAD: "Good UX" → GOOD: "Loading spinner shows during fetch"
- BAD: "Handles errors" → GOOD: "Shows error toast when API returns 4xx/5xx"

### Step 5: Archive Existing PRD (if any)

Before creating new `prd.json`, archive any existing one:

```bash
# Check for existing prd.json
if [ -f ralph/prd.json ]; then
    EXISTING_BRANCH=$(jq -r '.branchName' ralph/prd.json)
    ARCHIVE_NAME=$(date +%Y-%m-%d)-${EXISTING_BRANCH#ralph/}
    mkdir -p ralph/archive/$ARCHIVE_NAME
    mv ralph/prd.json ralph/archive/$ARCHIVE_NAME/
    [ -f ralph/progress.txt ] && mv ralph/progress.txt ralph/archive/$ARCHIVE_NAME/
fi
```

### Step 6: Generate prd.json

Create `ralph/prd.json` with this structure:

```json
{
  "project": "[Project Name from PRD]",
  "branchName": "ralph/[kebab-case-feature-name]",
  "description": "[Overview from PRD]",
  "userStories": [
    {
      "id": "US-001",
      "title": "[Story Title]",
      "priority": 1,
      "description": "[User story in 'As a... I want... So that...' format]",
      "acceptanceCriteria": [
        "[Criterion 1]",
        "[Criterion 2]",
        "Typecheck passes"
      ],
      "passes": false,
      "notes": ""
    }
  ]
}
```

**Important:**
- IDs are sequential: US-001, US-002, US-003...
- Priority matches order (1 is highest priority)
- All stories start with `"passes": false`
- All stories start with empty `"notes": ""`

### Step 7: Create Feature Branch

```bash
git checkout -b ralph/[feature-name]
```

### Step 8: Initialize Progress File

Create fresh `ralph/progress.txt`:

```markdown
# Ralph Progress Log
# Branch: ralph/[feature-name]
# Started: [timestamp]

## Codebase Patterns
(Patterns discovered during implementation will be added here)

---

```

### Step 9: Provide Next Steps

Tell the user:
```
PRD converted to ralph/prd.json with [N] stories.
Branch: ralph/[feature-name]

To start autonomous implementation:
  ./ralph/ralph.sh

To run with more iterations:
  ./ralph/ralph.sh 20

Monitor progress in ralph/progress.txt
```

## Troubleshooting

### "Story too large"
Split it into smaller stories. Ask: "What's the first thing that needs to exist before the rest can work?"

### "Unclear acceptance criteria"
Ask the user: "How would you verify this is done? What would you check?"

### "Circular dependencies"
Re-order stories. Schema and data models always come first.
