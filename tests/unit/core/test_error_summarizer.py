import unittest

from litellm.exceptions import (  # type: ignore[import-untyped]
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadRequestError,
    ContentPolicyViolationError,
    ContextWindowExceededError,
    InternalServerError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
)

from openhands.core.exceptions import (
    AgentStuckInLoopError,
    FunctionCallNotExistsError,
    FunctionCallValidationError,
    LLMContextWindowExceedError,
    LLMMalformedActionError,
    LLMNoActionError,
    LLMResponseError,
)
from openhands.core.error_summarizer import summarize_error


class TestErrorSummarizer(unittest.TestCase):
    def test_litellm_exceptions(self):
        self.assertEqual(
            summarize_error(AuthenticationError("Invalid API Key")),
            "There's an issue with your LLM API key. Please check if it's correct and has enough credits."
        )
        self.assertEqual(
            summarize_error(RateLimitError("Rate limit exceeded")),
            "The LLM API is rate limiting requests. Please wait a moment and try again. If the problem persists, check your API plan limits."
        )
        self.assertEqual(
            summarize_error(ServiceUnavailableError("Service unavailable")),
            "The LLM API service is currently unavailable. Please try again later."
        )
        self.assertEqual(
            summarize_error(APIConnectionError("Could not connect")),
            "Could not connect to the LLM API. Please check your internet connection and API endpoint."
        )
        self.assertEqual(
            summarize_error(Timeout("Request timed out")),
            "The request to the LLM API timed out. Please try again."
        )
        self.assertEqual(
            summarize_error(ContextWindowExceededError("Context window exceeded")),
            "The conversation history is too long for the LLM to process. The agent will attempt to condense the history. If this error persists, you may need to start a new task or use a model with a larger context window."
        )
        self.assertEqual(
            summarize_error(LLMContextWindowExceedError("Context window exceeded via LLM")),
            "The conversation history is too long for the LLM to process. The agent will attempt to condense the history. If this error persists, you may need to start a new task or use a model with a larger context window."
        )
        self.assertEqual(
            summarize_error(BadRequestError("ExceededBudget: Your request would exceed the budget.")),
            "The LLM operation could not be completed because it would exceed the allocated budget for this task."
        )
        self.assertEqual(
            summarize_error(BadRequestError("ContentPolicyViolationError: Harmful content detected.")),
            "The request to the LLM was blocked due to a content policy violation. Please modify your request or task."
        )
        self.assertEqual(
            summarize_error(BadRequestError("Generic bad request")),
            "The LLM API received a bad request. Details: Generic bad request"
        )
        self.assertEqual(
            summarize_error(NotFoundError("Endpoint not found")),
            "The LLM API endpoint was not found. Please check the API configuration. Details: Endpoint not found"
        )
        self.assertEqual(
            summarize_error(InternalServerError("Internal server error")),
            "The LLM API encountered an internal server error. Please try again later. Details: Internal server error"
        )
        self.assertEqual(
            summarize_error(ContentPolicyViolationError("Violated content policy")),
            "The request to the LLM was blocked due to a contentPolicyViolation. Please modify your request or task."
        )
        self.assertEqual(
            summarize_error(APIError("Generic API Error")),
            "An LLM API error occurred: Generic API Error"
        )

    def test_openhands_core_llm_exceptions(self):
        self.assertEqual(
            summarize_error(LLMMalformedActionError("Malformed action")),
            "The LLM tried to perform an action but the format was incorrect. Details: Malformed action"
        )
        self.assertEqual(
            summarize_error(LLMNoActionError("No action specified")),
            "The LLM did not specify an action to perform. It might need more context or a clearer instruction."
        )
        self.assertEqual(
            summarize_error(LLMResponseError("Unexpected LLM response")),
            "The LLM's response was not as expected. Details: Unexpected LLM response"
        )
        self.assertEqual(
            summarize_error(FunctionCallNotExistsError("Tool `do_magic` not found")),
            "The LLM tried to use a tool or function that doesn't exist: Tool `do_magic` not found"
        )
        self.assertEqual(
            summarize_error(FunctionCallValidationError("Invalid params for `do_stuff`")),
            "The LLM tried to use a tool or function with invalid parameters: Invalid params for `do_stuff`"
        )

    def test_openhands_agent_exceptions(self):
        self.assertEqual(
            summarize_error(AgentStuckInLoopError("Agent is stuck")),
            "The agent appears to be stuck in a loop and cannot make progress. You might need to modify the task or provide more specific instructions."
        )

    def test_generic_python_exceptions(self):
        self.assertEqual(
            summarize_error(FileNotFoundError("No such file or directory: /test.txt")),
            "File not found: '/test.txt'. Please ensure the file exists at the correct location."
        )
        self.assertEqual(
            summarize_error(FileNotFoundError("No such file or directory"), {'file_path': '/explicit/path.txt'}),
            "File not found: '/explicit/path.txt'. Please ensure the file exists at the correct location."
        )
        self.assertEqual(
            summarize_error(PermissionError("Operation not permitted")),
            "Permission denied. The agent does not have the necessary permissions to perform an operation. Details: Operation not permitted"
        )
        self.assertEqual(
            summarize_error(ConnectionError("Failed to establish a new connection")),
            "A network connection error occurred. Please check your internet connection. Details: Failed to establish a new connection"
        )
        self.assertEqual(
            summarize_error(ValueError("Invalid value provided")),
            "A value error occurred: Invalid value provided."
        )
        self.assertEqual(
            summarize_error(TypeError("Incorrect type for argument")),
            "A type error occurred: Incorrect type for argument."
        )
        self.assertEqual(
            summarize_error(KeyError("my_key")),
            "Missing key: 'my_key'. A required piece of data was not found."
        )
        self.assertEqual(
            summarize_error(KeyError("random_key"), {'key': 'explicit_key'}),
            "Missing key: 'explicit_key'. A required piece of data was not found."
        )
        self.assertEqual(
            summarize_error(AttributeError("object has no attribute `foo`")),
            "Attribute error: object has no attribute `foo`. This might indicate an issue with the agent's internal state or code."
        )
        self.assertEqual(
            summarize_error(NotImplementedError("This is not implemented")),
            "This feature or action is not yet implemented."
        )

    def test_default_summary(self):
        self.assertEqual(
            summarize_error(RuntimeError("A generic runtime error")),
            "An unexpected error occurred: RuntimeError - A generic runtime error. Please check the logs for more details."
        )
        self.assertEqual(
            summarize_error("This is a string error message"),
            "An unexpected error occurred: str - This is a string error message. Please check the logs for more details."
        )

    def test_context_usage(self):
        # Example where context is used by a specific handler (e.g., FileNotFoundError)
        self.assertEqual(
            summarize_error(FileNotFoundError("msg"), {'file_path': 'specific_file.txt'}),
            "File not found: 'specific_file.txt'. Please ensure the file exists at the correct location."
        )
        # Example where context is not directly used by a specific handler, but passed along (not explicitly tested here)
        # The default handler doesn't use context, but specific future handlers might.
        self.assertEqual(
            summarize_error(RuntimeError("Command failed"), {'command': 'test_cmd --arg'}),
            "An unexpected error occurred: RuntimeError - Command failed. Please check the logs for more details."
        )

if __name__ == '__main__':
    unittest.main()
