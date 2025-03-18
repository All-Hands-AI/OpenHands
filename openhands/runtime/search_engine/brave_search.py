import re

import requests
import tenacity

from openhands.events.action import SearchAction
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.search_engine import SearchEngineObservation
from openhands.utils.tenacity_stop import stop_if_should_exit


def get_title(result):
    return f"### Title: {result['title']}\n" if 'title' in result else ''


def get_url(result):
    return f"### URL: {result['url']}\n" if 'url' in result else ''


def get_description(result):
    return (
        f"### Description: {result['description']}\n" if 'description' in result else ''
    )


def get_question(result):
    return f"### Question: {result['question']}\n" if 'question' in result else ''


def get_answer(result):
    return f"### Answer: {result['answer']}\n" if 'answer' in result else ''


def get_cluster(result):
    if 'cluster' in result:
        output = ''
        for i, result_obj in enumerate(result['cluster']):
            title = get_title(result_obj)
            url = get_url(result_obj)
            description = get_description(result_obj)
            discussion_output = (
                f'### Related webpage\n#{title}#{url}#{description}\n'
                if url != ''
                else ''
            )
            output += discussion_output
        return output
    else:
        return ''


def response_to_markdown(results, query):
    all_results = {}

    # discussions
    discussion_results = []
    if 'discussions' in results and 'results' in results['discussions']['results']:
        for result in results['discussions']['results']:
            title = get_title(result)
            url = get_url(result)
            description = get_description(result)
            cluster = get_cluster(result)
            discussion_output = f'## Discussion\n{title}{url}{description}{cluster}\n'
            discussion_results.append(discussion_output)
    all_results['discussions'] = discussion_results

    # FAQs
    faq_results = []
    if 'faq' in results and 'results' in results['faq']:
        for result in results['faq']['results']:
            title = get_title(result)
            url = get_url(result)
            question = get_question(result)
            answer = get_answer(result)
            faq_output = f'## FAQ\n{title}{url}{question}{answer}\n'
            faq_results.append(faq_output)
    all_results['faq'] = faq_results

    # News
    news_results = []
    if 'news' in results and 'results' in results['news']:
        for result in results['news']['results']:
            title = get_title(result)
            url = get_url(result)
            description = get_description(result)
            news_output = f'## News\n{title}{url}{description}\n'
            news_results.append(news_output)
    all_results['news'] = news_results

    # Videos
    video_results = []
    if 'videos' in results and 'results' in results['videos']:
        for result in results['videos']['results']:
            title = get_title(result)
            url = get_url(result)
            description = get_description(result)
            video_output = f'## Video\n{title}{url}{description}\n'
            video_results.append(video_output)
    all_results['videos'] = video_results

    # Web Search Results
    websearch_results = []
    if 'web' in results and 'results' in results['web']:
        for result in results['web']['results']:
            title = get_title(result)
            url = get_url(result)
            description = get_description(result)
            cluster = get_cluster(result)
            if cluster:
                websearch_output = f'## Webpage\n{title}{url}{description}\n{cluster}\n'
            else:
                websearch_output = f'## Webpage\n{title}{url}{description}\n'
            websearch_results.append(websearch_output)
    all_results['web'] = websearch_results

    # infobox
    infobox_results = []
    if 'infobox' in results and 'results' in results['infobox']:
        for result in results['infobox']['results']:
            title = get_title(result)
            url = get_url(result)
            description = get_description(result)
            infobox_output = f'## Infobox\n{title}{url}{description}\n'
            infobox_results.append(infobox_output)
    all_results['infobox'] = infobox_results

    # locations
    location_results = []
    if 'locations' in results and 'results' in results['location']:
        for result in results['locations']['results']:
            title = get_title(result)
            url = get_url(result)
            description = get_description(result)
            location_output = f'## Location\n{title}{url}{description}\n'
            location_results.append(location_output)
    all_results['locations'] = location_results

    markdown = '# Search Results\n\n'
    markdown += f'**Searched query**: {query}\n\n'

    # ranked results if available
    if 'mixed' in results:
        for rank_type in ['main', 'top', 'side']:
            if rank_type not in results['mixed']:
                continue
            for ranked_result in results['mixed'][rank_type]:
                result_type = ranked_result['type']
                if result_type in all_results:
                    include_all = ranked_result['all']
                    idx = ranked_result.get('index', None)
                    if include_all:
                        markdown += ''.join(all_results[result_type])
                    elif idx is not None and idx < len(all_results[result_type]):
                        markdown += all_results[result_type][idx]
        for result_list in all_results.values():
            for result in result_list:
                if result in markdown:
                    continue
                else:
                    markdown += result
    else:
        markdown += ''.join(
            websearch_results
            + video_results
            + news_results
            + infobox_results
            + faq_results
            + discussion_results
            + location_results
        )
    return markdown


def return_error(retry_state: tenacity.RetryCallState):
    return ErrorObservation('Failed to query Brave Search API.')


@tenacity.retry(
    wait=tenacity.wait_exponential(min=2, max=10),
    stop=tenacity.stop_after_attempt(5) | stop_if_should_exit(),
    retry_error_callback=return_error,
)
def query_api(query: str, API_KEY, BRAVE_SEARCH_URL):
    headers = {'Accept': 'application/json', 'X-Subscription-Token': API_KEY}

    params: list[tuple[str, str | int | bool]] = [
        ('q', query),
        ('count', 20),  # Number of results to return, max allowed = 20
        ('extra_snippets', False),  # TODO: Should we keep it as true?
    ]

    response = requests.get(
        BRAVE_SEARCH_URL,
        headers=headers,
        params=params,  # type: ignore
        timeout=10,
    )
    response.raise_for_status()  # Raise exception for 4XX/5XX responses
    results = response.json()
    markdown_content = response_to_markdown(results, query)
    # TODO: Handle other types of HTML tags? I couldn't find any other tags in brave search responses for the queries I tried.
    markdown_content = re.sub(r'</?strong>', '', markdown_content)
    return SearchEngineObservation(query=query, content=markdown_content)


def search(action: SearchAction):
    from openhands.core.config.app_config import AppConfig

    query = action.query
    if query is None or len(query.strip()) == 0:
        return ErrorObservation(
            content='The query string for search_engine tool must be a non-empty string.'
        )

    search_config = AppConfig().search
    if search_config.brave_api_key is None:
        raise ValueError(
            'Brave Search API key not set in configuration. Please set it in the search configuration.'
        )
    return query_api(query, search_config.brave_api_key, search_config.brave_api_url)
