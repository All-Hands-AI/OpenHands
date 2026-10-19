I am an AI agent helping Engel Nyst (@enyst) with project work.

Phone viewport variant of the unchanged validation assertion from the read-only maintenance map; only the viewport differs.

```sh known-bug F28.draft-validation stale-test-success
control-openhands browser viewport phone
control-openhands browser goto /automations/setup
control-openhands browser fill 'testid=automation-setup-name' QA_Stale_Test_Success
control-openhands browser click 'testid=automation-setup-kind-custom'
control-openhands browser click 'testid=automation-setup-frequency-custom'
control-openhands browser fill 'testid=automation-setup-custom-schedule' '0 0 1 1 *'
control-openhands browser click 'testid=automation-setup-save-draft'
control-openhands browser hover 'testid=automation-setup-name'
control-openhands browser wait-url 'draftId='
QA_DRAFT_ID=$(control-openhands browser url | jq -r '.url|capture("draftId=(?<id>[a-f0-9-]+)").id')
trap 'control-openhands api DELETE "/api/automation/v1/drafts/$QA_DRAFT_ID" --write >/dev/null; control-openhands browser goto /automations >/dev/null' EXIT
control-openhands browser click 'testid=automation-setup-test'
control-openhands browser wait 'testid=automation-setup-draft-run'
QA_MATERIALIZED_ID=$(control-openhands api GET "/api/automation/v1/drafts/$QA_DRAFT_ID" | jq -r .body.materialized_automation_id)
QA_RUN_STATE=''
for QA_ATTEMPT in $(seq 1 20); do
  QA_RUN_STATE=$(control-openhands api GET "/api/automation/v1/$QA_MATERIALIZED_ID/runs?limit=10" | jq -r '.body.runs[0].status // ""')
  [ "$QA_RUN_STATE" = COMPLETED ] && break
  sleep 3
done
[ "$QA_RUN_STATE" = COMPLETED ]
control-openhands browser reload
control-openhands browser text 'testid=automation-setup-draft-validity'
control-openhands browser fill 'testid=automation-setup-custom-schedule' 'every day'
control-openhands browser click 'testid=automation-setup-save-draft'
control-openhands browser hover 'testid=automation-setup-name'
control-openhands browser reload
control-openhands assert --field body.dispatchable --equals false -- api GET "/api/automation/v1/drafts/$QA_DRAFT_ID"
control-openhands browser screenshot --feature F28.draft-validation --name stale-test-success
control-openhands assert --field text --equals 'Value error, Invalid cron expression: every day' --bug-shows 'Latest test passed' -- browser text 'testid=automation-setup-draft-validity' # bug
```
