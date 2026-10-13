# Delete all pagination proof

Run-owned backend only. Arrange one non-validating QA LLM profile for blank
conversations before this recipe; no messages are sent and no model is invoked.
Select desktop or phone before running. The same recipe runs twice per viewport
on bdb69754a1 and the fix branch.

```sh known-bug F04.delete-all pagination
control-openhands browser goto /
phone=$(control-openhands browser eval 'window.innerWidth < 768' | node -pe 'JSON.parse(require("fs").readFileSync(0,"utf8")).value')
panel=''
if [ "$phone" = true ]; then panel='testid=sidebar-mobile-drawer >> '; fi
ids=$(control-openhands api GET '/api/conversations/search?limit=100' --pick items | node -pe 'JSON.parse(require("fs").readFileSync(0,"utf8")).value.map(x=>x.id).join("\n")')
for id in $ids; do control-openhands api DELETE "/api/conversations/$id" --write; done
for index in $(seq 1 23); do
  control-openhands browser goto /
  if [ "$phone" = true ]; then control-openhands browser click 'testid=sidebar-mobile-menu-toggle'; fi
  control-openhands browser click "${panel}testid=conversation-panel-new-thread-picker"
  control-openhands browser click "${panel}testid=launch-no-workspace" --expect-url '/conversations/'
done
control-openhands assert --field value --equals 23 -- api GET '/api/conversations/search?limit=100' --pick items.length
control-openhands browser goto /
control-openhands browser reload
if [ "$phone" = true ]; then control-openhands browser click 'testid=sidebar-mobile-menu-toggle'; fi
control-openhands browser record start --feature F04.delete-all --name pagination-delete
trap 'control-openhands browser record stop --gif || true' EXIT
control-openhands browser click "${panel}testid=conversation-layouts-toggle"
control-openhands browser click 'testid=delete-all-conversations'
control-openhands browser wait 'role=dialog >> button[data-testid="confirm-button"]:not(:disabled)' --timeout 30000
control-openhands browser snapshot 'role=dialog' --feature F04.delete-all --name full-count
control-openhands browser screenshot --feature F04.delete-all --name confirmation
control-openhands browser click 'role=dialog >> testid=confirm-button'
control-openhands browser wait 'role=dialog' --state detached --timeout 30000
control-openhands browser screenshot --feature F04.delete-all --name after-delete
control-openhands assert --field value --equals 0 --bug-shows 3 -- api GET '/api/conversations/search?limit=100' --pick items.length # bug
```
