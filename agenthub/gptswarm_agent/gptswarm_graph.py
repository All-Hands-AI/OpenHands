#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import asyncio
import dataclasses
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, List, Literal, Optional

import requests
from pytube import YouTube
from swarm.graph import Graph, Node

from agenthub.gptswarm_agent.prompt import GPTSwarmPromptSet
from opendevin.core.logger import opendevin_logger as logger
from opendevin.llm.llm import LLM
from opendevin.runtime.plugins.agent_skills.agentskills import (
    parse_audio,
    parse_docx,
    parse_image,
    parse_latex,
    parse_pdf,
    parse_pptx,
    parse_txt,
    parse_video,
)

OPENAI_API_KEY = 'sk-proj-****'  # TODO: get from environment or config
SEARCHAPI_API_KEY = '****'  # TODO: get from environment or config

MessageRole = Literal['system', 'user', 'assistant']


@dataclasses.dataclass()
class Message:
    role: MessageRole
    content: str


READER_MAP = {
    '.png': parse_image,
    '.jpg': parse_image,
    '.jpeg': parse_image,
    '.gif': parse_image,
    '.bmp': parse_image,
    '.tiff': parse_image,
    '.tif': parse_image,
    '.webp': parse_image,
    '.mp3': parse_audio,
    '.m4a': parse_audio,
    '.wav': parse_audio,
    '.MOV': parse_video,
    '.mp4': parse_video,
    '.mov': parse_video,
    '.avi': parse_video,
    '.mpg': parse_video,
    '.mpeg': parse_video,
    '.wmv': parse_video,
    '.flv': parse_video,
    '.webm': parse_video,
    '.pptx': parse_pptx,
    '.pdf': parse_pdf,
    '.docx': parse_docx,
    '.tex': parse_latex,
    '.txt': parse_txt,
}


class FileReader:
    def __init__(self):
        self.reader = None  # Initial type is None

    def set_reader(self, suffix: str):
        reader = READER_MAP.get(suffix)
        if reader is not None:
            self.reader = reader
            logger.info(f'Setting Reader to {self.reader.__name__}')
        else:
            logger.error(f'No reader found for suffix {suffix}')
            self.reader = None

    def read_file(self, file_path: Path, task: str = 'describe the file') -> str:
        suffix = file_path.suffix
        self.set_reader(suffix)
        if not self.reader:
            raise ValueError(f'No reader set for suffix {suffix}')
        if self.reader in [parse_image, parse_video]:
            file_content = self.reader(file_path, task)
        else:
            file_content = self.reader(file_path)
        logger.info(f'Reading file {file_path} using {self.reader.__name__}')
        return file_content


class GenerateQuery(Node):
    def __init__(
        self,
        domain: str = 'gaia',
        model_name: Optional[str] = 'gpt-4o-2024-05-13',
        operation_description: str = 'Given a question, return what information is needed to answer the question.',
        id=None,
    ):
        super().__init__(operation_description, id, True)
        self.domain = domain
        self.api_key = OPENAI_API_KEY
        self.llm = LLM(model=model_name, api_key=self.api_key)
        self.prompt_set = GPTSwarmPromptSet()

    @property
    def node_name(self) -> str:
        return self.__class__.__name__

    def extract_urls(self, text: str) -> List[str]:
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        return urls

    def is_youtube_url(self, url: str) -> bool:
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return bool(re.match(youtube_regex, url))

    def _youtube_download(self, url: str) -> str:
        try:
            video_id = url.split('v=')[-1].split('&')[0]
            video_id = video_id.strip()
            youtube = YouTube(url)
            video_stream = (
                youtube.streams.filter(progressive=True, file_extension='mp4')
                .order_by('resolution')
                .desc()
                .first()
            )
            if not video_stream:
                raise ValueError('No suitable video stream found.')

            output_dir = 'workspace/tmp'
            os.makedirs(output_dir, exist_ok=True)
            output_path = f'{output_dir}/{video_id}.mp4'
            video_stream.download(output_path=output_dir, filename=f'{video_id}.mp4')
            return output_path

        except Exception as e:
            logger.error(
                f'Error downloading video from {url}: {e}'
            )  # Use logger for error messages
            return ''

    async def _execute(
        self, inputs: Optional[List[dict]] = None, **kwargs
    ) -> List[dict]:
        if inputs is None:
            inputs = []
        node_inputs = inputs
        outputs = []

        for input in node_inputs:
            urls = self.extract_urls(input['task'])

            download_paths = []

            for url in urls:
                if self.is_youtube_url(url):
                    download_path = self._youtube_download(url)
                    if download_path:
                        download_paths.append(download_path)

            if urls:
                logger.info(urls)
            if download_paths:
                logger.info(download_paths)

            files = input.get('files', [])
            if not isinstance(files, list):
                files = []
            files.extend(download_paths)

            role = self.prompt_set.get_role()
            # constraint = self.prompt_set.get_constraint()
            prompt = self.prompt_set.get_query_prompt(question=input['task'])

            messages = [
                Message(role='system', content=f'You are a {role}.'),
                Message(role='user', content=prompt),
            ]

            response = self.llm.do_completion(
                messages=[
                    {'role': msg.role, 'content': msg.content} for msg in messages
                ]
            )
            response = response.choices[0].message.content

            executions = {
                'operation': self.node_name,
                'task': input['task'],
                'files': files,
                'input': input.get('task', None),
                'subtask': prompt,
                'output': response,
                'format': 'natural language',
            }
            outputs.append(executions)

        return outputs


