import os
from datetime import datetime

import tenacity
from exa_py import Exa

from openhands.events.action import SearchAction
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.search_engine import SearchEngineObservation
from openhands.utils.tenacity_stop import stop_if_should_exit


def get_title(result):
    if result.title:
        return f'### Title: {result.title}\n'
    else:
        return ''


def get_url(result):
    if result.url:
        return f'### URL: {result.url}\n'
    else:
        return ''


def get_highlights(result):
    content = ''
    if result.highlights:
        highlights = []
        for highlight in result.highlights:
            if len(highlight.strip()) > 0:
                highlights.append(highlight.strip())
        highlights_str = ' '.join(highlights)
        content = f'### Highlights: {highlights_str}'
    return content


def get_summary(result):
    content = ''
    if result.summary:
        content = f'### Summary: {result.summary.strip()}'
    return content


def response_to_markdown(search_results, query):
    markdown = '# Search Results\n\n'
    markdown += f'**Searched query**: {query}\n\n'
    for result in search_results.results:
        title = get_title(result)
        url = get_url(result)
        highlights = get_highlights(result)
        summary = get_summary(result)
        markdown += f'{title}{url}{highlights}{summary}\n\n'
    return markdown


def get_date(dt_str):
    try:
        datetime.fromisoformat(dt_str)
        return dt_str
    except Exception as _:
        return None


def return_error(retry_state: tenacity.RetryCallState):
    return ErrorObservation('Failed to query Exa Search API.')


@tenacity.retry(
    wait=tenacity.wait_exponential(min=2, max=10),
    stop=tenacity.stop_after_attempt(5) | stop_if_should_exit(),
    retry_error_callback=return_error,
)
def query_api(
    query: str, API_KEY: str, start_date: str | None = None, end_date: str | None = None
):
    exa = Exa(api_key=API_KEY)
    search_results = exa.search_and_contents(
        query=query,
        type='auto',
        num_results=10,
        text=False,
        summary={'query': query},
        highlights=False,
        start_published_date=get_date(start_date),
        end_published_date=get_date(end_date),
    )
    markdown_content = response_to_markdown(search_results, query)
    return SearchEngineObservation(query=query, content=markdown_content)


def search(action: SearchAction):
    query = action.query
    start_date = action.start_date
    end_date = action.end_date

    if query is None or len(query.strip()) == 0:
        return ErrorObservation(
            content='The query string for search_engine tool must be a non-empty string.'
        )
    if start_date and not get_date(start_date):
        return ErrorObservation(
            content='The start_date for search_engine tool must be a string in ISO 8601 format. Examples: 2023-01-01 OR 2023-01-01T00:00:00.000Z'
        )
    if end_date and not get_date(end_date):
        return ErrorObservation(
            content='The end_date for search_engine tool must be a string in ISO 8601 format. Examples: 2023-12-31 OR 2023-12-31T00:00:00.000Z'
        )

    API_KEY = os.environ.get('SEARCH_API_KEY', None)
    if API_KEY is None:
        raise ValueError(
            'Environment variable SEARCH_API_KEY not set. It must be set to Exa Search API Key.'
        )
    return query_api(query, API_KEY, start_date, end_date)
