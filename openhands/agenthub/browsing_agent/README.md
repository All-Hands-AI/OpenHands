# Browsing Agent

This folder implements the basic browser agent that enables full-featured web browsing using Browser-Use.


## Test run

Note that for browsing tasks, GPT-4 is usually a requirement to get reasonable results, due to the complexity of the web page structures.

```
poetry run python ./openhands/core/main.py \
           -i 10 \
           -t "tell me the usa's president using google search" \
           -c BrowsingAgent \
           -m claude-3-5-sonnet-20241022
```