class FileAnalyse(Node):
    def __init__(
        self,
        domain: str = 'gaia',
        model_name: Optional[str] = 'gpt-4o-2024-05-13',
        operation_description: str = 'Given a question, extract information from a file.',
        id=None,
    ):
        super().__init__(operation_description, id, True)
        self.domain = domain
        self.api_key = OPENAI_API_KEY
        self.llm = LLM(model=model_name, api_key=self.api_key)
        self.prompt_set = GPTSwarmPromptSet()
        self.reader = FileReader()

    @property
    def node_name(self) -> str:
        return self.__class__.__name__

    async def _execute(
        self, inputs: Optional[List[dict]] = None, **kwargs
    ) -> List[dict]:
        if inputs is None:
            inputs = []
        node_inputs = inputs
        outputs = []
        for input in node_inputs:
            query = input.get('output', 'Please organize the information of this file.')
            files = input.get('files', [])
            response = await self.file_analyse(query, files, self.llm)

            executions = {
                'operation': self.node_name,
                'task': input['task'],
                'files': files,
                'input': query,
                'subtask': f'Read the content of ###{files}, use query ###{query}',
                'output': response,
                'format': 'natural language',
            }

            outputs.append(executions)

        return outputs

    async def file_analyse(self, query: str, files: List[str], llm: LLM) -> str:
        answer = ''
        for file in files:
            file_path = Path(file)
            if self.reader not in [parse_image, parse_video]:
                file_content = self.reader.read_file(file_path)
                prompt = self.prompt_set.get_file_analysis_prompt(
                    query=query, file=file_content
                )
                messages = [
                    Message(
                        role='system',
                        content=f'You are a {self.prompt_set.get_role()}.',
                    ),
                    Message(role='user', content=prompt),
                ]
                response = llm.do_completion(
                    messages=[
                        {'role': msg.role, 'content': msg.content} for msg in messages
                    ]
                )
                answer += response.choices[0].message.content + '\n'
        return answer


class WebSearch(Node):
    def __init__(
        self,
        domain: str = 'gaia',
        model_name: Optional[str] = 'gpt-4o-2024-05-13',
        operation_description: str = 'Given a question, search the web for infomation.',
        id=None,
    ):
        super().__init__(operation_description, id, True)
        self.domain = domain
        self.api_key = OPENAI_API_KEY
        self.llm = LLM(model=model_name, api_key=self.api_key)
        self.prompt_set = GPTSwarmPromptSet()

    @property
    def node_name(self) -> str:
        return self.__class__.__name__

    async def _execute(
        self, inputs: Optional[List[dict]] = None, max_keywords: int = 4, **kwargs
    ) -> List[dict]:
        if inputs is None:
            inputs = []
        node_inputs = inputs
        outputs = []
        for input in node_inputs:
            task = input['task']
            query = input['output']
            prompt = self.prompt_set.get_websearch_prompt(question=task, query=query)
            messages = [
                Message(
                    role='system', content=f'You are a {self.prompt_set.get_role()}.'
                ),
                Message(role='user', content=prompt),
            ]
            generated_quires = self.llm.do_completion(
                messages=[
                    {'role': msg.role, 'content': msg.content} for msg in messages
                ]
            )

            generated_quires = generated_quires.choices[0].message.content
            generated_quires = generated_quires.split(',')[:max_keywords]
            logger.info(f'The search keywords include: {generated_quires}')
            search_results = [self.web_search(query) for query in generated_quires]
            logger.info(f'The search results: {str(search_results)[:100]}...')

            distill_prompt = self.prompt_set.get_distill_websearch_prompt(
                question=input['task'], query=query, results='.\n'.join(search_results)
            )

            messages = [
                Message(
                    role='system', content=f'You are a {self.prompt_set.get_role()}.'
                ),
                Message(role='user', content=distill_prompt),
            ]
            response = self.llm.do_completion(
                messages=[
                    {'role': msg.role, 'content': msg.content} for msg in messages
                ]
            )
            response = response.choices[0].message.content

            executions = {
                'operation': self.node_name,
                'task': task,
                'files': input.get('files', []),
                'input': query,
                'subtask': distill_prompt,
                'output': response,
                'format': 'natural language',
            }
            outputs.append(executions)

        return outputs

    def web_search(self, query: str, item_num: int = 3) -> str:
        url = 'https://www.searchapi.io/api/v1/search'
        params = {
            'engine': 'google',
            'q': query,
            'api_key': SEARCHAPI_API_KEY,  # os.getenv("SEARCHAPI_API_KEY")
        }

        response = ast.literal_eval(requests.get(url, params=params).text)

        if (
            'knowledge_graph' in response.keys()
            and 'description' in response['knowledge_graph'].keys()
        ):
            return response['knowledge_graph']['description']

        if (
            'organic_results' in response.keys()
            and len(response['organic_results']) > 0
        ):
            snippets = []
            for res in response['organic_results'][:item_num]:
                if 'snippet' in res:
                    snippets.append(res['snippet'])
            return '\n'.join(snippets)

        return ' '


