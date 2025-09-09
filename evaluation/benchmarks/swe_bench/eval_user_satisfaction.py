#!/usr/bin/env python3
"""
User Satisfaction Evaluation Script for SWE-Bench

This script evaluates agent performance from a user perspective by analyzing trajectories
and generating satisfaction ratings. It focuses on evaluating stateful mode outputs
where user profiles and preferences are considered.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

from litellm import completion as litellm_completion

from openhands.core.config import get_llm_config_arg
from openhands.events.serialization.event import event_from_dict


@dataclass
class UserSatisfactionMetrics:
    """Metrics for user satisfaction evaluation"""
    overall_satisfaction: float  # 1-5 scale
    communication_quality: float  # 1-5 scale
    problem_solving_approach: float  # 1-5 scale
    efficiency: float  # 1-5 scale
    user_preference_alignment: float  # 1-5 scale (for stateful mode)
    explanation: str
    detailed_feedback: Dict[str, str]


class FakeUserEvaluator:
    """Simulates a user evaluating the agent's performance"""
    
    def __init__(self, llm_config_name: str = 'llm.eval_user'):
        self.llm_config = get_llm_config_arg(llm_config_name)
        
    def evaluate_trajectory(
        self, 
        instance: Dict[str, Any], 
        history: List[Dict[str, Any]], 
        test_result: Dict[str, Any],
        user_profile: str = None
    ) -> UserSatisfactionMetrics:
        """
        Evaluate a single trajectory from user perspective
        
        Args:
            instance: The problem instance data
            history: Complete interaction history
            test_result: Results from the agent's attempt
            user_profile: User roleplay prompt (for stateful mode)
        """
        # Extract relevant information from trajectory
        user_messages = []
        agent_messages = []
        actions_taken = []
        
        for event in history:
            if event.get('source') == 'user':
                if event.get('action') == 'message':
                    user_messages.append(event.get('args', {}).get('content', ''))
            elif event.get('source') == 'agent':
                if event.get('action') == 'message':
                    agent_messages.append(event.get('args', {}).get('content', ''))
                elif event.get('action') in ['run', 'str_replace', 'create', 'edit']:
                    actions_taken.append({
                        'action': event.get('action'),
                        'args': event.get('args', {})
                    })
        
        # Build evaluation prompt
        evaluation_prompt = self._build_evaluation_prompt(
            instance, user_messages, agent_messages, actions_taken, test_result, user_profile
        )
        
        # Get LLM evaluation
        response = litellm_completion(
            model=self.llm_config.model,
            messages=[{'role': 'user', 'content': evaluation_prompt}],
            api_key=self.llm_config.api_key.get_secret_value(),
            base_url=self.llm_config.base_url,
            temperature=0.1,
        )
        
        # Parse response into metrics
        return self._parse_evaluation_response(response.choices[0].message.content)
    
    def _build_evaluation_prompt(
        self, 
        instance: Dict[str, Any], 
        user_messages: List[str], 
        agent_messages: List[str], 
        actions_taken: List[Dict[str, Any]],
        test_result: Dict[str, Any],
        user_profile: str = None
    ) -> str:
        """Build the evaluation prompt for the LLM"""
        
        # Base context
        problem_statement = instance.get('problem_statement', 'No problem statement provided')
        instance_id = instance.get('instance_id', 'Unknown')
        git_patch = test_result.get('git_patch', '')
        
        # User profile context (for stateful mode)
        profile_context = ""
        if user_profile:
            profile_context = f"""
USER PROFILE CONTEXT:
The user has a specific profile with preferences: {user_profile}

The agent should have adapted its behavior to align with these user preferences.
"""

        # Count interactions
        interaction_count = len(user_messages)
        
        prompt = f"""
You are evaluating an AI coding agent's performance from a USER PERSPECTIVE. 

PROBLEM CONTEXT:
Instance ID: {instance_id}
Problem: {problem_statement}

{profile_context}

INTERACTION SUMMARY:
- Total user-agent interactions: {interaction_count}
- Agent took {len(actions_taken)} technical actions
- Final result: {'Some changes made' if git_patch.strip() else 'No changes made'}

USER MESSAGES ({len(user_messages)} total):
{chr(10).join([f"User {i+1}: {msg[:200]}..." if len(msg) > 200 else f"User {i+1}: {msg}" for i, msg in enumerate(user_messages)]) if user_messages else "No user messages"}

AGENT MESSAGES ({len(agent_messages)} total):
{chr(10).join([f"Agent {i+1}: {msg[:200]}..." if len(msg) > 200 else f"Agent {i+1}: {msg}" for i, msg in enumerate(agent_messages)]) if agent_messages else "No agent messages"}

TECHNICAL ACTIONS TAKEN:
{chr(10).join([f"- {action['action']}: {str(action['args'])[:100]}..." if len(str(action['args'])) > 100 else f"- {action['action']}: {action['args']}" for action in actions_taken[:10]]) if actions_taken else "No technical actions taken"}
{f"... and {len(actions_taken) - 10} more actions" if len(actions_taken) > 10 else ""}

FINAL RESULT:
Git patch length: {len(git_patch)} characters
{"Preview: " + git_patch[:300] + "..." if len(git_patch) > 300 else git_patch if git_patch.strip() else "No changes were made to the codebase."}

EVALUATION INSTRUCTIONS:
Rate the agent's performance from 1-5 (1=Very Poor, 2=Poor, 3=Average, 4=Good, 5=Excellent) on:

1. OVERALL_SATISFACTION: How satisfied would a user be with this interaction?
2. COMMUNICATION_QUALITY: How well did the agent communicate with the user?
3. PROBLEM_SOLVING_APPROACH: How systematic and effective was the agent's approach?
4. EFFICIENCY: How efficiently did the agent work (not too slow, not too rushed)?
5. USER_PREFERENCE_ALIGNMENT: How well did the agent respect user preferences? {f"(Consider the user profile: {user_profile[:100]}...)" if user_profile and len(user_profile) > 100 else f"(Consider the user profile)" if user_profile else "(Rate based on general user expectations)"}

Respond in this EXACT JSON format:
{{
    "overall_satisfaction": 4.2,
    "communication_quality": 4.0,
    "problem_solving_approach": 4.5,
    "efficiency": 3.8,
    "user_preference_alignment": 4.1,
    "explanation": "Brief explanation of the overall rating",
    "detailed_feedback": {{
        "strengths": "What the agent did well",
        "weaknesses": "What could be improved",
        "user_experience": "How this felt from user perspective"
    }}
}}
"""
        return prompt
    
    def _parse_evaluation_response(self, response: str) -> UserSatisfactionMetrics:
        """Parse the LLM response into structured metrics"""
        try:
            # Extract JSON from response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:-3]
            elif response.startswith('```'):
                response = response[3:-3]
            
            data = json.loads(response)
            
            return UserSatisfactionMetrics(
                overall_satisfaction=float(data.get('overall_satisfaction', 0)),
                communication_quality=float(data.get('communication_quality', 0)),
                problem_solving_approach=float(data.get('problem_solving_approach', 0)),
                efficiency=float(data.get('efficiency', 0)),
                user_preference_alignment=float(data.get('user_preference_alignment', 0)),
                explanation=data.get('explanation', ''),
                detailed_feedback=data.get('detailed_feedback', {})
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Could not parse evaluation response: {e}")
            print(f"Response: {response}")
            return UserSatisfactionMetrics(
                overall_satisfaction=0,
                communication_quality=0,
                problem_solving_approach=0,
                efficiency=0,
                user_preference_alignment=0,
                explanation=f"Failed to parse response: {str(e)}",
                detailed_feedback={}
            )


def evaluate_output_file(
    output_file: str, 
    evaluator: FakeUserEvaluator,
    max_instances: int = None
) -> Dict[str, Any]:
    """Evaluate all instances in an output file"""
    results = []
    
    with open(output_file, 'r') as f:
        for i, line in enumerate(f):
            if max_instances and i >= max_instances:
                break
                
            try:
                instance_data = json.loads(line)
                
                # Convert history events from dicts to proper format if needed
                history = instance_data.get('history', [])
                
                # Extract user profile if available (for stateful mode)
                user_profile = None
                instance_dict = instance_data.get('instance', {})
                if isinstance(instance_dict, dict) and 'user_roleplay_prompt' in instance_dict:
                    user_profile = instance_dict['user_roleplay_prompt']
                
                # Evaluate this instance
                metrics = evaluator.evaluate_trajectory(
                    instance=instance_dict,
                    history=history,
                    test_result=instance_data.get('test_result', {}),
                    user_profile=user_profile
                )
                
                result = {
                    'instance_id': instance_data.get('instance_id'),
                    'metrics': {
                        'overall_satisfaction': metrics.overall_satisfaction,
                        'communication_quality': metrics.communication_quality,
                        'problem_solving_approach': metrics.problem_solving_approach,
                        'efficiency': metrics.efficiency,
                        'user_preference_alignment': metrics.user_preference_alignment,
                    },
                    'explanation': metrics.explanation,
                    'detailed_feedback': metrics.detailed_feedback,
                    'has_user_profile': user_profile is not None,
                    'trajectory_length': len(history)
                }
                
                results.append(result)
                print(f"Evaluated {instance_data.get('instance_id')}: Overall satisfaction = {metrics.overall_satisfaction:.2f}")
                
            except Exception as e:
                print(f"Error processing instance {i}: {e}")
                continue
    
    return aggregate_results(results)


def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate evaluation results"""
    if not results:
        return {}
    
    # Calculate averages
    metrics = ['overall_satisfaction', 'communication_quality', 'problem_solving_approach', 'efficiency', 'user_preference_alignment']
    averages = {}
    
    for metric in metrics:
        values = [r['metrics'][metric] for r in results if r['metrics'][metric] > 0]
        averages[metric] = sum(values) / len(values) if values else 0
    
    # Separate stateful vs non-stateful results
    stateful_results = [r for r in results if r['has_user_profile']]
    non_stateful_results = [r for r in results if not r['has_user_profile']]
    
    def calc_avg_for_subset(subset, metric):
        values = [r['metrics'][metric] for r in subset if r['metrics'][metric] > 0]
        return sum(values) / len(values) if values else 0
    
    stateful_averages = {}
    non_stateful_averages = {}
    
    for metric in metrics:
        stateful_averages[metric] = calc_avg_for_subset(stateful_results, metric)
        non_stateful_averages[metric] = calc_avg_for_subset(non_stateful_results, metric)
    
    return {
        'summary': {
            'total_instances': len(results),
            'stateful_instances': len(stateful_results),
            'non_stateful_instances': len(non_stateful_results),
            'average_trajectory_length': sum(r['trajectory_length'] for r in results) / len(results)
        },
        'overall_averages': averages,
        'stateful_averages': stateful_averages,
        'non_stateful_averages': non_stateful_averages,
        'detailed_results': results
    }


def main():
    parser = argparse.ArgumentParser(description='Evaluate user satisfaction from SWE-Bench trajectories')
    parser.add_argument('--input-dir', type=str, required=True,
                        help='Directory containing output.jsonl files to evaluate')
    parser.add_argument('--output-file', type=str, required=True,
                        help='Output file for evaluation results')
    parser.add_argument('--llm-config', type=str, default='llm.eval_user',
                        help='LLM config name for evaluation')
    parser.add_argument('--max-instances', type=int, default=None,
                        help='Maximum number of instances to evaluate per file')
    parser.add_argument('--recursive', action='store_true',
                        help='Search for output.jsonl files recursively')
    
    args = parser.parse_args()
    
    # Initialize evaluator
    evaluator = FakeUserEvaluator(args.llm_config)
    
    # Find all output files
    input_path = Path(args.input_dir)
    if args.recursive:
        output_files = list(input_path.rglob('output.jsonl'))
    else:
        output_files = list(input_path.glob('*/output.jsonl'))
        output_files.extend(list(input_path.glob('output.jsonl')))
    
    if not output_files:
        print(f"No output.jsonl files found in {args.input_dir}")
        sys.exit(1)
    
    print(f"Found {len(output_files)} output files to evaluate")
    
    # Evaluate each file
    all_results = {}
    
    for output_file in output_files:
        print(f"\nEvaluating {output_file}...")
        file_results = evaluate_output_file(str(output_file), evaluator, args.max_instances)
        all_results[str(output_file)] = file_results
    
    # Save results
    with open(args.output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Print summary
    print(f"\nEvaluation complete! Results saved to {args.output_file}")
    
    # Print overall summary
    total_instances = sum(result['summary']['total_instances'] for result in all_results.values() if result)
    if total_instances > 0:
        print(f"\nOVERALL SUMMARY ({total_instances} instances):")
        
        # Calculate overall averages across all files
        all_instance_results = []
        for file_results in all_results.values():
            if file_results and 'detailed_results' in file_results:
                all_instance_results.extend(file_results['detailed_results'])
        
        if all_instance_results:
            overall_aggregated = aggregate_results(all_instance_results)
            averages = overall_aggregated['overall_averages']
            
            print(f"Overall Satisfaction: {averages['overall_satisfaction']:.2f}/5")
            print(f"Communication Quality: {averages['communication_quality']:.2f}/5")
            print(f"Problem Solving: {averages['problem_solving_approach']:.2f}/5")
            print(f"Efficiency: {averages['efficiency']:.2f}/5")
            print(f"User Preference Alignment: {averages['user_preference_alignment']:.2f}/5")
            
            if overall_aggregated['summary']['stateful_instances'] > 0:
                print(f"\nStateful Mode Results ({overall_aggregated['summary']['stateful_instances']} instances):")
                stateful_avg = overall_aggregated['stateful_averages']
                print(f"Overall Satisfaction: {stateful_avg['overall_satisfaction']:.2f}/5")
                print(f"User Preference Alignment: {stateful_avg['user_preference_alignment']:.2f}/5")


if __name__ == '__main__':
    main()