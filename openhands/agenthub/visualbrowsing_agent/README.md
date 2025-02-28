# Browsing Agent Framework

This folder implements the AgentLab [generic agent](https://github.com/ServiceNow/AgentLab/tree/main/src/agentlab/agents/generic_agent) that enables full-featured web browsing. The observations given to the agent include set-of-marks annotated web-page screenshot, accessibility tree of the web-page and all the thoughts and actions from previous steps.

## Test run

Note that for browsing tasks, GPT-4/Claude is usually a requirement to get reasonable results, due to the complexity of the web page structures. This agent has been evaluated on the VisualWebArena benchmark and the CodeAct agent does not call this VisualBrowsingAgent. CodeAct agent uses has in-built support for browsing (e.g., via browse_url and browser tool).
