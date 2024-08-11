#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Any, Dict


class GPTSwarmPromptSet:
    """
    GPTSwarmPromptSet provides a collection of static methods to generate prompts
    for a general AI assistant. These prompts cover various tasks like answering questions,
    performing web searches, analyzing files, and reflecting on tasks.
    """

    @staticmethod
    def get_role():
        return 'a general AI assistant'

    @staticmethod
    def get_constraint():
        return (
            'I will ask you a question. Report your thoughts, and finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER]. '
            'YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings. '
            "If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise. "
            "If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise. "
            'If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string. '
        )

    @staticmethod
    def get_format():
        return 'natural language'

    @staticmethod
    def get_answer_prompt(question):
        return f'{question}'

    @staticmethod
    def get_query_prompt(question):
        return (
            '# Information Gathering for Question Resolution\n\n'
            'Evaluate if additional information is needed to answer the question. '
            'If a web search or file analysis is necessary, outline specific clues or details to be searched for.\n\n'
            f'## ❓ Target Question:\n{question}\n\n'
            '## 🔍 Clues for Investigation:\n'
            'Identify critical clues and concepts within the question that are essential for finding the answer.\n'
        )

    @staticmethod
    def get_file_analysis_prompt(query, file):
        return (
            '# File Analysis Task\n\n'
            f'## 🔍 Information Extraction Objective:\n---\n{query}\n---\n\n'
            f'## 📄 File Under Analysis:\n---\n{file}\n---\n\n'
            '## 📝 Instructions:\n'
            '1. Identify the key sections in the file relevant to the query.\n'
            '2. Extract and summarize the necessary information from these sections.\n'
            '3. Ensure the response is focused and directly addresses the query.\n'
            "Example: 'Identify the main theme in the text.'"
        )

    @staticmethod
    def get_websearch_prompt(question, query):
        return (
            '# Web Search Task\n\n'
            f'## Original Question: \n---\n{question}\n---\n\n'
            f'## 🔍 Targeted Search Objective:\n---\n{query}\n---\n\n'
            '## 🌐 Simplified Search Instructions:\n'
            'Generate three specific search queries directly related to the original question. Each query should focus on key terms from the question. Format the output as a comma-separated list.\n'
            "For example, if the question is 'Who will be the next US president?', your queries could be: 'US presidential candidates, current US president, next US president'.\n"
            "Remember to format the queries as 'query1, query2, query3'."
        )

    @staticmethod
    def get_distill_websearch_prompt(question, query, results):
        return (
            '# Summarization of Search Results\n\n'
            f'## Original question: \n---\n{question}\n---\n\n'
            f'## 🔍 Required Information for Summary:\n---\n{query}\n---\n\n'
            f'## 🌐 Analyzed Search Results:\n---\n{results}\n---\n\n'
            '## 📝 Instructions for Summarization:\n'
            '1. Review the provided search results and identify the most relevant information related to the question and query.\n'
            '2. Extract and highlight the key findings, facts, or data points from these results.\n'
            '3. Organize the summarized information in a coherent and logical manner.\n'
            '4. Ensure the summary is concise and directly addresses the query, avoiding extraneous details.\n'
            '5. If the information from web search is useless, directly answer: "No useful information from WebSearch".\n'
        )

    @staticmethod
    def get_combine_materials(materials: Dict[str, Any], avoid_vague=True) -> str:
        question = materials.get('task', 'No problem provided')

        for key, value in materials.items():
            if 'No useful information from WebSearch' in value:
                continue
            value = value.strip('\n').strip()
            if key != 'task' and value:
                question += (
                    f'\n\nReference information for {key}:'
                    + '\n----------------------------------------------\n'
                    + f'{value}'
                    + '\n----------------------------------------------\n\n'
                )

        if avoid_vague:
            question += (
                '\nProvide a specific answer. For questions with known answers, ensure to provide accurate and factual responses. '
                + "Avoid vague responses or statements like 'unable to...' that don't contribute to a definitive answer. "
                + "For example: if a question asks 'who will be the president of America', and the answer is currently unknown, you could suggest possibilities like 'Donald Trump', or 'Biden'. However, if the answer is known, provide the correct information."
            )

        return question

    @staticmethod
    def get_self_consistency(question: str, answers: list, constraint: str) -> str:
        formatted_answers = '\n'.join(
            [f'Answer {index + 1}: {answer}' for index, answer in enumerate(answers)]
        )
        return (
            '# Self-Consistency Evaluation Task\n\n'
            f'## 🤔 Question for Review:\n---\n{question}\n---\n\n'
            f'## 💡 Reviewable Answers:\n---\n{formatted_answers}\n---\n\n'
            '## 📋 Instructions for Selection:\n'
            '1. Read each answer and assess how it addresses the question.\n'
            "2. Compare the answers for their adherence to the given question's criteria and logical coherence.\n"
            "3. Identify the answer that best aligns with the question's requirements and is the most logically consistent.\n"
            "4. Ignore the candidate answers if they do not give a direct answer, for example, using 'unable to ...', 'as an AI ...'.\n"
            '5. Copy the most suitable answer as it is, without modification, to maintain its original form.\n'
            f'6. Adhere to the constraints: {constraint}.\n'
            'Note: If no answer fully meets the criteria, choose and copy the one that is closest to the requirements.'
        )
