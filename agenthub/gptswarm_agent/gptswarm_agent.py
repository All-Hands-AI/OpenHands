import asyncio
import dataclasses
from copy import deepcopy
from typing import Any, Dict, List, Literal

from agenthub.gptswarm_agent.gptswarm_graph import AssistantGraph
from agenthub.gptswarm_agent.prompt import GPTSwarmPromptSet
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import Action
from opendevin.llm.llm import LLM

ENABLE_GITHUB = True
OPENAI_API_KEY = 'sk-proj-****'  # TODO: get from environment or config


MessageRole = Literal['system', 'user', 'assistant']


@dataclasses.dataclass()
class Message:
    role: MessageRole
    content: str


class GPTSwarm(Agent):
    VERSION = '1.0'
    """
    This is simple revision of GPTSwarm which serve as an assistant agent.

    GPTSwarm Paper: https://arxiv.org/abs/2402.16823 (ICML 2024, Oral Presentation)
    GPTSwarm Code: https://github.com/metauto-ai/GPTSwarm
    """

    def __init__(
        self,
        llm: LLM,
        model_name: str,
    ) -> None:
        """
        Initializes a new instance of the GPTSwarm class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)
        self.api_key = OPENAI_API_KEY
        self.llm = LLM(model=model_name, api_key=self.api_key)
        self.graph = AssistantGraph(domain='gaia', model_name=model_name)
        self.prompt_set = GPTSwarmPromptSet()

    def reset(self) -> None:
        """
        Resets the GPTSwarm Agent.
        """
        super().reset()

    def step(self, state: State) -> Action:
        """
        # TODO: It is stateless now. Find a way to make it stateful.
        # NOTE: For the AI assistant, state-based design may introduce more uncertainties.
        """
        raise NotImplementedError

    async def swarm_run(self, inputs: List[Dict[str, Any]], num_agents=3) -> List[str]:
        """
        Run the `run` method of this agent concurrently for `num_agents` times.
        # NOTE: This is just a simple self-consistency.
        # TODO: should follow original GPTSwarm's graph design to revise.
        """

        async def run_single_agent(index):
            try:
                result = await asyncio.wait_for(self.run(inputs=inputs), timeout=200)
                print('-----------------------------------')
                print(f'No. {index} Agent complete task..')
                logger.info(result[0])
                print('-----------------------------------')
                return result[0]
            except asyncio.TimeoutError:
                print(f'No. {index} Agent timed out.')
                return None
            except Exception as e:
                print(f'No. {index} Agent resulted in an error: {e}')
                return None

        # Create a list of tasks to run concurrently
        tasks = [run_single_agent(i) for i in range(num_agents)]

        # Run all tasks concurrently and gather the results
        agent_answers = await asyncio.gather(*tasks)

        # Filter out None results (from timeouts or errors)
        agent_answers = [answer for answer in agent_answers if answer is not None]

        task = inputs[0]['task']
        prompt = self.prompt_set.get_self_consistency(
            question=task,
            answers=agent_answers,
            constraint=self.prompt_set.get_constraint(),
        )
        messages = [
            Message(role='system', content=f'You are a {self.prompt_set.get_role()}.'),
            Message(role='user', content=prompt),
        ]

        swarm_ans = self.llm.do_completion(
            messages=[{'role': msg.role, 'content': msg.content} for msg in messages]
        )
        swarm_ans = swarm_ans.choices[0].message.content
        return [swarm_ans]

    async def run(
        self,
        inputs: List[Dict[str, Any]],
        max_tries: int = 3,
        max_time: int = 600,
        return_all_outputs: bool = False,
    ) -> List[Any]:
        def is_node_useful(node):
            if node in self.graph.output_nodes:
                return True

            for successor in node.successors:
                if is_node_useful(successor):
                    return True
            return False

        useful_node_ids = [
            node_id
            for node_id, node in self.graph.nodes.items()
            if is_node_useful(node)
        ]
        in_degree = {
            node_id: len(self.graph.nodes[node_id].predecessors)
            for node_id in useful_node_ids
        }
        zero_in_degree_queue = [
            node_id
            for node_id, deg in in_degree.items()
            if deg == 0 and node_id in useful_node_ids
        ]

        for i, input_node in enumerate(self.graph.input_nodes):
            node_input = deepcopy(inputs)
            input_node.inputs = [node_input]

        while zero_in_degree_queue:
            current_node_id = zero_in_degree_queue.pop(0)
            current_node = self.graph.nodes[current_node_id]
            tries = 0
            while tries < max_tries:
                try:
                    await asyncio.wait_for(
                        self.graph.nodes[current_node_id].execute(), timeout=max_time
                    )
                    # TODO: make GPTSwarm stateful in OpenDevin.
                    # State.inputs = self.graph.nodes[current_node_id].inputs
                    # State.outputs = self.graph.nodes[current_node_id].outputs
                    # self.step(State)

                except asyncio.TimeoutError:
                    print(
                        f'Node {current_node_id} execution timed out, retrying {tries + 1} out of {max_tries}...'
                    )
                except Exception as e:
                    print(f'Error during execution of node {current_node_id}: {e}')
                    break
                tries += 1

            for successor in current_node.successors:
                if successor.id in useful_node_ids:
                    in_degree[successor.id] -= 1
                    if in_degree[successor.id] == 0:
                        zero_in_degree_queue.append(successor.id)

        final_answers = []

        for output_node in self.graph.output_nodes:
            output_messages = output_node.outputs

            if len(output_messages) > 0 and not return_all_outputs:
                final_answer = output_messages[-1].get('output', output_messages[-1])
                final_answers.append(final_answer)
            else:
                for output_message in output_messages:
                    final_answer = output_message.get('output', output_message)
                    final_answers.append(final_answer)

        if len(final_answers) == 0:
            final_answers.append('No answer since there are no inputs provided')
        return final_answers

    def search_memory(self, query: str) -> list[str]:
        raise NotImplementedError('Implement this abstract method')
