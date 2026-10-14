# Frozen baseline/fix recipes

I am an AI agent helping Engel Nyst (@enyst) with project maintenance.

These scripts preserve the exact recipe used for comparison. Run them only against an isolated control-openhands run with the appropriate backend pins and test credential environment. The maintained feature map converts the accepted behavior to a normal recipe after verification.

  ```sh known-bug F10.create-prefill desktop-inherited
  control-openhands llm set --profile QA_Inherit --model deepseek/deepseek-flash --api-key-env DEEPSEEK_API_KEY --no-activate --no-validate
  control-openhands api DELETE /api/profiles/QA_Inherit --write
  control-openhands api PATCH /api/settings --write --data '{"agent_settings_diff":{"llm":{"temperature":0.4}}}'
  control-openhands browser viewport desktop
  control-openhands browser goto /settings/llm
  control-openhands browser click 'testid=add-llm-profile'
  control-openhands browser click 'testid=sdk-section-all-toggle'
  control-openhands assert --field value --equals 0.4 -- browser value 'testid=sdk-settings-llm.temperature'
  control-openhands browser fill 'testid=llm-custom-model-input' deepseek/deepseek-flash
  control-openhands browser fill 'testid=profile-name-input' QA_Inherit
  control-openhands browser fill 'testid=llm-api-key-input' --value-env DEEPSEEK_API_KEY
  control-openhands browser record start --feature F10.create-prefill --name inherited-save
  control-openhands browser scroll 'testid=sdk-settings-llm.temperature'
  control-openhands browser screenshot --feature F10.create-prefill --name inherited-before-save
  control-openhands browser click 'testid=save-profile-btn'
  control-openhands browser wait-text 'created'
  control-openhands browser click '[data-testid=profile-row]:has([title="QA_Inherit"]) >> testid=profile-menu-trigger'
  control-openhands browser click 'testid=profile-actions-menu >> testid=profile-edit'
  control-openhands browser click 'testid=sdk-section-all-toggle'
  control-openhands browser scroll 'testid=sdk-settings-llm.temperature'
  control-openhands browser screenshot --feature F10.create-prefill --name inherited-after-save
  control-openhands browser record stop --gif
  control-openhands api GET /api/profiles/QA_Inherit --pick config.temperature
  control-openhands assert --field value --equals 0.4 --bug-shows '' -- browser value 'testid=sdk-settings-llm.temperature' # bug
  ```

  ```sh known-bug F10.create-prefill phone-inherited
  control-openhands llm set --profile QA_Inherit --model deepseek/deepseek-flash --api-key-env DEEPSEEK_API_KEY --no-activate --no-validate
  control-openhands api DELETE /api/profiles/QA_Inherit --write
  control-openhands api PATCH /api/settings --write --data '{"agent_settings_diff":{"llm":{"temperature":0.4}}}'
  control-openhands browser viewport phone
  control-openhands browser goto /settings/llm
  control-openhands browser click 'testid=add-llm-profile'
  control-openhands browser click 'testid=sdk-section-all-toggle'
  control-openhands assert --field value --equals 0.4 -- browser value 'testid=sdk-settings-llm.temperature'
  control-openhands browser fill 'testid=llm-custom-model-input' deepseek/deepseek-flash
  control-openhands browser fill 'testid=profile-name-input' QA_Inherit
  control-openhands browser fill 'testid=llm-api-key-input' --value-env DEEPSEEK_API_KEY
  control-openhands browser record start --feature F10.create-prefill --name phone-inherited-save
  control-openhands browser scroll 'testid=sdk-settings-llm.temperature'
  control-openhands browser screenshot --feature F10.create-prefill --name phone-inherited-before-save
  control-openhands browser click 'testid=save-profile-btn'
  control-openhands browser wait-text 'created'
  control-openhands browser click '[data-testid=profile-row]:has([title="QA_Inherit"]) >> testid=profile-menu-trigger'
  control-openhands browser click 'testid=profile-actions-menu >> testid=profile-edit'
  control-openhands browser click 'testid=sdk-section-all-toggle'
  control-openhands browser scroll 'testid=sdk-settings-llm.temperature'
  control-openhands browser screenshot --feature F10.create-prefill --name phone-inherited-after-save
  control-openhands browser record stop --gif
  control-openhands api GET /api/profiles/QA_Inherit --pick config.temperature
  control-openhands assert --field value --equals 0.4 --bug-shows '' -- browser value 'testid=sdk-settings-llm.temperature' # bug
  ```
