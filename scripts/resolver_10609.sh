set -e

OH_DIR="$(dirname "$0")/.."
if [[ -z "$TMP_DIR" ]]; then
    TMP_DIR="/tmp"
fi

export DEBUG=1
export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"

OUTPUT_DIR="$TMP_DIR/resolver-output"
OUTPUT_FILE="$OUTPUT_DIR/output.jsonl"

ISSUE_NUMBER=15
ISSUE_TYPE=issue

LOG_FILE="$TMP_DIR/tmp.log"

if [[ -z "$LLM_API_KEY" ]]; then
    if [[ -z "$ANTHROPIC_API_KEY" ]]; then
        echo "LLM_API_KEY or ANTHROPIC_API_KEY environment variable must be set."
        exit 1
    fi
    export LLM_API_KEY=$ANTHROPIC_API_KEY
fi

TARGET_REPO="$OUTPUT_DIR/workspace/${ISSUE_TYPE}_${ISSUE_NUMBER}"

rm -f $OUTPUT_FILE

echo "Target repo at: $TARGET_REPO"

# only cd if the directory exists
if [ -d "$TARGET_REPO" ]; then
    cd "$TARGET_REPO"
    diff=$(git diff)
    if [ -n "$diff" ]; then
        echo "Make sure that the repo is clean. Current diff:"
        echo "$diff"
    fi
fi
echo "Logging to \"$LOG_FILE\"..."

cd "$OH_DIR"

python -m openhands.resolver.resolve_issue \
    --repo replayio-public/bench-devtools-10609 \
    --issue-number $ISSUE_NUMBER \
    --issue-type $ISSUE_TYPE \
    --max-iterations 50 \
    --comment-id 2526444494 \
    --output-dir "$OUTPUT_DIR" \
    > "$LOG_FILE" 2>&1
