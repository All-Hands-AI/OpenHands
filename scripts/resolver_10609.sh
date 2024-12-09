set -e

export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"

if [[ -z "$TMP_DIR" ]]; then
    TMP_DIR="/tmp"
fi
LOG_FILE="$TMP_DIR/tmp.log"

if [[ -z "$LLM_API_KEY" ]]; then
    if [[ -z "$ANTHROPIC_API_KEY" ]]; then
        echo "LLM_API_KEY or ANTHROPIC_API_KEY environment variable must be set."
        exit 1
    fi
    export LLM_API_KEY=$ANTHROPIC_API_KEY
fi

export DEBUG=1

echo -e "Logging to \"$LOG_FILE\"\n"

python -m openhands.resolver.resolve_issue \
    --repo replayio-public/bench-devtools-10609 \
    --issue-number 15 \
    --issue-type issue \
    --max-iterations 50 \
    --comment-id 2526444494 \
    --output-dir "$TMP_DIR/resolver-output" \
    > "$LOG_FILE" 2>&1
