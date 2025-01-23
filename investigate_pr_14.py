import os
import logging
import traceback
from openhands.resolver.issue_definitions import PRHandler
from openhands.core.config import LLMConfig

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Modify the PRHandler class to add logging
class DebugPRHandler(PRHandler):
    def __get_pr_status(self, pull_number: int):
        logger.debug(f"Fetching PR status for PR #{pull_number}")
        try:
            result = super().__get_pr_status(pull_number)
            logger.debug(f"PR status result: {result}")
            
            # Print detailed information about the API response
            print(f"Detailed PR status for PR #{pull_number}:")
            print(f"Mergeable status: {result[0]}")
            print("Failed checks:")
            for check in result[1]:
                print(f"  Name: {check['name']}")
                print(f"  Description: {check['description']}")
                print("  ---")
            
            return result
        except Exception as e:
            logger.error(f"Error in __get_pr_status: {str(e)}")
            logger.debug(traceback.format_exc())
            raise

    def get_instruction(self, issue, prompt_template, repo_instruction=None):
        logger.debug(f"Generating instruction for PR #{issue.number}")
        logger.debug(f"Prompt template: {prompt_template}")
        logger.debug(f"Issue data: {issue}")
        try:
            result = super().get_instruction(issue, prompt_template, repo_instruction)
            logger.debug(f"Generated instruction: {result[0]}")
            return result
        except Exception as e:
            logger.error(f"Error in get_instruction: {str(e)}")
            logger.debug(traceback.format_exc())
            raise

    def get_converted_issues(self, issue_numbers=None, comment_id=None):
        logger.debug(f"Getting converted issues: {issue_numbers}")
        try:
            result = super().get_converted_issues(issue_numbers, comment_id)
            logger.debug(f"Converted issues: {result}")
            
            # Print detailed information about each converted issue
            for issue in result:
                print(f"\nDetailed information for PR #{issue.number}:")
                print(f"Title: {issue.title}")
                print(f"Merge conflicts: {issue.has_merge_conflicts}")
                print("Failed checks:")
                if issue.failed_checks:
                    for check in issue.failed_checks:
                        print(f"  Name: {check['name']}")
                        print(f"  Description: {check['description']}")
                        print("  ---")
                else:
                    print("  No failed checks")
            
            return result
        except Exception as e:
            logger.error(f"Error in get_converted_issues: {str(e)}")
            logger.debug(traceback.format_exc())
            raise

def main():
    try:
        print("Starting main function")
        # GitHub token
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")
        print("GitHub token retrieved")

        # Create PRHandler instance
        llm_config = LLMConfig(model='gpt-3.5-turbo')  # Adjust as needed
        pr_handler = DebugPRHandler('neubig', 'pr-viewer', github_token, llm_config)
        print("PRHandler instance created")

        # Call __get_pr_status directly
        print("Calling __get_pr_status for PR #14")
        has_conflicts, failed_checks = pr_handler._PRHandler__get_pr_status(14)
        print(f"PR #14 status: has_conflicts={has_conflicts}, failed_checks={failed_checks}")

        # Fetch PR #14
        print("Fetching PR #14")
        issues = pr_handler.get_converted_issues([14])
        if not issues:
            logger.error("Failed to fetch PR #14")
            return
        print(f"Fetched {len(issues)} issues")

        pr = issues[0]
        print(f"PR data: {pr}")

        # Generate instruction
        prompt_template = """
        {{ pr_status }}

        {{ body }}

        {% if review_comments %}
        Review Comments:
        {{ review_comments }}
        {% endif %}

        {% if review_threads %}
        Review Threads:
        {{ review_threads }}
        {% endif %}

        {% if files %}
        Files:
        {{ files }}
        {% endif %}

        {% if thread_context %}
        Thread Context:
        {{ thread_context }}
        {% endif %}

        {% if repo_instruction %}
        Repository Instruction:
        {{ repo_instruction }}
        {% endif %}
        """

        print("Generating instruction")
        instruction, _ = pr_handler.get_instruction(pr, prompt_template)
        print("Instruction generated")
        print(f"Final instruction:\n{instruction}")

    except Exception as e:
        print(f"An error occurred in main: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred in main: {str(e)}")
        print(traceback.format_exc())