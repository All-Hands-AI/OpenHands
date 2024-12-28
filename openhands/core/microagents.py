"""MicroAgent system for OpenHands."""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, validator


class TriggerType(str, Enum):
    """Type of trigger for knowledge-based agents."""
    REPOSITORY = "repository"
    KEYWORD = "keyword"


class TemplateType(str, Enum):
    """Type of template-based agent."""
    WORKFLOW = "workflow"
    SNIPPET = "snippet"
    GUIDE = "guide"


class InputValidation(BaseModel):
    """Validation rules for template inputs."""
    pattern: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None


class TemplateInput(BaseModel):
    """Input parameter for template-based agents."""
    name: str
    description: str
    type: str
    required: bool = True
    default: Optional[Any] = None
    validation: Optional[InputValidation] = None


class MicroAgent(BaseModel):
    """Base class for all microagents."""
    name: str
    version: str
    author: str
    agent: str
    category: str
    tags: List[str] = Field(default_factory=list)
    requires: List[str] = Field(default_factory=list)
    description: str
    capabilities: List[str] = Field(default_factory=list)
    guidelines: List[str] = Field(default_factory=list)
    examples: List[Dict[str, str]] = Field(default_factory=list)


class KnowledgeAgent(MicroAgent):
    """Knowledge-based microagent with repository or keyword triggers."""
    trigger_type: TriggerType
    trigger_pattern: Optional[str] = None  # For repository triggers
    triggers: Optional[List[str]] = None   # For keyword triggers
    priority: Optional[int] = None         # For repository triggers
    file_patterns: Optional[List[str]] = None
    knowledge: str

    @validator('trigger_pattern')
    def validate_repo_trigger(cls, v, values):
        """Validate repository trigger pattern."""
        if values.get('trigger_type') == TriggerType.REPOSITORY and not v:
            raise ValueError("trigger_pattern is required for repository triggers")
        return v

    @validator('triggers')
    def validate_keyword_trigger(cls, v, values):
        """Validate keyword triggers."""
        if values.get('trigger_type') == TriggerType.KEYWORD and not v:
            raise ValueError("triggers is required for keyword triggers")
        return v


class TemplateAgent(MicroAgent):
    """Template-based microagent with user inputs."""
    template_type: TemplateType
    template: str
    inputs: List[TemplateInput]


@dataclass
class MicroAgentHub:
    """Central hub for managing microagents."""
    root_dir: Path
    repo_agents: Dict[str, KnowledgeAgent]
    keyword_agents: Dict[str, KnowledgeAgent]
    template_agents: Dict[str, TemplateAgent]

    @classmethod
    def load(cls, root_dir: Union[str, Path] = None) -> 'MicroAgentHub':
        """Load all microagents from the given directory."""
        if root_dir is None:
            # Default to the package's microagents directory
            root_dir = Path(__file__).parent.parent.parent / 'microagents'
        elif isinstance(root_dir, str):
            root_dir = Path(root_dir)

        repo_agents = {}
        keyword_agents = {}
        template_agents = {}

        # Load official agents
        official_dir = root_dir / 'official'
        if official_dir.exists():
            # Load knowledge agents
            knowledge_dir = official_dir / 'knowledge'
            if knowledge_dir.exists():
                # Load repository-triggered agents
                repo_dir = knowledge_dir / 'repo'
                if repo_dir.exists():
                    for file in repo_dir.glob('*.yaml'):
                        with open(file) as f:
                            data = yaml.safe_load(f)
                            agent = KnowledgeAgent(**data)
                            repo_agents[agent.name] = agent

                # Load keyword-triggered agents
                keyword_dir = knowledge_dir / 'keyword'
                if keyword_dir.exists():
                    for file in keyword_dir.glob('*.yaml'):
                        with open(file) as f:
                            data = yaml.safe_load(f)
                            agent = KnowledgeAgent(**data)
                            keyword_agents[agent.name] = agent

            # Load template agents
            template_dir = official_dir / 'templates'
            if template_dir.exists():
                for file in template_dir.rglob('*.yaml'):
                    with open(file) as f:
                        data = yaml.safe_load(f)
                        agent = TemplateAgent(**data)
                        template_agents[agent.name] = agent

        # Load community agents if they exist
        community_dir = root_dir / 'community'
        if community_dir.exists():
            # Similar loading logic for community agents...
            pass

        return cls(
            root_dir=root_dir,
            repo_agents=repo_agents,
            keyword_agents=keyword_agents,
            template_agents=template_agents,
        )

    def get_repo_agents(self, repo_name: str) -> List[KnowledgeAgent]:
        """Get all repository agents that match the given repository name."""
        matching_agents = []
        for agent in self.repo_agents.values():
            # TODO: Implement proper glob pattern matching
            if agent.trigger_pattern and repo_name.startswith(agent.trigger_pattern.replace('*', '')):
                matching_agents.append(agent)
        
        # Sort by priority (higher first)
        matching_agents.sort(key=lambda x: x.priority or 0, reverse=True)
        return matching_agents

    def get_keyword_agents(self, text: str, file_path: Optional[str] = None) -> List[KnowledgeAgent]:
        """Get all keyword agents whose triggers match in the given text."""
        matching_agents = []
        for agent in self.keyword_agents.values():
            if not agent.triggers:
                continue
            
            # Check if any trigger word is present
            if any(trigger.lower() in text.lower() for trigger in agent.triggers):
                # Check file pattern if specified
                if agent.file_patterns and file_path:
                    # TODO: Implement proper glob pattern matching
                    if not any(file_path.endswith(pattern.replace('*', '')) 
                             for pattern in agent.file_patterns):
                        continue
                matching_agents.append(agent)
        
        return matching_agents

    def get_template_agent(self, name: str) -> Optional[TemplateAgent]:
        """Get a template agent by name."""
        return self.template_agents.get(name)

    def list_template_agents(self, template_type: Optional[TemplateType] = None) -> List[TemplateAgent]:
        """List all template agents, optionally filtered by type."""
        if template_type is None:
            return list(self.template_agents.values())
        return [agent for agent in self.template_agents.values() 
                if agent.template_type == template_type]

    def process_template(self, template_name: str, inputs: Dict[str, Any]) -> Optional[str]:
        """Process a template with the given inputs."""
        agent = self.get_template_agent(template_name)
        if not agent:
            return None

        # Validate required inputs
        for input_def in agent.inputs:
            if input_def.required and input_def.name not in inputs:
                raise ValueError(f"Missing required input: {input_def.name}")

        # Process template
        result = agent.template
        for name, value in inputs.items():
            result = result.replace(f"${{{name}}}", str(value))

        return result