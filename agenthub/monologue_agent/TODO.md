# TODO
There's a lot of low-hanging fruit for this agent:

* Strip `<script>`, `<style>`, and other non-text tags from the HTML before sending it to the LLM
* Keep track of the working directory when the agent uses `cd`
* Improve memory condensing--condense earlier memories more aggressively
* Limit the time that `run` can wait (in case agent runs an interactive command and it's hanging)
* Figure out how to run background processes, e.g. `node server.js` to start a server
