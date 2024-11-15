from typing import Any, Dict, List, Optional
from langchain.agents import AgentExecutor, Tool
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from openhands.agents.base import BaseAgent
from openhands.core.config import Config

class SupervisorAgent(BaseAgent):
    def __init__(self, config: Config):
        super().__init__(config)
        self.openhands_instances = {}
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize LLM for supervisor
        self.llm = OpenAI(
            base_url=config.llm.base_url,
            api_key=config.llm.api_key,
            model=config.llm.model,
            temperature=config.llm.temperature
        )
        
        # Create tools for interacting with OpenHands instances
        self.tools = [
            Tool(
                name="delegate_to_openhands",
                func=self._delegate_to_openhands,
                description="Delegate a task to an OpenHands instance"
            ),
            Tool(
                name="create_openhands_instance",
                func=self._create_openhands_instance,
                description="Create a new OpenHands instance"
            )
        ]
        
        # Initialize the agent executor
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    def _delegate_to_openhands(self, instance_id: str, task: str) -> str:
        if instance_id not in self.openhands_instances:
            return f"Error: OpenHands instance {instance_id} not found"
        instance = self.openhands_instances[instance_id]
        return instance.execute(task)

    def _create_openhands_instance(self, instance_id: str) -> str:
        if instance_id in self.openhands_instances:
            return f"Error: OpenHands instance {instance_id} already exists"
        # Create new OpenHands instance with unique LLM
        self.openhands_instances[instance_id] = BaseAgent(self.config)
        return f"Created new OpenHands instance {instance_id}"

    def execute(self, task: str) -> str:
        """Execute a task using the supervisor agent"""
        return self.agent_executor.run(task)

    def get_prompt(self) -> str:
        return """You are a supervisor agent that manages multiple OpenHands instances.
You can delegate tasks to specific instances or create new ones as needed.
Current conversation:
{chat_history}
