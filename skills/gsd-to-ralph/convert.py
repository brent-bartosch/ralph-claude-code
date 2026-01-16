#!/usr/bin/env python3
"""
GSD-to-Ralph Converter

Converts GSD (Get Shit Done) phase plans to Ralph's prd.json format.
"""

import json
import re
import sys
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict


@dataclass
class UserStory:
    id: str
    title: str
    priority: int
    description: str
    acceptanceCriteria: list[str]
    tests: list[str] = field(default_factory=list)
    passes: bool = False
    blocked: bool = False
    blockedReason: str = ""
    notes: str = ""


@dataclass
class PRD:
    project: str
    branchName: str
    description: str
    userStories: list[UserStory]


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
        return frontmatter or {}, body
    except yaml.YAMLError:
        return {}, content


def parse_xml_tasks(content: str) -> list[dict]:
    """Extract tasks from XML-style task blocks."""
    tasks = []

    # Find all task blocks
    task_pattern = r'<task[^>]*type="([^"]*)"[^>]*>(.*?)</task>'
    matches = re.findall(task_pattern, content, re.DOTALL)

    for task_type, task_content in matches:
        task = {'type': task_type}

        # Extract task fields
        for field in ['name', 'files', 'action', 'verify', 'done']:
            pattern = rf'<{field}>(.*?)</{field}>'
            match = re.search(pattern, task_content, re.DOTALL)
            if match:
                task[field] = match.group(1).strip()

        tasks.append(task)

    return tasks


