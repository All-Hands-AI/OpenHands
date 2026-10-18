I am an AI agent helping Engel Nyst (@enyst) with project work.

Browser consumer proof for the normal bare package import. The host's error element observes native window error events; it supplies no require shim or mocked module response. Arrange the supplied host fixture against the selected package and write its loopback URL to the owned run workspace/library-host-url file. The same recipe is used on base and fix.

```sh known-bug F26.lib-host-app bare-package-mount
control-openhands browser viewport desktop
QA_LIBRARY_HOST_URL=$(cat "$OH_VERIFY_RUN/workspace/library-host-url")
control-openhands browser goto "$QA_LIBRARY_HOST_URL" --allow-external
control-openhands browser wait '#outside'
control-openhands browser wait '#inside, #module-error:not(:empty)' --timeout 30000
control-openhands browser screenshot --feature F26.lib-host-app --name bare-package-host
control-openhands assert --field value.mounted --equals true --bug 'value.mounted eq false && value.reactRequireError eq true' -- browser eval '(()=>({mounted:!!document.querySelector("#inside"),reactRequireError:document.querySelector("#module-error").textContent.includes("Calling `require` for \"react\"")}))()' # bug
control-openhands browser click '#inside'
control-openhands assert --field text --equals 'Inside Canvas 1' -- browser text '#inside'
```
