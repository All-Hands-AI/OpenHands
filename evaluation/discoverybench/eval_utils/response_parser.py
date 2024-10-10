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


def extract_gen_hypo_from_logs(content):
    error = ''

    # extract workflow
    gen_workflow = extract_between(
        content,
        [
            'WORKFLOW_SUMMARY:',
            '**WORKFLOW_SUMMARY**:',
            "'WORKFLOW_SUMMARY':",
            'WORKFLOW SUMMARY',
        ],
        [
            'FINAL_ANSWER:',
            '**FINAL_ANSWER**:',
            "'FINAL_ANSWER':",
            'FINAL ANSWER',
            'Final Answer',
            'Scientific Hypothesis',
        ],
    )

    if not gen_workflow:
        error += 'No Workflow Summary found in the line. | '

    # extract final answer
    gen_hypothesis = extract_between(
        content,
        [
            'FINAL_ANSWER:',
            '**FINAL_ANSWER**:',
            "'FINAL_ANSWER':",
            'Final Answer',
            'Scientific Hypothesis',
        ],
        [
            'NEXT-AGENT:',
            '**NEXT-AGENT**:',
            "'NEXT-AGENT':",
            'FEEDBACK:',
            '**FEEDBACK**:',
            "'FEEDBACK':",
        ],
    )

    if not gen_hypothesis:
        error += 'No Final Answer in the line.'

    return gen_hypothesis, gen_workflow, error