def extract_project_info(planning_dir: Path) -> tuple[str, str]:
    """Extract project name and description from PROJECT.md."""
    project_file = planning_dir / 'PROJECT.md'

    if not project_file.exists():
        return "Unnamed Project", "No description available"

    content = project_file.read_text()

    # Try to extract project name from heading
    name_match = re.search(r'^#\s+(?:Project:\s*)?(.+)$', content, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else "Unnamed Project"

    # Try to extract description from first paragraph after heading
    desc_match = re.search(r'^#.*?\n\n(.+?)(?:\n\n|$)', content, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else "No description"

    return name, description


def extract_phase_info(planning_dir: Path, phase_num: int) -> tuple[str, list[str]]:
    """Extract phase name and success criteria from ROADMAP.md."""
    roadmap_file = planning_dir / 'ROADMAP.md'

    if not roadmap_file.exists():
        return f"Phase {phase_num}", []

    content = roadmap_file.read_text()

    # Try to find phase name
    phase_pattern = rf'###?\s+Phase\s+{phase_num}[:\s]+([^\n]+)'
    name_match = re.search(phase_pattern, content)
    phase_name = name_match.group(1).strip() if name_match else f"Phase {phase_num}"

    # Try to find success criteria
    criteria = []
    criteria_pattern = rf'Phase\s+{phase_num}.*?Success Criteria.*?:\s*(.*?)(?=###|\*\*Phase|$)'
    criteria_match = re.search(criteria_pattern, content, re.DOTALL | re.IGNORECASE)
    if criteria_match:
        criteria_text = criteria_match.group(1)
        # Extract numbered or bulleted items
        items = re.findall(r'^\s*[\d\-\*\.]+\s*(.+)$', criteria_text, re.MULTILINE)
        criteria = [item.strip() for item in items if item.strip()]

    return phase_name, criteria


def find_plan_files(planning_dir: Path, phase_num: Optional[int] = None) -> list[Path]:
    """Find all PLAN.md files for a given phase or all phases."""
    phases_dir = planning_dir / 'phases'

    if not phases_dir.exists():
        return []

    plan_files = []

    for phase_dir in sorted(phases_dir.iterdir()):
        if not phase_dir.is_dir():
            continue

        # Check if this matches the requested phase
        if phase_num is not None:
            phase_match = re.match(r'^(\d+)', phase_dir.name)
            if not phase_match or int(phase_match.group(1)) != phase_num:
                continue

        # Find all PLAN.md files in this phase
        for plan_file in sorted(phase_dir.glob('*PLAN.md')):
            plan_files.append(plan_file)

    return plan_files


def convert_task_to_story(
    task: dict,
    phase_num: int,
    plan_num: int,
    task_num: int,
    wave: int,
    must_haves: dict
) -> UserStory:
    """Convert a GSD task to a Ralph user story."""

    # Generate story ID
    story_id = f"US-{phase_num:02d}{plan_num:02d}-{task_num:02d}"

    # Extract title from task name (remove "Task N:" prefix if present)
    title = task.get('name', 'Unnamed Task')
    title = re.sub(r'^Task\s+\d+:\s*', '', title)

    # Build description
    description_parts = [task.get('action', '')]
    if task.get('files'):
        description_parts.append(f"\nFiles: {task['files']}")
    description = '\n'.join(description_parts).strip()

    # Build acceptance criteria
    criteria = []
    if task.get('done'):
        criteria.append(task['done'])

    # Add must_haves.truths as additional criteria
    truths = must_haves.get('truths', [])
    if isinstance(truths, list):
        criteria.extend(truths)

    # Add artifact existence checks
    artifacts = must_haves.get('artifacts', [])
    if isinstance(artifacts, list):
        for artifact in artifacts:
            criteria.append(f"File exists: {artifact}")

    # Build tests from verify
    tests = []
    if task.get('verify'):
        # Split multiple commands
        verify_cmds = re.split(r'\s*&&\s*|\s*;\s*', task['verify'])
        tests.extend([cmd.strip() for cmd in verify_cmds if cmd.strip()])

    # Priority based on wave (wave 1 = priority 1, etc.)
    priority = wave

    return UserStory(
        id=story_id,
        title=title,
        priority=priority,
        description=description,
        acceptanceCriteria=criteria,
        tests=tests
    )


def convert_plan_file(plan_file: Path) -> list[UserStory]:
    """Convert a single PLAN.md file to user stories."""
    content = plan_file.read_text()
    frontmatter, body = parse_frontmatter(content)

    # Extract metadata
    phase_str = frontmatter.get('phase', '01-unknown')
    phase_match = re.match(r'^(\d+)', phase_str)
    phase_num = int(phase_match.group(1)) if phase_match else 1

    plan_num = int(frontmatter.get('plan', 1))
    wave = int(frontmatter.get('wave', 1))
    must_haves = frontmatter.get('must_haves', {})

    # Parse tasks
    tasks = parse_xml_tasks(body)

    # Convert each task to a story
    stories = []
    for i, task in enumerate(tasks, 1):
        story = convert_task_to_story(
            task=task,
            phase_num=phase_num,
            plan_num=plan_num,
            task_num=i,
            wave=wave,
            must_haves=must_haves
        )
        stories.append(story)

    return stories


def generate_prd(
    planning_dir: Path,
    phase_num: Optional[int] = None
) -> PRD:
    """Generate a Ralph PRD from GSD plans."""

    # Get project info
    project_name, project_desc = extract_project_info(planning_dir)

    # Find plan files
    plan_files = find_plan_files(planning_dir, phase_num)

    if not plan_files:
        raise ValueError(f"No PLAN.md files found for phase {phase_num}")

    # Convert all plans to stories
    all_stories = []
    for plan_file in plan_files:
        stories = convert_plan_file(plan_file)
        all_stories.extend(stories)

    # Sort by priority (wave)
    all_stories.sort(key=lambda s: (s.priority, s.id))

    # Renumber priorities sequentially
    for i, story in enumerate(all_stories, 1):
        story.priority = i

    # Build branch name
    if phase_num:
        phase_name, _ = extract_phase_info(planning_dir, phase_num)
        phase_slug = re.sub(r'[^a-z0-9]+', '-', phase_name.lower()).strip('-')
        branch_name = f"ralph/phase-{phase_num:02d}-{phase_slug}"
        project_title = f"{project_name} (Phase {phase_num}: {phase_name})"
    else:
        branch_name = f"ralph/{re.sub(r'[^a-z0-9]+', '-', project_name.lower()).strip('-')}"
        project_title = project_name

    return PRD(
        project=project_title,
        branchName=branch_name,
        description=project_desc,
        userStories=all_stories
    )


def generate_progress_txt(prd: PRD, planning_dir: Path, phase_num: Optional[int]) -> str:
    """Generate initial progress.txt content."""
    lines = [
        "# Ralph Progress Log",
        f"# Branch: {prd.branchName}",
        f"# Started: (pending)",
        "",
        "## Codebase Patterns",
        "",
        "(Patterns discovered during implementation will be added here)",
        "",
    ]

    # Add GSD context if available
    project_file = planning_dir / 'PROJECT.md'
    if project_file.exists():
        lines.extend([
            "## GSD Project Context",
            "",
            f"Project: {prd.project}",
            f"Description: {prd.description}",
            "",
        ])

    if phase_num:
        phase_name, criteria = extract_phase_info(planning_dir, phase_num)
        lines.extend([
            f"## Phase {phase_num}: {phase_name}",
            "",
            "Success Criteria:",
        ])
        for criterion in criteria:
            lines.append(f"- {criterion}")
        lines.append("")

    lines.extend([
        "---",
        "",
    ])

    return '\n'.join(lines)


def main():
    """Main entry point."""
    # Parse arguments
    phase_num = None
    if len(sys.argv) > 1:
        try:
            phase_num = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [phase-number]")
            sys.exit(1)

    # Find planning directory
    planning_dir = Path('.planning')
    if not planning_dir.exists():
        print("Error: .planning directory not found")
        print("Run GSD planning commands first:")
        print("  /gsd:new-project")
        print("  /gsd:create-roadmap")
        print("  /gsd:plan-phase N")
        sys.exit(1)

    # Generate PRD
    try:
        prd = generate_prd(planning_dir, phase_num)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Create ralph directory
    ralph_dir = Path('ralph')
    ralph_dir.mkdir(exist_ok=True)

    # Write prd.json
    prd_file = ralph_dir / 'prd.json'
    prd_dict = {
        'project': prd.project,
        'branchName': prd.branchName,
        'description': prd.description,
        'userStories': [asdict(s) for s in prd.userStories]
    }
    prd_file.write_text(json.dumps(prd_dict, indent=2))
    print(f"Created: {prd_file}")

    # Write progress.txt if it doesn't exist
    progress_file = ralph_dir / 'progress.txt'
    if not progress_file.exists():
        progress_content = generate_progress_txt(prd, planning_dir, phase_num)
        progress_file.write_text(progress_content)
        print(f"Created: {progress_file}")
    else:
        print(f"Skipped: {progress_file} (already exists)")

    # Summary
    print()
    print(f"Converted {len(prd.userStories)} tasks to user stories")
    print(f"Project: {prd.project}")
    print(f"Branch: {prd.branchName}")
    print()
    print("Next steps:")
    print("  1. Review ralph/prd.json")
    print("  2. Run: ./ralph/ralph.sh --auto")


if __name__ == '__main__':
    main()
