ANALYZE_PROMPT = """Analyze this prompt to see if it requires a detailed plan generation.

Some example scenarios that require generating a step-by-step plan:

1. Structured Rule-Based Tasks with Well-Defined Constraints
    * Example: In a synthetic task, adhering to a sequence like loosening nuts before removing wheels is critical

2. Tasks Requiring Step-by-Step Reasoning to plan a structured chain of actions
	* Example: In a synthetic task, objects must be manipulated in a sequence to achieve a configuration

3. Scenarios with Limited Resources or Strict Constraints
	* Tasks that require resource-sensitive planning, such as minimizing actions or handling tools efficiently
	* Example: In a synthetic task, we need to efficiently coordinate robot actions across rooms and minimize energy consumption costs

4. Generalization in Familiar Symbolic Representations
	* Tasks where the rules remain consistent, and the specific instances change.
	* Example: When we need to adapt strategies to new but structured instances of tasks.

5. Requests Requiring Self-Evaluation
	* Self-evaluation mechanism enables the identification and correction of errors mid-process.
	* Example: When we need to reevaluate actions and adjust plans or actions based on constraints.

In context of software engineering, below are some scenarios where plan generation is required:

1. Dependency and Workflow Management
    * Automating and optimizing CI/CD pipelines, build processes, and package dependency resolution.
	* Example: Resolving complex dependency graphs or sequencing multi-step deployments.
2. Code Refactoring and Debugging
	* Planning systematic changes for refactoring large codebases and isolating root causes during debugging.
	* Example: Refactoring monolithic code into modular components while preserving functionality.
3. Infrastructure and Resource Planning
	* Designing and optimizing Infrastructure as Code (IaC) changes and dynamic resource allocation.
	* Example: Planning cloud resource provisioning while adhering to dependency constraints.
4. High-level Requirements to Low-level Implementation Mapping
    * Translating high-level requirements into detailed implementation steps and ensuring consistency.

=== BEGIN USER MESSAGE ===
{message}
=== END USER MESSAGE ===

Only respond with 0 for no plan generation required or 1 for plan generation required.
"""
