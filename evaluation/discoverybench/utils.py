def extract_gen_hypo_from_logs(content):
    gen_workflow = ''
    gen_hypothesis = ''
    error = ''

    # extract workflow
    if 'WORKFLOW_SUMMARY:' in content:
        gen_workflow = content.split('WORKFLOW_SUMMARY:')[1]
    if '**WORKFLOW_SUMMARY**' in content:
        gen_workflow = content.split('**WORKFLOW_SUMMARY**:')[1]
    if "'WORKFLOW_SUMMARY'" in content:
        gen_workflow = content.split("'WORKFLOW_SUMMARY':")[1]
    if 'WORKFLOW SUMMARY' in content:
        gen_workflow = content.split('WORKFLOW SUMMARY')[1]

    if 'FINAL_ANSWER:' in gen_workflow:
        gen_workflow = gen_workflow.split('FINAL_ANSWER:')[0]
    if '**FINAL_ANSWER**' in gen_workflow:
        gen_workflow = gen_workflow.split('**FINAL_ANSWER**:')[0]
    if "'FINAL_ANSWER'" in gen_workflow:
        gen_workflow = gen_workflow.split("'FINAL_ANSWER':")[0]
    if 'FINAL ANSWER' in gen_workflow:
        gen_workflow = gen_workflow.split('FINAL ANSWER')[0]
    if 'Final Answer' in gen_workflow:
        gen_workflow = gen_workflow.split('Final Answer')[0]
    if 'Scientific Hypothesis' in gen_workflow:
        gen_workflow = gen_workflow.split('Scientific Hypothesis')[0]

    if gen_workflow == '':
        error += 'No Workflow Summary found in the line. | '

    # extract final answer
    if 'FINAL_ANSWER:' in content:
        gen_hypothesis = content.split('FINAL_ANSWER:')[1]
    if '**FINAL_ANSWER**' in content:
        gen_hypothesis = content.split('**FINAL_ANSWER**:')[1]
    if "'FINAL_ANSWER'" in content:
        gen_hypothesis = content.split("'FINAL_ANSWER':")[1]
    if 'Final Answer' in content:
        gen_hypothesis = content.split('Final Answer')[1]
    if 'Scientific Hypothesis' in content:
        gen_hypothesis = content.split('Scientific Hypothesis')[1]

    if 'NEXT-AGENT:' in gen_hypothesis:
        gen_hypothesis = gen_hypothesis.split('NEXT-AGENT:')[0]
    if '**NEXT-AGENT**' in gen_hypothesis:
        gen_hypothesis = gen_hypothesis.split('**NEXT-AGENT**:')[0]
    if "'NEXT-AGENT'" in gen_hypothesis:
        gen_hypothesis = gen_hypothesis.split("'NEXT-AGENT':")[0]

    if 'FEEDBACK' in gen_hypothesis:
        gen_hypothesis = gen_hypothesis.split('FEEDBACK:')[0]
    if '**FEEDBACK**' in gen_hypothesis:
        gen_hypothesis = gen_hypothesis.split('**FEEDBACK**:')[0]
    if "'FEEDBACK'" in gen_hypothesis:
        gen_hypothesis = gen_hypothesis.split("'FEEDBACK':")[0]

    if gen_hypothesis == '':
        error += 'No Final Answer in the line.'

    return gen_hypothesis, gen_workflow, error
