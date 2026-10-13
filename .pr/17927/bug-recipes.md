# Frozen baseline/fix recipes

I am an AI agent helping Engel Nyst (@enyst) with project maintenance.

These scripts preserve the exact recipe used for comparison. Run them only against an isolated control-openhands run with the appropriate backend pins and test credential environment. The maintained feature map converts the accepted behavior to a normal recipe after verification.

  ```sh known-bug F16.save-states desktop
  control-openhands restart
  control-openhands doctor
  control-openhands browser viewport desktop
  control-openhands browser goto /settings/app
  control-openhands browser wait 'testid=submit-button'
  control-openhands assert --field value --equals false -- browser eval "document.querySelector('[data-testid=enable-sound-notifications-switch]').checked"
  control-openhands service stop agent-server
  control-openhands browser record start --feature F16.save-states --name failed-save-desktop
  control-openhands browser click 'testid=app-settings-screen >> text=Sound Notifications'
  control-openhands browser click 'testid=submit-button'
  control-openhands browser wait-text 'An error occurred'
  control-openhands browser screenshot --feature F16.save-states --name failed-save-desktop
  control-openhands browser record stop --gif
  control-openhands restart
  control-openhands assert --field value --equals true --bug-shows false -- browser eval "document.querySelector('[data-testid=enable-sound-notifications-switch]').checked" # bug
  ```

  ```sh known-bug F16.save-states phone
  control-openhands restart
  control-openhands doctor
  control-openhands browser viewport phone
  control-openhands browser goto /settings/app
  control-openhands browser wait 'testid=submit-button'
  control-openhands assert --field value --equals false -- browser eval "document.querySelector('[data-testid=enable-sound-notifications-switch]').checked"
  control-openhands service stop agent-server
  control-openhands browser record start --feature F16.save-states --name failed-save-phone
  control-openhands browser click 'testid=app-settings-screen >> text=Sound Notifications'
  control-openhands browser click 'testid=submit-button'
  control-openhands browser wait-text 'An error occurred'
  control-openhands browser screenshot --feature F16.save-states --name failed-save-phone
  control-openhands browser record stop --gif
  control-openhands restart
  control-openhands assert --field value --equals true --bug-shows false -- browser eval "document.querySelector('[data-testid=enable-sound-notifications-switch]').checked" # bug
  ```