class CombineAnswer(Node):
    def __init__(
        self,
        domain: str = 'gaia',
        model_name: Optional[str] = 'gpt-4o-2024-05-13',
        operation_description: str = 'Combine multiple inputs into one.',
        max_token: int = 500,
        id=None,
    ):
        super().__init__(operation_description, id, True)
        self.domain = domain
        self.max_token = max_token
        self.api_key = OPENAI_API_KEY
        self.llm = LLM(model=model_name, api_key=self.api_key)
        self.prompt_set = GPTSwarmPromptSet()
        self.materials: defaultdict[str, str] = defaultdict(str)

    @property
    def node_name(self) -> str:
        return self.__class__.__name__

    async def _execute(
        self, inputs: Optional[List[Any]] = None, **kwargs
    ) -> List[dict]:
        if inputs is None:
            inputs = []
        node_inputs = inputs

        role = self.prompt_set.get_role()
        constraint = self.prompt_set.get_constraint()

        self.materials = defaultdict(str)
        for input in node_inputs:
            operation = input.get('operation')
            if operation:
                self.materials[operation] += f'{input.get("output", "")}\n'
            self.materials['task'] = input.get('task')

        question = self.prompt_set.get_combine_materials(self.materials)
        prompt = self.prompt_set.get_answer_prompt(question=question)

        messages = [
            Message(role='system', content=f'You are a {role}. {constraint}'),
            Message(role='user', content=prompt),
        ]

        response = self.llm.do_completion(
            messages=[{'role': msg.role, 'content': msg.content} for msg in messages]
        )

        response = response.choices[0].message.content

        executions = {
            'operation': self.node_name,
            'task': self.materials['task'],
            'files': self.materials['files']
            if isinstance(self.materials['files'], str)
            else ', '.join(self.materials['files']),
            'input': node_inputs,
            'subtask': prompt,
            'output': response,
            'format': 'natural language',
        }

        return [executions]


class AssistantGraph(Graph):
    def build_graph(self):
        query = GenerateQuery(self.domain, self.model_name)

        file_analysis = FileAnalyse(self.domain, self.model_name)
        web_search = WebSearch(self.domain, self.model_name)

        query.add_successor(file_analysis)
        query.add_successor(web_search)

        combine = CombineAnswer(self.domain, self.model_name)
        file_analysis.add_successor(combine)
        web_search.add_successor(combine)

        self.input_nodes = [query]
        self.output_nodes = [combine]

        self.add_node(query)
        self.add_node(file_analysis)
        self.add_node(web_search)
        self.add_node(combine)


if __name__ == '__main__':
    # # test node
    # task = 'What is the text representation of the last digit of twelve squared?'
    # inputs = [{'task': task}]
    # query_instance = GenerateQuery()
    # query = asyncio.run(query_instance._execute(inputs))
    # print(query)

    # task = 'What is the text representation of the last digit of twelve squared?'
    # inputs = [
    #     {
    #         'task': 'How can researchers ensure AGI development is both safe and ethical while avoiding societal biases and inequalities?',
    #         'files': ['agi.txt'],
    #     }
    # ]
    # file_instance = FileAnalyse()
    # file_info = asyncio.run(file_instance._execute(inputs))
    # print(file_info)

    # task = 'What is the text representation of the last digit of twelve squared?'
    # inputs = [
    #     {
    #         'task': 'How can researchers ensure AGI development is both safe and ethical while avoiding societal biases and inequalities?'
    #     }
    # ]
    # search_instance = WebSearch()
    # search_info = asyncio.run(search_instance._execute(inputs))
    # print(search_info)

    assistant_graph = AssistantGraph(domain='gaia', model_name='gpt-4o-2024-05-13')

    # test graph
    assistant_graph.build_graph()
    inputs = [
        {
            'task': 'How can researchers ensure AGI development is both safe and ethical while avoiding societal biases and inequalities?',
            'files': ['agi.txt'],
        }
    ]
    outputs = asyncio.run(assistant_graph.run(inputs))
    print(outputs)
