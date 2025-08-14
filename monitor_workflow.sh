#!/bin/bash

RUN_ID="16896094781"
JOB_ID="47866065370"
LOG_FILE="/tmp/e2e_workflow_logs.txt"

echo "Monitoring workflow run $RUN_ID (job $JOB_ID)"
echo "Logs will be saved to $LOG_FILE"

while true; do
    echo "$(date): Checking workflow status..."

    # Get current status
    STATUS=$(gh run view $RUN_ID --json status --jq '.status')
    echo "$(date): Status: $STATUS"

    if [ "$STATUS" = "completed" ]; then
        echo "$(date): Workflow completed! Fetching logs..."
        gh run view --log --job=$JOB_ID > "$LOG_FILE" 2>&1
        echo "$(date): Logs saved to $LOG_FILE"

        # Also get the conclusion
        CONCLUSION=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
        echo "$(date): Conclusion: $CONCLUSION"
        echo "Workflow finished with conclusion: $CONCLUSION" >> "$LOG_FILE"
        break
    elif [ "$STATUS" = "in_progress" ]; then
        echo "$(date): Still running, waiting 30 seconds..."
        sleep 30
    else
        echo "$(date): Unexpected status: $STATUS"
        break
    fi
done

echo "Monitoring complete. Check $LOG_FILE for full logs."
