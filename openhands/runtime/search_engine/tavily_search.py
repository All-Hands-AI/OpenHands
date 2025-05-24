import os

import tenacity
from tavily import TavilyClient

from openhands.events.action import SearchAction
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.search_engine import SearchEngineObservation
from openhands.utils.tenacity_stop import stop_if_should_exit


def get_title(result):
    return f"### Title: {result['title']}\n" if 'title' in result else ''


def get_url(result):
    return f"### URL: {result['url']}\n" if 'url' in result else ''


def get_description(result):
    return f"### Brief Summary: {result['content']}" if 'content' in result else ''


def get_answer(result):
    return (
        f"### LLM-Generated Answer: {result['answer']}\n\n"
        if 'answer' in result
        else ''
    )


def response_to_markdown(tavily_response):
    markdown = '# Search Results\n\n'
    markdown += f'**Searched query**: {tavily_response['query']}\n\n'
    markdown += get_answer(tavily_response)
    for result in tavily_response['results']:
        title = get_title(result)
        url = get_url(result)

        highlights = get_description(result)
        markdown += f'{title}{url}{highlights}\n\n'
    return markdown


def return_error(retry_state: tenacity.RetryCallState):
    return ErrorObservation('Failed to query Tavily Search API.')


@tenacity.retry(
    wait=tenacity.wait_exponential(min=2, max=10),
    stop=tenacity.stop_after_attempt(5) | stop_if_should_exit(),
    retry_error_callback=return_error,
)
def query_api(query: str, API_KEY: str):
    client = TavilyClient(API_KEY)

    search_results = client.search(
        query=query,
        search_depth='advanced',
        topic='general',
        max_results=5,
        chunks_per_source=3,
        include_answer='advanced',
    )
    markdown_content = response_to_markdown(search_results)
    return SearchEngineObservation(query=query, content=markdown_content)


def search(action: SearchAction):
    query = action.query

    if query is None or len(query.strip()) == 0:
        return ErrorObservation(
            content='The query string for search_engine tool must be a non-empty string.'
        )

    API_KEY = os.environ.get('SEARCH_API_KEY', None)
    if API_KEY is None:
        raise ValueError(
            'Environment variable SEARCH_API_KEY not set. It must be set to Tavily Search API Key.'
        )
    return query_api(query, API_KEY)
