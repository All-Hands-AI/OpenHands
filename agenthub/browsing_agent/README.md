# Browsing Agent Framework

This folder implements the basic BrowserGym [demo agent](https://github.com/ServiceNow/BrowserGym/tree/main/demo_agent) that enables full-featured web browsing.


## Test run

Note that for browsing tasks, GPT-4 is usually a requirement to get reasonable results, due to the complexity of the web page structures.

```
poetry run python ./opendevin/core/main.py \
           -i 5 \
           -t "tell me the usa's president using google search" \
           -c BrowsingAgent \
           -m gpt-4o-2024-05-13
```
