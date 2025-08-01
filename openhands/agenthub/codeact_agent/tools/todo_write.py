from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import TODO_WRITE_TOOL_NAME

_DETAILED_TODO_WRITE_DESCRIPTION = """Use this tool to create and manage a structured task list for your current
coding session. This helps you track progress, organize complex tasks, and
demonstrate thoroughness to the user.
It also helps the user understand the progress of the task and overall
progress of their requests.

## When to Use This Tool
Use this tool proactively in these scenarios:

1. Complex multi-step tasks - When a task requires 3 or more distinct steps
   or actions
2. Non-trivial and complex tasks - Tasks that require careful planning or
   multiple operations
3. User explicitly requests todo list - When the user directly asks you to
   use the todo list
4. User provides multiple tasks - When users provide a list of things to be
   done (numbered or comma-separated)
5. After receiving new instructions - Immediately capture user requirements
   as todos
6. When you start working on a task - Mark it as in_progress BEFORE beginning
   work. Ideally you should only have one todo as in_progress at a time
7. After completing a task - Mark it as completed and add any new follow-up
   tasks discovered during implementation

## When NOT to Use This Tool

Skip using this tool when:
1. There is only a single, straightforward task
2. The task is trivial and tracking it provides no organizational benefit
3. The task can be completed in less than 3 trivial steps
4. The task is purely conversational or informational

NOTE that you should not use this tool if there is only one trivial task to
do. In this case you are better off just doing the task directly.

## Examples of When to Use the Todo List

**Example 1: Multi-step feature implementation**
User: I want to add a dark mode toggle to the application settings. Make sure
you run the tests and build when you're done!
Assistant: I'll help add a dark mode toggle to your application settings. Let
me create a todo list to track this implementation.
*Creates todo list with the following items:*
1. Create dark mode toggle component in Settings page
2. Add dark mode state management (context/store)
3. Implement CSS-in-JS styles for dark theme
4. Update existing components to support theme switching
5. Run tests and build process, addressing any failures or errors that occur
*Begins working on the first task*

**Example 2: Complex refactoring**
User: Help me rename the function getCwd to getCurrentWorkingDirectory across
my project
Assistant: Let me first search through your codebase to find all occurrences
of 'getCwd'.
*Uses grep or search tools to locate all instances of getCwd in the codebase*
Assistant: I've found 15 instances of 'getCwd' across 8 different files. Let
me create a todo list to track these changes.
*Creates todo list with specific items for each file that needs updating*

**Example 3: Multiple features**
User: I need to implement these features for my e-commerce site: user
registration, product catalog, shopping cart, and checkout flow.
Assistant: I'll help implement these features. First, let's add all the
features to the todo list.
*Creates a todo list breaking down each feature into specific tasks based on
the project architecture*

## Examples of When NOT to Use the Todo List

**Example 1: Simple question**
User: How do I print 'Hello World' in Python?
Assistant: In Python, you can print "Hello World" with this simple code:
```python
print("Hello World")
```
*No todo list needed - single, trivial task*

**Example 2: Single straightforward task**
User: Can you add a comment to the calculateTotal function to explain what it
does?
Assistant: Sure, let me add a comment to the calculateTotal function.
*Uses the Edit tool to add a comment*
*No todo list needed - single, straightforward edit*

## Task States and Management

1. **Task States**: Use these states to track progress:
   - pending: Task not yet started
   - in_progress: Currently working on (limit to ONE task at a time)
   - completed: Task finished successfully

2. **Task Management**:
   - Update task status in real-time as you work
   - Mark tasks complete IMMEDIATELY after finishing (don't batch
     completions)
   - Only have ONE task in_progress at any time
   - Complete current tasks before starting new ones
   - Remove tasks that are no longer relevant from the list entirely

3. **Task Completion Requirements**:
   - ONLY mark a task as completed when you have FULLY accomplished it
   - If you encounter errors, blockers, or cannot finish, keep the task as
     in_progress
   - When blocked, create a new task describing what needs to be resolved
   - Never mark a task as completed if:
       - Tests are failing
       - Implementation is partial
       - You encountered unresolved errors
       - You couldn't find necessary files or dependencies

4. **Task Breakdown**:
   - Create specific, actionable items
   - Break complex tasks into smaller, manageable steps
   - Use clear, descriptive task names

When in doubt, use this tool. Being proactive with task management
demonstrates attentiveness and ensures you complete all requirements
successfully.
"""

_SHORT_TODO_WRITE_DESCRIPTION = """Use this tool to create and manage a structured task list for your current
coding session. This helps you track progress, organize complex tasks, and
demonstrate thoroughness to the user.

* Use for complex multi-step tasks (3+ steps) or when user provides multiple tasks
* Mark tasks as pending/in_progress/completed in real-time
* Only have ONE task in_progress at any time
* Mark tasks complete IMMEDIATELY after finishing
* Break complex tasks into smaller, manageable steps
"""


def create_todo_write_tool(
    use_short_description: bool = False,
) -> ChatCompletionToolParam:
    description = (
        _SHORT_TODO_WRITE_DESCRIPTION
        if use_short_description
        else _DETAILED_TODO_WRITE_DESCRIPTION
    )
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=TODO_WRITE_TOOL_NAME,
            description=description,
            parameters={
                'type': 'object',
                'properties': {
                    'todos': {
                        'type': 'array',
                        'description': 'The updated todo list',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'content': {
                                    'type': 'string',
                                    'description': 'The task description',
                                    'minLength': 1,
                                },
                                'status': {
                                    'type': 'string',
                                    'description': 'Current status of the task',
                                    'enum': ['pending', 'in_progress', 'completed'],
                                },
                                'priority': {
                                    'type': 'string',
                                    'description': 'Priority level of the task',
                                    'enum': ['high', 'medium', 'low'],
                                },
                                'id': {
                                    'type': 'string',
                                    'description': 'Unique identifier for the task',
                                },
                            },
                            'required': ['content', 'status', 'priority', 'id'],
                            'additionalProperties': False,
                        },
                    },
                },
                'required': ['todos'],
                'additionalProperties': False,
            },
        ),
    )
