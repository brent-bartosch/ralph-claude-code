#!/bin/bash
# Ralph for Claude Code - Autonomous AI Agent Loop
# Adapted from https://github.com/snarktank/ralph for Claude Code CLI
#
# Usage: ./ralph.sh [options] [max_iterations]
#
# Options:
#   --auto          Skip permission prompts (uses --dangerously-skip-permissions)
#   --help          Show this help message
#
# Examples:
#   ./ralph.sh              # Run with prompts, 10 iterations
#   ./ralph.sh 20           # Run with prompts, 20 iterations
#   ./ralph.sh --auto       # Fully autonomous, 10 iterations
#   ./ralph.sh --auto 25    # Fully autonomous, 25 iterations

set -e

# Parse arguments
AUTO_MODE=false
MAX_ITERATIONS=10

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --help)
            head -17 "$0" | tail -14
            exit 0
            ;;
        *)
            if [[ "$1" =~ ^[0-9]+$ ]]; then
                MAX_ITERATIONS=$1
            fi
            shift
            ;;
    esac
done
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRD_FILE="$SCRIPT_DIR/prd.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}           ${GREEN}Ralph for Claude Code${NC} - Autonomous Loop         ${BLUE}║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check for required files
if [ ! -f "$PRD_FILE" ]; then
    echo -e "${RED}Error: prd.json not found at $PRD_FILE${NC}"
    echo "Create a prd.json file first. See prd.json.example for the format."
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/prompt.md" ]; then
    echo -e "${RED}Error: prompt.md not found at $SCRIPT_DIR/prompt.md${NC}"
    exit 1
fi

# Check if claude CLI is available
if ! command -v claude &> /dev/null; then
    echo -e "${RED}Error: 'claude' CLI not found. Install Claude Code first.${NC}"
    echo "See: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

# Get current branch from prd.json
CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null)
if [ -z "$CURRENT_BRANCH" ]; then
    echo -e "${YELLOW}Warning: No branchName in prd.json${NC}"
    CURRENT_BRANCH="ralph/unknown"
fi

# Archive previous run if branch changed
if [ -f "$LAST_BRANCH_FILE" ]; then
    LAST_BRANCH=$(cat "$LAST_BRANCH_FILE")
    if [ "$LAST_BRANCH" != "$CURRENT_BRANCH" ] && [ -f "$PROGRESS_FILE" ]; then
        echo -e "${YELLOW}Branch changed from $LAST_BRANCH to $CURRENT_BRANCH${NC}"
        echo "Archiving previous run..."

        ARCHIVE_NAME=$(date +%Y-%m-%d)-$(echo "$LAST_BRANCH" | sed 's/ralph\///' | tr '/' '-')
        mkdir -p "$ARCHIVE_DIR/$ARCHIVE_NAME"

        [ -f "$PRD_FILE.bak" ] && cp "$PRD_FILE.bak" "$ARCHIVE_DIR/$ARCHIVE_NAME/prd.json"
        [ -f "$PROGRESS_FILE" ] && mv "$PROGRESS_FILE" "$ARCHIVE_DIR/$ARCHIVE_NAME/progress.txt"

        echo -e "${GREEN}Archived to $ARCHIVE_DIR/$ARCHIVE_NAME${NC}"
    fi
fi

# Save current branch
echo "$CURRENT_BRANCH" > "$LAST_BRANCH_FILE"

# Initialize progress file if it doesn't exist
if [ ! -f "$PROGRESS_FILE" ]; then
    echo "# Ralph Progress Log" > "$PROGRESS_FILE"
    echo "# Branch: $CURRENT_BRANCH" >> "$PROGRESS_FILE"
    echo "# Started: $(date '+%Y-%m-%d %H:%M:%S')" >> "$PROGRESS_FILE"
    echo "" >> "$PROGRESS_FILE"
    echo "## Codebase Patterns" >> "$PROGRESS_FILE"
    echo "(Patterns discovered during implementation will be added here)" >> "$PROGRESS_FILE"
    echo "" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
    echo "" >> "$PROGRESS_FILE"
fi

# Count total and completed stories
count_stories() {
    local total=$(jq '.userStories | length' "$PRD_FILE")
    local completed=$(jq '[.userStories[] | select(.passes == true)] | length' "$PRD_FILE")
    echo "$completed/$total"
}

# Main loop
echo -e "${BLUE}Starting Ralph loop with max $MAX_ITERATIONS iterations${NC}"
if [ "$AUTO_MODE" = true ]; then
    echo -e "${YELLOW}Mode: AUTONOMOUS (--dangerously-skip-permissions)${NC}"
else
    echo -e "Mode: Interactive (will prompt for permissions)"
fi
echo -e "Progress: $(count_stories) stories complete"
echo ""

for ((i=1; i<=MAX_ITERATIONS; i++)); do
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Iteration $i of $MAX_ITERATIONS${NC} - $(date '+%H:%M:%S')"
    echo -e "Stories: $(count_stories)"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Create temporary files
    OUTPUT_FILE=$(mktemp)
    PROMPT_FILE=$(mktemp)

    # Run Claude Code with the prompt
    # Each iteration spawns a NEW conversation (fresh context window)
    # Memory persists through: git, progress.txt, prd.json
    #
    # Write prompt to temp file to avoid shell escaping issues
    cat "$SCRIPT_DIR/prompt.md" > "$PROMPT_FILE"

    # Build command based on mode
    # Use --print-only to get just the response, pipe prompt from file
    if [ "$AUTO_MODE" = true ]; then
        CLAUDE_ARGS="--dangerously-skip-permissions"
    else
        CLAUDE_ARGS=""
    fi

    if cat "$PROMPT_FILE" | claude -p - $CLAUDE_ARGS 2>&1 | tee "$OUTPUT_FILE"; then
        # Check for completion signal
        if grep -q "<promise>COMPLETE</promise>" "$OUTPUT_FILE"; then
            echo ""
            echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║${NC}                    ${GREEN}ALL STORIES COMPLETE!${NC}                  ${GREEN}║${NC}"
            echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
            rm -f "$OUTPUT_FILE" "$PROMPT_FILE"
            exit 0
        fi
    else
        echo -e "${YELLOW}Warning: Claude Code exited with non-zero status${NC}"
    fi

    rm -f "$OUTPUT_FILE" "$PROMPT_FILE"

    # Brief pause between iterations
    if [ $i -lt $MAX_ITERATIONS ]; then
        echo ""
        echo -e "${YELLOW}Pausing 2 seconds before next iteration...${NC}"
        sleep 2
    fi
done

echo ""
echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║${NC}         Max iterations reached without completion         ${YELLOW}║${NC}"
echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Final progress: $(count_stories)"
echo "Check $PROGRESS_FILE for details."
exit 1
