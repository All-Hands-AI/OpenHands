#!/usr/bin/env python3
"""
Demo script for the Automation Agent - showcasing Manus.im-like capabilities
"""

import json

# Add the OpenHands directory to the Python path
import sys

sys.path.insert(0, '/workspace/OpenHands')

from openhands.agenthub.automation_agent.automation_agent import (
    AutomationAgent,
    TaskType,
)
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.events.action import MessageAction


class AutomationAgentDemo:
    """Demo class to showcase Automation Agent capabilities."""

    def __init__(self):
        """Initialize the demo with a mock LLM and agent."""
        # Create a mock LLM configuration
        self.llm = self._create_mock_llm()

        # Create agent configuration
        self.config = AgentConfig(
            enable_cmd=True,
            enable_browsing=True,
            enable_jupyter=True,
            enable_editor=True,
            enable_think=True,
            enable_finish=True,
        )

        # Create the automation agent
        self.agent = AutomationAgent(self.llm, self.config)

    def _create_mock_llm(self):
        """Create a mock LLM for demonstration purposes."""

        class MockLLM:
            def __init__(self):
                self.config = type('Config', (), {'model': 'mock-model'})()

            def completion(self, *args, **kwargs):
                return type(
                    'Response',
                    (),
                    {
                        'choices': [
                            type(
                                'Choice',
                                (),
                                {
                                    'message': type(
                                        'Message',
                                        (),
                                        {
                                            'content': 'Mock LLM response for demonstration'
                                        },
                                    )()
                                },
                            )()
                        ]
                    },
                )()

        return MockLLM()

    def demo_task_creation(self):
        """Demonstrate task creation and management."""
        print('🎯 Demo: Task Creation and Management')
        print('=' * 50)

        # Create various types of tasks
        tasks = [
            {
                'description': 'Research AI trends in healthcare for 2024',
                'task_type': TaskType.RESEARCH,
                'priority': 3,
            },
            {
                'description': 'Create a comprehensive market analysis report',
                'task_type': TaskType.CONTENT_CREATION,
                'priority': 2,
                'dependencies': ['task_1'],
            },
            {
                'description': 'Build a data visualization dashboard',
                'task_type': TaskType.SOFTWARE_DEVELOPMENT,
                'priority': 1,
            },
            {
                'description': 'Analyze customer satisfaction data',
                'task_type': TaskType.DATA_ANALYSIS,
                'priority': 2,
            },
        ]

        created_tasks = []
        for task_data in tasks:
            task = self.agent.create_task(**task_data)
            created_tasks.append(task)
            print(f'✅ Created {task.task_type.value} task: {task.description}')

        print(f'\n📊 Total tasks created: {len(created_tasks)}')

        # Show task status
        status = self.agent.get_task_status()
        print(f'📈 Agent status: {json.dumps(status, indent=2, default=str)}')

        return created_tasks

    def demo_workflow_planning(self):
        """Demonstrate workflow planning capabilities."""
        print('\n🔄 Demo: Workflow Planning')
        print('=' * 50)

        # Example complex task that needs planning
        complex_task = """
        Create a comprehensive business intelligence system that:
        1. Researches market trends in the AI industry
        2. Analyzes competitor data and strategies
        3. Processes internal sales and customer data
        4. Generates predictive models for growth
        5. Creates an executive dashboard
        6. Writes a strategic recommendations report
        """

        print(f'📋 Complex Task: {complex_task.strip()}')

        # Create a mixed task that requires planning
        planning_task = self.agent.create_task(
            description=complex_task.strip(),
            task_type=TaskType.MIXED,
            priority=5,
            metadata={
                'complexity': 'high',
                'estimated_duration': '2-3 days',
                'required_skills': [
                    'research',
                    'data_analysis',
                    'development',
                    'content_creation',
                ],
            },
        )

        print(f'✅ Created planning task: {planning_task.task_id}')
        print(f'📊 Task metadata: {json.dumps(planning_task.metadata, indent=2)}')

        return planning_task

    def demo_autonomous_execution(self):
        """Demonstrate autonomous task execution."""
        print('\n🤖 Demo: Autonomous Execution')
        print('=' * 50)

        # Create a state with a user message
        state = State()
        user_message = MessageAction(
            content='I need you to research the latest trends in AI automation tools like Manus.im and create a comprehensive competitive analysis report. Include market size, key players, features comparison, and strategic recommendations.'
        )
        user_message._source = 'user'
        state.history.append(user_message)

        print(f'👤 User Request: {user_message.content}')

        # Simulate agent execution
        print('\n🔄 Agent Processing...')

        try:
            # Get agent's response (simplified for demo - would normally call step)
            print('🤖 Agent would process this request and create appropriate tasks...')

            # Show current task status
            if self.agent.current_task:
                print(f'📋 Current Task: {self.agent.current_task.description}')
                print(f'📊 Task Status: {self.agent.current_task.status.value}')
            else:
                print('📋 Agent has created a new task to handle this request')

            action = 'Demo completed successfully'

        except Exception as e:
            print(f'❌ Error during execution: {e}')
            action = None

        return action

    def demo_tool_capabilities(self):
        """Demonstrate the available tools and their capabilities."""
        print('\n🛠️ Demo: Tool Capabilities')
        print('=' * 50)

        tools = self.agent.tools
        print(f'📦 Total tools available: {len(tools)}')

        tool_categories = {
            'Core Tools': [
                'cmd_run',
                'str_replace_editor',
                'ipython',
                'browser',
                'think',
            ],
            'Automation Tools': [
                'research',
                'create_content',
                'plan_task',
                'orchestrate_workflow',
                'verify_result',
            ],
        }

        for category, tool_names in tool_categories.items():
            print(f'\n📂 {category}:')
            for tool in tools:
                if (
                    tool
                    and 'function' in tool
                    and tool['function']['name'] in tool_names
                ):
                    name = tool['function']['name']
                    desc = tool['function']['description'].split('\n')[0].strip()
                    print(f'  ✅ {name}: {desc}')

        # Show automation-specific capabilities
        print('\n🎯 Automation Capabilities:')
        capabilities = [
            '🔍 Comprehensive Research & Analysis',
            '✍️ Content Creation & Documentation',
            '💻 Software Development & Deployment',
            '📊 Data Analysis & Visualization',
            '🔄 Workflow Orchestration & Automation',
            '📋 Task Planning & Management',
            '✅ Quality Verification & Testing',
        ]

        for capability in capabilities:
            print(f'  {capability}')

    def demo_quality_assurance(self):
        """Demonstrate quality assurance and verification capabilities."""
        print('\n✅ Demo: Quality Assurance')
        print('=' * 50)

        # Example verification scenarios
        verification_scenarios = [
            {
                'type': 'output_validation',
                'target': 'research_report.md',
                'criteria': ['completeness', 'accuracy', 'citations'],
            },
            {
                'type': 'code_review',
                'target': 'api_server.py',
                'criteria': ['functionality', 'security', 'performance'],
            },
            {
                'type': 'data_validation',
                'target': 'sales_analysis.csv',
                'criteria': ['data_quality', 'statistical_validity', 'insights'],
            },
        ]

        print('🔍 Verification Scenarios:')
        for i, scenario in enumerate(verification_scenarios, 1):
            print(f'  {i}. {scenario["type"].replace("_", " ").title()}')
            print(f'     Target: {scenario["target"]}')
            print(f'     Criteria: {", ".join(scenario["criteria"])}')

        print('\n📊 Quality Standards:')
        standards = [
            '🎯 Accuracy: All information must be factually correct',
            '📝 Completeness: All requirements must be addressed',
            '🔧 Functionality: All code must work as intended',
            '📚 Documentation: Clear explanations and instructions',
            '🔒 Security: Follow security best practices',
            '⚡ Performance: Optimize for efficiency and speed',
        ]

        for standard in standards:
            print(f'  {standard}')

    def run_full_demo(self):
        """Run the complete demonstration."""
        print('🚀 Automation Agent Demo - Manus.im-like Capabilities')
        print('=' * 60)
        print('This demo showcases a comprehensive AI agent for full task automation')
        print('=' * 60)

        # Run all demo sections
        self.demo_task_creation()
        self.demo_workflow_planning()
        self.demo_autonomous_execution()
        self.demo_tool_capabilities()
        self.demo_quality_assurance()

        print('\n🎉 Demo Complete!')
        print('=' * 60)
        print('The Automation Agent provides comprehensive capabilities for:')
        print('• Research and information gathering')
        print('• Content creation and documentation')
        print('• Software development and deployment')
        print('• Data analysis and visualization')
        print('• Workflow orchestration and automation')
        print('• Quality assurance and verification')
        print('\nReady to handle complex, multi-step tasks autonomously!')


if __name__ == '__main__':
    demo = AutomationAgentDemo()
    demo.run_full_demo()
