# PRD Generator Skill for Claude Code

Use this skill when the user wants to create a new Product Requirements Document.

## Trigger Phrases
- "Create a PRD for..."
- "I need a PRD for..."
- "/prd [feature name]"

## Process

### Step 1: Clarifying Questions

Ask 3-5 clarifying questions with multiple-choice answers. Cover:

1. **Problem/Goal**: What problem are we solving? What's the desired outcome?
2. **Core Functionality**: What are the must-have features?
3. **Scope Boundaries**: What's explicitly NOT included?
4. **Target Users**: Who will use this?
5. **Success Criteria**: How do we know it's done correctly?

Format questions like:
```
**Q1: What's the primary goal?**
a) [Option 1]
b) [Option 2]
c) [Option 3]
d) Other (please specify)
```

### Step 2: Generate PRD

After receiving answers, create a PRD document at `tasks/prd-[feature-name].md` with:

```markdown
# PRD: [Feature Name]

## Overview
[2-3 sentences describing the feature]

## Goals
- [Goal 1]
- [Goal 2]

## User Stories
[List of user stories - see format below]

## Functional Requirements
[Numbered list of specific requirements]

## Non-Goals (Out of Scope)
- [What this feature will NOT do]

## Technical Considerations
- [Architecture notes]
- [Dependencies]
- [Potential risks]

## Design Considerations
- [UI/UX notes if applicable]

## Success Metrics
- [How to measure success]

## Open Questions
- [Unresolved questions for stakeholder review]
```

### Step 3: User Story Format

Each user story should be:
- Completable in ONE focused session
- Have VERIFIABLE acceptance criteria

Good:
```markdown
### US-001: Add priority column to database
**As a** developer
**I want** a priority column on the tasks table
**So that** tasks can be ordered by importance

**Acceptance Criteria:**
- [ ] Add `priority` column (enum: 'high', 'medium', 'low')
- [ ] Default value is 'medium'
- [ ] Migration file created
- [ ] Typecheck passes
```

Bad (too vague):
```markdown
### US-001: Implement priority system
- Works correctly
- Good user experience
```

## Writing Guidelines

1. **Be explicit** - A junior developer or AI agent should understand without guessing
2. **Use concrete examples** - "Shows red badge for high priority" not "Shows appropriate indicator"
3. **Number requirements** - Makes them easy to reference and verify
4. **Explain jargon** - Don't assume domain knowledge
5. **Include verification steps** - For UI: "Verify in browser"

## Critical Rules

1. **Do NOT start implementing** - This skill only creates the PRD
2. **Keep stories small** - Each story = one context window of work
3. **Include "Typecheck passes"** as acceptance criteria for all stories
4. **Include "Verify in browser"** for any UI stories
5. **Order stories by dependency** - Schema before API before UI

## After PRD Creation

Tell the user:
1. Review the PRD at `tasks/prd-[feature-name].md`
2. Use `/ralph-convert` to convert it to `prd.json` format
3. Then run `./ralph/ralph.sh` to start autonomous implementation
