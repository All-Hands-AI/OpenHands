PAIRED_IMPLEMENT_DEMONSTRATION = """
 {
  "Type and color of each item":
  "Number of items of each color":
  "Number of items of each type":
  "Number of items of each color and type":
  "Final answer":
}

"""

ROLE_DESCRIPTION = """You are a seasoned manager at a Fortune 500 company with a team of capable software engineers.
Your responsibility is to plan the given task for your team. You must only plan and must not code yourself."""

INTERACTION_SKILL = """You are working with a curious user that needs your help. You can directly interact with the user by replying with
<execute_ask> and </execute_ask>. For example, <execute_ask> Are my assumptions correct? </execute_ask>.
"""

BROWSING_SKILL = """You can also browse the Internet with <execute_browse> and </execute_browse>.
For example, <execute_browse> Tell me the usa's president using google search </execute_browse>.
Or <execute_browse> Tell me what is in http://example.com </execute_browse>.
"""

SYSTEM_SUFFIX = """Let the following principles guide your response:
- Before responding read all information carefully.
- Responses should be concise.
- Use only information that's explicitly stated by the user.
"""

# - Use only information that's explicitly stated by the user. You MUST NOT assume anything that is not confirmed by the user. To ask the user for clarirification, you must respond by <execute_ask> your ask </execute_ask>.


# SYSTEM_MESSAGE = ROLE_DESCRIPTION + INTERACTION_SKILL + BROWSING_SKILL + SYSTEM_SUFFIX
SYSTEM_MESSAGE = ROLE_DESCRIPTION + SYSTEM_SUFFIX


RESEASONING_MODULES_LIST = [
    'How could I devise an experiment to help solve that problem?',
    'Make a list of ideas for solving this problem, and apply them one by one to the problem to see if any progress can be made.',
    'How could I measure progress on this problem?',
    'How can I simplify the problem so that it is easier to solve?',
    'What are the key assumptions underlying this problem?',
    'What are the potential risks and drawbacks of each solution?',
    'What are the alternative perspectives or viewpoints on this problem?',
    'What are the long-term implications of this problem and its solutions?',
    'How can I break down this problem into smaller, more manageable parts?',
    'Critical Thinking: This style involves analyzing the problem from different perspectives, questioning assumptions, and evaluating the evidence or information available. It focuses on logical reasoning, evidence-based decision-making, and identifying potential biases or flaws in thinking.',
    'Try creative thinking, generate innovative and out-of-the-box ideas to solve the problem. Explore unconventional solutions, thinking beyond traditional boundaries, and encouraging imagination and originality.',
    'Seek input and collaboration from others to solve the problem. Empha- size teamwork, open communication, and leveraging the diverse per- spectives and expertise of a group to come up with effective solutions.',
    'Use systems thinking: Consider the problem as part of a larger system and understanding the interconnectedness of various elements. Focuses on identifying the underlying causes, feedback loops, and interdepen- dencies that influence the problem, and developing holistic solutions that address the system as a whole.',
    'Use Risk Analysis: Evaluate potential risks, uncertainties, and trade- offs associated with different solutions or approaches to a problem. Em- phasize assessing the potential consequences and likelihood of success or failure, and making informed decisions based on a balanced analysis of risks and benefits.',
    'Use Reflective Thinking: Step back from the problem, take the time for introspection and self-reflection. Examine personal biases, assump- tions, and mental models that may influence problem-solving, and being open to learning from past experiences to improve future approaches.',
    'What is the core issue or problem that needs to be addressed?',
    'What are the underlying causes or factors contributing to the problem?',
    'Are there any potential solutions or strategies that have been tried before? If yes, what were the outcomes and lessons learned?',
    'What are the potential obstacles or challenges that might arise in solving this problem?',
    'Are there any relevant data or information that can provide insights into the problem? If yes, what data sources are available, and how can they be analyzed?',
    'Are there any stakeholders or individuals who are directly affected by the problem? What are their perspectives and needs?',
    'What resources (financial, human, technological, etc.) are needed to tackle the problem effectively?',
    'How can progress or success in solving the problem be measured or evaluated?',
    'What indicators or metrics can be used?',
    'Is the problem a technical or practical one that requires a specific expertise or skill set? Or is it more of a conceptual or theoretical problem?',
    'Does the problem involve a physical constraint, such as limited re- sources, infrastructure, or space?',
    'Is the problem related to human behavior, such as a social, cultural, or psychological issue?',
    'Does the problem involve decision-making or planning, where choices need to be made under uncertainty or with competing objectives?',
    'Is the problem an analytical one that requires data analysis, modeling, or optimization techniques?',
    'Is the problem a design challenge that requires creative solutions and innovation?',
    'Does the problem require addressing systemic or structural issues rather than just individual instances?',
    'Is the problem time-sensitive or urgent, requiring immediate attention and action?',
    'What kinds of solution typically are produced for this kind of problem specification?',
    'Given the problem specification and the current best solution, have a guess about other possible solutions.',
    'Let’s imagine the current best solution is totally wrong, what other ways are there to think about the problem specification?',
    'What is the best way to modify this current best solution, given what you know about these kinds of problem specification?',
    'Ignoring the current best solution, create an entirely new solution to the problem.',
    'Let’s think step by step.',
    'Let’s make a step by step plan and implement it with good notion and explanation.',
]

SELECT_PROMPT = """Select several reasoning moduls that are crucial to solve the following task.

## Task
{task}

## Reasoning modules list
{RESEASONING_MODULES}

## Constraints
Select at most 5 task-relevant reasoning modules.

Your response MUST be in JSON format. It must be an object with the field "reasoning_modules",
which contains the indeces of selected reasoning modules. For example, for selecting reasoning modules
"How could I devise an experiment to help solve that problem?" and "How could I measure progress on this problem?",
you would reply with

{
  "reasoning_modules": [0, 2]
}

You MUST NOT include any other text besides the JSON response.
"""

ADAPT_PROMPT = """Rephrase and specify each previously selected reasoning module so that it better helps solving the user's task.
"""

IMPLEMENT_PROMPT = """Implement a reasoning structure for your team members to follow step-by-step and arrive at correct answers by replying with
<execute_plan>
Your implementation
</execute_plan>.
"""

IMPLEMENT_EXAMPLES = """Example 1 TODO CONTINUE HERE
"""
