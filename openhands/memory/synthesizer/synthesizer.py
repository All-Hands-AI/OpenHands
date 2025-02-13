from typing import List, Optional, Tuple
from dataclasses import dataclass

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.events.stream import EventStream


@dataclass
class Environment:
    """Represents the environment for agent interaction"""
    def reset(self):
        """Reset the environment to initial state"""
        pass

    def get_observation(self) -> str:
        """Get current observation from environment"""
        pass

    def finished(self) -> bool:
        """Check if interaction is complete"""
        pass


class AgentSynthesizer:
    def __init__(
        self,
        llm_config: LLMConfig,
        event_stream: EventStream,
    ):
        self.llm = llm_config.get_llm()
        self.event_stream = event_stream

    def synthesize(
        self,
        doc: str,
        environment: Environment,
        num_instructions: int,
        data_filter: Optional[callable] = None
    ) -> List[Tuple[str, List[Event]]]:
        """Synthesize agent interaction data based on documentation

        Args:
            doc: Standard documentation/instructions
            environment: Environment to interact with
            num_instructions: Number of instructions to generate per document
            data_filter: Optional filter function for generated data

        Returns:
            List of tuples containing (instruction, trajectory)
        """
        synthesized_data = []

        for _ in range(num_instructions):
            # Generate task instructions
            instructions = self.llm.generate_instructions(doc, num_instructions)

            for instruction in instructions:
                # Initialize trajectory for this instruction
                trajectory = []
                environment.reset()

                # Generate interaction trajectory
                while not environment.finished():
                    observation = environment.get_observation()
                    action = self.llm.generate_action(instruction, trajectory, observation)
                    trajectory.append((observation, action))

                # Add final observation
                trajectory.append((environment.get_observation(), None))

                # Backward construction to generate new instructions
                for i in range(0, len(trajectory) - 1, 2):
                    for j in range(i + 2, len(trajectory), 2):
                        sub_trajectory = trajectory[i:j]
                        # Generate new instruction from sub-trajectory
                        new_instruction = self.llm.generate_instruction_from_trajectory(
                            sub_trajectory
                        )
                        synthesized_data.append((new_instruction, sub_trajectory))

        # Filter low-quality data if filter provided
        if data_filter:
            synthesized_data = data_filter(synthesized_data)

        return synthesized_data

    def save_synthesized_data(self, data: List[Tuple[str, List[Event]]]):
        """Save synthesized data to event stream
        
        Args:
            data: List of (instruction, trajectory) pairs
        """
        for instruction, trajectory in data:
            # Create events from trajectory and add to stream
            for observation, action in trajectory:
                if observation:
                    self.event_stream.add_event(
                        Event(type="observation", content=observation)
                    )
                if action:
                    self.event_stream.add_event(
                        Event(type="action", content=action)
                    ) 