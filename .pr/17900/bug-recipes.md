# Frozen baseline/fix recipes

I am an AI agent helping Engel Nyst (@enyst) with project maintenance.

These scripts preserve the exact recipe used for comparison. Run them only against an isolated control-openhands run with the appropriate backend pins and test credential environment. The maintained feature map converts the accepted behavior to a normal recipe after verification.

  ```sh known-bug F16.keyboard desktop
  control-openhands browser viewport desktop
  control-openhands browser goto /settings/app
  control-openhands browser wait 'testid=submit-button'
  control-openhands browser record start --feature F16.keyboard --name keyboard-desktop
  control-openhands browser focus 'testid=color-theme-input'
  control-openhands browser press Tab
  control-openhands browser press Escape
  control-openhands browser screenshot --feature F16.keyboard --name keyboard-desktop
  control-openhands browser record stop --gif
  control-openhands assert --field value --equals enable-analytics-switch --bug-shows title-llm-profile-input -- browser eval "document.activeElement.getAttribute('data-testid')" # bug
  ```

  ```sh known-bug F16.keyboard phone
  control-openhands browser viewport phone
  control-openhands browser goto /settings/app
  control-openhands browser wait 'testid=submit-button'
  control-openhands browser record start --feature F16.keyboard --name keyboard-phone
  control-openhands browser focus 'testid=color-theme-input'
  control-openhands browser press Tab
  control-openhands browser press Escape
  control-openhands browser screenshot --feature F16.keyboard --name keyboard-phone
  control-openhands browser record stop --gif
  control-openhands assert --field value --equals enable-analytics-switch --bug-shows title-llm-profile-input -- browser eval "document.activeElement.getAttribute('data-testid')" # bug
  ```
