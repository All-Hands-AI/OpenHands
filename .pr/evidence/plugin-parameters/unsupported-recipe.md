I am an AI agent helping Engel Nyst (@enyst) with project work.

Paired proof for the documented acceptable alternative: unsupported Local parameters are identified before creation. The existing accepted-create delivery recipe is unchanged and was separately reproduced twice on base. This recipe does not claim runtime parameter support or an xpass of that accepted-create recipe.

```sh known-bug F19.launch-parameters unsupported-local
QA_PARAM_SOURCE="$OH_VERIFY_RUN/workspace/qa-unsupported-parameter-plugin"
[ ! -L "$QA_PARAM_SOURCE" ]
mkdir -p "$QA_PARAM_SOURCE/.plugin"
printf '%s\n' '{"name":"qa-unsupported-parameter-plugin","version":"0.1.0","description":"Inert parameter configuration check; no skills or tools."}' > "$QA_PARAM_SOURCE/.plugin/plugin.json"
trap 'rm -rf "$QA_PARAM_SOURCE"; control-openhands browser goto /conversations >/dev/null' EXIT
QA_PARAM_PAYLOAD=$(jq -nc --arg source "$QA_PARAM_SOURCE" '[{source:$source,parameters:{city:"Paris",days:3,metric:true}}]' | base64 | tr -d '\n')
QA_PARAM_QUERY=$(jq -rn --arg value "$QA_PARAM_PAYLOAD" '$value|@uri')
control-openhands browser viewport desktop
control-openhands browser goto "/launch?plugins=$QA_PARAM_QUERY"
control-openhands browser fill 'testid=plugin-0-param-city' Tokyo
control-openhands browser fill 'testid=plugin-0-param-days' 7
control-openhands browser check 'testid=plugin-0-param-metric'
control-openhands browser check 'testid=trust-checkbox'
control-openhands browser screenshot --feature F19.launch-parameters --name unsupported-local
control-openhands assert --field count --equals 1 --bug-shows 0 -- browser count 'testid=plugin-parameters-unsupported' # bug
control-openhands assert --field text --equals 'This local backend does not support plugin parameters. Remove the parameters from the launch link before starting a conversation.' -- browser text 'testid=plugin-parameters-unsupported'
control-openhands assert --field value --equals true -- browser eval 'document.querySelector("[data-testid=start-conversation-button]").disabled'
```
