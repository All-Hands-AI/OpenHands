from .agent import SelfDiscoverStep

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
Your duty is to plan the user given task for your team."""

INTERACTION_SKILL = """You are working with a curious user that needs your help. You can directly interact with the user by replying with
<execute_ask> and </execute_ask>. For example, <execute_ask> Are my assumptions correct? </execute_ask>.
"""

BROWSING_SKILL = """You can also browse the Internet with <execute_browse> and </execute_browse>.
For example, <execute_browse> Tell me the usa's president using google search </execute_browse>.
Or <execute_browse> Tell me what is in http://example.com </execute_browse>.
"""

SYSTEM_SUFFIX = """Let the following principles guide your response.
- Before responding read all information carefully.
- Use only information that's explicitly stated by the user. You MUST NOT assume anything that is not confirmed by the user. To ask the user for clarirification, you must respond by <execute_ask> your ask </execute_ask>.
- Responses should be concise.
"""


SYSTEM_MESSAGE = ROLE_DESCRIPTION + INTERACTION_SKILL + BROWSING_SKILL + SYSTEM_SUFFIX


SELECT_PREFIX = """Select several reasoning moduls that are crucial to solve the question above.
"""

RESEASONING_MODULES = """The following reasoning modules are at your disposal.
1. How could I devise an experiment to help solve that problem?
2. Make a list of ideas for solving this problem, and apply them one by one to the problem to see if any progress can be made.
3. How could I measure progress on this problem?
4. How can I simplify the problem so that it is easier to solve?
5. What are the key assumptions underlying this problem?
6. What are the potential risks and drawbacks of each solution?
7. What are the alternative perspectives or viewpoints on this problem?
8. What are the long-term implications of this problem and its solutions?
9. How can I break down this problem into smaller, more manageable parts?
10. Critical Thinking: This style involves analyzing the problem from different perspectives, questioning assumptions, and evaluating the evidence or information available. It focuses on logical reasoning, evidence-based decision-making, and identifying potential biases or flaws in thinking.
11. Try creative thinking, generate innovative and out-of-the-box ideas to solve the problem. Explore unconventional solutions, thinking beyond traditional boundaries, and encouraging imagination and originality.
12. Seek input and collaboration from others to solve the problem. Empha- size teamwork, open communication, and leveraging the diverse per- spectives and expertise of a group to come up with effective solutions.
13. Use systems thinking: Consider the problem as part of a larger system and understanding the interconnectedness of various elements. Focuses on identifying the underlying causes, feedback loops, and interdepen- dencies that influence the problem, and developing holistic solutions that address the system as a whole.
14. Use Risk Analysis: Evaluate potential risks, uncertainties, and trade- offs associated with different solutions or approaches to a problem. Em- phasize assessing the potential consequences and likelihood of success or failure, and making informed decisions based on a balanced analysis of risks and benefits.
15. Use Reflective Thinking: Step back from the problem, take the time for introspection and self-reflection. Examine personal biases, assump- tions, and mental models that may influence problem-solving, and being open to learning from past experiences to improve future approaches.
16. What is the core issue or problem that needs to be addressed?
17. What are the underlying causes or factors contributing to the problem?
18. Are there any potential solutions or strategies that have been tried before? If yes, what were the outcomes and lessons learned?
19. What are the potential obstacles or challenges that might arise in solving this problem?
20. Are there any relevant data or information that can provide insights into the problem? If yes, what data sources are available, and how can they be analyzed?
21. Are there any stakeholders or individuals who are directly affected by the problem? What are their perspectives and needs?
22. What resources (financial, human, technological, etc.) are needed to tackle the problem effectively?
23. How can progress or success in solving the problem be measured or evaluated?
24. What indicators or metrics can be used?
25. Is the problem a technical or practical one that requires a specific expertise or skill set? Or is it more of a conceptual or theoretical problem?
26. Does the problem involve a physical constraint, such as limited re- sources, infrastructure, or space?
27. Is the problem related to human behavior, such as a social, cultural, or psychological issue?
28. Does the problem involve decision-making or planning, where choices need to be made under uncertainty or with competing objectives?
29. Is the problem an analytical one that requires data analysis, modeling, or optimization techniques?
30. Is the problem a design challenge that requires creative solutions and innovation?
31. Does the problem require addressing systemic or structural issues rather than just individual instances?
32. Is the problem time-sensitive or urgent, requiring immediate attention and action?
33. What kinds of solution typically are produced for this kind of problem specification?
34. Given the problem specification and the current best solution, have a guess about other possible solutions.
35. Let’s imagine the current best solution is totally wrong, what other ways are there to think about the problem specification?
36. What is the best way to modify this current best solution, given what you know about these kinds of problem specification?
37. Ignoring the current best solution, create an entirely new solution to the problem.
38. Let’s think step by step.
39. Let’s make a step by step plan and implement it with good notion and explanation.
Note that the order of these reasoning models is arbitrary.
"""

SELECT_PROMPT = SELECT_PREFIX + RESEASONING_MODULES

ADAPT_PROMPT = """Rephrase and specify each previously selected reasoning module so that it better helps solving the question.
"""

IMPLEMENT_PROMPT = """Implement a reasoning structure for your team members to follow step-by-step and arrive at correct answers by replying with
<execute_plan>
Your implementation
</execute_plan>.
"""

IMPLEMENT_EXAMPLES = """Example 1 TODO CONTINUE HERE
"""


def get_prompt(
    previous_step: SelfDiscoverStep, current_step: SelfDiscoverStep
) -> dict[str, str] | None:
    if previous_step == current_step:
        return None

    if current_step == SelfDiscoverStep.SELECT:
        content = SELECT_PROMPT
    elif current_step == SelfDiscoverStep.ADAPT:
        content = ADAPT_PROMPT
    elif current_step == SelfDiscoverStep.IMPLEMENT:
        content = IMPLEMENT_PROMPT
    else:
        content = ''
    return {
        'role': 'user',
        'content': content,
    }
