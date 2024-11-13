workflow_summary_markers = [
    'WORKFLOW SUMMARY',
    'WORKFLOW_SUMMARY',
    'WORKFLOW-SUMMARY',
    'Workflow Summary',
]

final_answer_markers = [
    'FINAL ANSWER',
    'FINAL_ANSWER',
    'FINAL-ANSWER',
    'Final Answer',
    'Scientific Hypothesis',
    'Hypothesis',
]

next_agent_markers = [
    'NEXT AGENT',
    'NEXT-AGENT',
    'NEXT_AGENT',
    'FEEDBACK',
]


def extract_between(content, start_markers, end_markers=None):
    for marker in start_markers:
        if marker in content:
            result = content.split(marker, 1)[1]
            if end_markers:
                for end_marker in end_markers:
                    if end_marker in result:
                        result = result.split(end_marker, 1)[0]
            return result
    return ''


def extract_gen_hypo_from_logs(content: str):
    error = ''

    gen_workflow = extract_between(
        content, workflow_summary_markers, final_answer_markers
    )

    if not gen_workflow:
        error += 'No Workflow Summary found in the line. | '

    gen_hypothesis = extract_between(content, final_answer_markers, next_agent_markers)

    if not gen_hypothesis:
        error += 'No Final Answer in the line.'

    return gen_hypothesis, gen_workflow, error
