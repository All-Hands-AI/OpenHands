#!/usr/bin/env python3
"""
Analyze agent-human interactions in SWE-bench interactive evaluations.
Focus on detecting when agents ask questions to gather more information.
"""
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

class AgentQuestionAnalyzer:
    def __init__(self, eval_base_dir: Optional[Path] = None):
        self.eval_base_dir = eval_base_dir

    def load_resolve_info(self, eval_dir: Path) -> Dict[str, bool]:
        """Load resolve information from report.json file."""
        report_path = eval_dir / "report.json"
        resolve_info = {}
        
        if not report_path.exists():
            return resolve_info
            
        try:
            with open(report_path, 'r') as f:
                report_data = json.load(f)
                
            for instance_id in report_data.get('resolved_ids', []):
                resolve_info[instance_id] = True
            for instance_id in report_data.get('unresolved_ids', []):
                resolve_info[instance_id] = False
                
        except Exception as e:
            print(f"Warning: Could not load report from {report_path}: {e}")
        
        return resolve_info

    def load_jsonl_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load JSONL evaluation data from output file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = [json.loads(line) for line in f if line.strip()]
            print(f"Loaded {len(data)} instances from {file_path}")
            return data
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []

    def is_negative_response(self, response_message: str) -> bool:
        """Check if user response indicates they don't want more questions."""
        message_lower = response_message.lower().strip()
        negative_patterns = [
            'do not ask for more help',
            'don\'t ask for more help',
            'do not ask me',
            'don\'t ask me',
            'stop asking',
            'no more questions',
            'please continue working',
            'just continue',
            'keep working',
            'work on the task',
            'focus on the task',
            'i don\'t have that information',
            'i don\'t have that info',
            'i do not have that information',
            'i do not have that info',
            'no additional information',
            'no further information',
            'i cannot provide that',
            'i can\'t provide that'
        ]
        return any(pattern in message_lower for pattern in negative_patterns)

    def detect_questions(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect questions in agent messages from conversation history.
        A question is defined as an agent message that is followed by a user response."""
        questions = []
        
        for i, entry in enumerate(history):
            if (entry.get('source') == 'agent' and entry.get('action') == 'message' 
                and 'message' in entry):
                
                # Look for next user response
                user_response = None
                for next_entry in history[i+1:]:
                    if (next_entry.get('source') == 'user' and next_entry.get('action') == 'message' 
                        and 'message' in next_entry):
                        user_response = {
                            'timestamp': next_entry.get('timestamp', ''),
                            'message': next_entry['message'],
                            'entry_id': next_entry.get('id', 0),
                            'is_negative': self.is_negative_response(next_entry['message'])
                        }
                        break

                # Include all questions with user responses, but mark negative ones
                if user_response:
                    questions.append({
                        'timestamp': entry.get('timestamp', ''),
                        'message': entry['message'],
                        'entry_id': entry.get('id', 0),
                        'user_response': user_response
                    })

        return questions

    def classify_question_type(self, message: str) -> str:
        """Classify the type of question based on content."""
        message_lower = message.lower()
        
        patterns = [
            (['clarify', 'unclear', 'understand', 'confusing', 'ambiguous'], 'clarification'),
            (['confirm', 'correct', 'right', 'is this'], 'confirmation'),
            (['what is', 'what are', 'what do', 'what does', 'how do', 'how can', 'where is', 'when should', 'why is', 'which'], 'information'),
            (['can you', 'could you', 'would you', 'should i', 'do you want'], 'request'),
            (['do you', 'are you', 'is there', 'will you', 'have you'], 'yes_no'),
        ]
        
        for words, category in patterns:
            if any(word in message_lower for word in words):
                return category
        return 'other'

    def analyze_instance(self, instance: Dict[str, Any], resolve_info: Dict[str, bool] = None) -> Dict[str, Any]:
        """Analyze a single evaluation instance for agent questions."""
        instance_id = instance.get('instance_id', 'unknown')
        history = instance.get('history') or []
        questions = self.detect_questions(history)
        
        # Classify questions
        question_types = defaultdict(int)
        for q in questions:
            question_types[self.classify_question_type(q['message'])] += 1

        return {
            'instance_id': instance_id,
            'question_count': len(questions),
            'questions': questions,
            'question_types': dict(question_types),
            'has_solution': bool(instance.get('test_result', {}).get('git_patch', '').strip()),
            'resolved': resolve_info.get(instance_id) if resolve_info else None,
            'total_history_length': len(history)
        }

    def has_questions_before_step(self, history: List[Dict[str, Any]], max_step: int) -> bool:
        """Check if instance has questions before a given step number."""
        return any(q.get('entry_id', 0) <= max_step for q in self.detect_questions(history))

    def analyze_directory(self, eval_dir: Path, max_step_for_questions: int = None) -> Dict[str, Any]:
        """Analyze all instances in an evaluation directory."""
        output_file = eval_dir / 'output.jsonl'
        
        if not output_file.exists():
            print(f"No output.jsonl found in {eval_dir}")
            return {}

        instances = self.load_jsonl_data(output_file)
        if not instances:
            return {}

        resolve_info = self.load_resolve_info(eval_dir)
        results = [self.analyze_instance(instance, resolve_info) for instance in instances]
        
        # Collect statistics
        stats = self._collect_statistics(results, instances, max_step_for_questions)
        
        return {
            'eval_directory': str(eval_dir),
            'detailed_results': results,
            **stats
        }

    def _collect_statistics(self, results: List[Dict[str, Any]], instances: List[Dict[str, Any]], 
                           max_step_for_questions: int = None) -> Dict[str, Any]:
        """Collect and calculate statistics from analysis results."""
        total_instances = len(results)
        total_questions = sum(r['question_count'] for r in results)
        instances_with_questions = sum(1 for r in results if r['question_count'] > 0)
        instances_with_solutions = sum(1 for r in results if r['has_solution'])
        
        # Question response analysis
        questions_with_responses = 0
        questions_with_positive_responses = 0  
        questions_with_negative_responses = 0
        
        for result in results:
            for question in result['questions']:
                if question.get('user_response'):
                    questions_with_responses += 1
                    if question['user_response'].get('is_negative', False):
                        questions_with_negative_responses += 1
                    else:
                        questions_with_positive_responses += 1
        
        # Resolve statistics - only count positive questions for resolved_with_questions
        resolved_results = [r for r in results if r['resolved'] is not None]
        instances_resolved = sum(1 for r in resolved_results if r['resolved'])
        instances_unresolved = sum(1 for r in resolved_results if not r['resolved'])
        
        # Count instances with more positive than negative questions for resolved_with_questions
        resolved_with_questions = 0
        unresolved_with_questions = 0
        
        for result in resolved_results:
            positive_count = sum(
                1 for q in result['questions'] 
                if q.get('user_response') and not q['user_response'].get('is_negative', False)
            )
            negative_count = sum(
                1 for q in result['questions'] 
                if q.get('user_response') and q['user_response'].get('is_negative', False)
            )
            
            has_more_positive_questions = positive_count > negative_count
            
            if result['resolved'] and has_more_positive_questions:
                resolved_with_questions += 1
            elif not result['resolved'] and has_more_positive_questions:
                unresolved_with_questions += 1
        
        questions_with_solutions = sum(1 for r in results if r['question_count'] > 0 and r['resolved'])
        
        # Question types
        overall_question_types = defaultdict(int)
        for result in results:
            for q_type, count in result['question_types'].items():
                overall_question_types[q_type] += count

        # Calculate rates
        def safe_divide(a, b): return a / b if b > 0 else 0
        
        stats = {
            'total_instances': total_instances,
            'total_questions': total_questions,
            'questions_with_responses': questions_with_responses,
            'questions_with_positive_responses': questions_with_positive_responses,
            'questions_with_negative_responses': questions_with_negative_responses,
            'response_rate': safe_divide(questions_with_responses, total_questions),
            'positive_response_rate': safe_divide(questions_with_positive_responses, questions_with_responses),
            'negative_response_rate': safe_divide(questions_with_negative_responses, questions_with_responses),
            'instances_with_questions': instances_with_questions,
            'instances_with_solutions': instances_with_solutions,
            'instances_resolved': instances_resolved,
            'instances_unresolved': instances_unresolved,
            'resolved_with_questions': resolved_with_questions,  # Only positive questions
            'unresolved_with_questions': unresolved_with_questions,  # Only positive questions
            'avg_questions_per_instance': safe_divide(total_questions, total_instances),
            'question_success_rate': safe_divide(questions_with_solutions, instances_with_questions),
            'overall_success_rate': safe_divide(instances_with_solutions, total_instances),
            'resolve_rate': safe_divide(instances_resolved, instances_resolved + instances_unresolved),
            'resolved_question_rate': safe_divide(resolved_with_questions, instances_resolved + instances_unresolved),
            'question_type_distribution': dict(overall_question_types),
        }
        
        # Add step filtering if specified
        if max_step_for_questions is not None:
            filtered_total_resolved = sum(1 for r in results if r['resolved'])
            filtered_resolved_with_questions = sum(
                1 for i, r in enumerate(results) 
                if r['resolved'] and self.has_questions_before_step(instances[i].get('history', []), max_step_for_questions)
            )
            stats.update({
                'step_filter_max_step': max_step_for_questions,
                'filtered_total_resolved': filtered_total_resolved,
                'filtered_resolved_with_questions': filtered_resolved_with_questions,
                'filtered_resolve_rate_with_questions': safe_divide(filtered_resolved_with_questions, filtered_total_resolved)
            })
            
        return stats

    def generate_report(self, analysis: Dict[str, Any]) -> None:
        """Generate a summary report of the analysis."""
        print(f"\n=== Agent Question Analysis Report ===")
        print(f"Evaluation Directory: {analysis['eval_directory']}")
        print(f"Total Instances: {analysis['total_instances']}")
        print(f"Total Agent Questions: {analysis['total_questions']}")
        print(f"Questions with User Responses: {analysis['questions_with_responses']}")
        print(f"  - Positive Responses: {analysis['questions_with_positive_responses']} ({analysis['positive_response_rate']:.1%})")
        print(f"  - Negative Responses: {analysis['questions_with_negative_responses']} ({analysis['negative_response_rate']:.1%})")
        print(f"Response Rate: {analysis['response_rate']:.2%}")
        print(f"Instances with Questions: {analysis['instances_with_questions']}")
        print(f"Instances with Solutions: {analysis['instances_with_solutions']}")
        print(f"Average Questions per Instance: {analysis['avg_questions_per_instance']:.2f}")
        print(f"Success Rate (instances with questions): {analysis['question_success_rate']:.2%}")
        print(f"Overall Success Rate: {analysis['overall_success_rate']:.2%}")

        # Show resolve information
        if 'instances_resolved' in analysis:
            print(f"\n=== Resolve Information ===")
            print(f"Resolved Instances: {analysis['instances_resolved']}")
            print(f"Unresolved Instances: {analysis['instances_unresolved']}")
            print(f"Overall Resolve Rate: {analysis['resolve_rate']:.2%}")
            print(f"Resolved with More Positive than Negative Questions: {analysis['resolved_with_questions']}")
            print(f"Unresolved with More Positive than Negative Questions: {analysis['unresolved_with_questions']}")
            print(f"Net Positive Question Rate among Resolved: {analysis['resolved_question_rate']:.2%}")

        # Show step filtering results
        if 'step_filter_max_step' in analysis:
            print(f"\n=== Step Filtering Results (Questions before Step {analysis['step_filter_max_step']}) ===")
            print(f"Total Resolved Instances: {analysis['filtered_total_resolved']}")
            print(f"Resolved with Questions before Step {analysis['step_filter_max_step']}: {analysis['filtered_resolved_with_questions']}")
            print(f"Filtered Resolve Rate (with early questions): {analysis['filtered_resolve_rate_with_questions']:.2%}")

        # Show question type distribution
        question_type_dist = analysis.get('question_type_distribution', {})
        if question_type_dist:
            print(f"\n=== Question Type Distribution ===")
            total_typed_questions = sum(question_type_dist.values())
            for q_type, count in sorted(question_type_dist.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_typed_questions) * 100 if total_typed_questions > 0 else 0
                print(f"{q_type.capitalize()}: {count} questions ({percentage:.1f}%)")

        # Show top instances with most questions
        detailed = analysis['detailed_results']
        top_questioners = sorted(detailed, key=lambda x: x['question_count'], reverse=True)[:5]

        print(f"\n=== Top 5 Instances by Question Count ===")
        for i, instance in enumerate(top_questioners, 1):
            resolved_str = "resolved" if instance.get('resolved') else "unresolved" if instance.get('resolved') is False else "unknown"
            print(f"{i}. {instance['instance_id']}: {instance['question_count']} questions "
                  f"({'solved' if instance['has_solution'] else 'unsolved'}, {resolved_str})")

        # Show some example question-answer pairs
        print(f"\n=== Example Question-Answer Pairs ===")
        examples_shown = 0
        for instance in detailed:
            if examples_shown >= 3:  # Show up to 3 examples
                break
            for question in instance['questions']:
                if question.get('user_response') and examples_shown < 3:
                    print(f"\nInstance: {instance['instance_id']}")
                    print(f"Agent Question: {question['message'][:200]}...")
                    print(f"User Response: {question['user_response']['message'][:200]}...")
                    examples_shown += 1
                    break


def main():
    parser = argparse.ArgumentParser(description='Analyze agent questions in SWE-bench interactive evaluations')
    parser.add_argument('eval_dir', type=str, help='Path to evaluation output directory')
    parser.add_argument('--output', '-o', type=str, help='Output JSON file for detailed results')
    parser.add_argument('--max-step', '-s', type=int, default=None, help='Filter resolve rate by instances that asked questions before step N')

    args = parser.parse_args()

    eval_dir = Path(args.eval_dir)
    if not eval_dir.exists():
        print(f"Error: Directory {eval_dir} does not exist")
        return 1

    analyzer = AgentQuestionAnalyzer(eval_base_dir=eval_dir)
    analysis = analyzer.analyze_directory(eval_dir, max_step_for_questions=args.max_step)

    if not analysis:
        print("No analysis results generated")
        return 1

    analyzer.generate_report(analysis)

    # Save detailed results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\nDetailed results saved to {args.output}")

    return 0


if __name__ == '__main__':
    exit(main())
