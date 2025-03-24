import os
import unittest
from pathlib import Path


class TestCodeactAgentPrompt(unittest.TestCase):
    """Test that the codeact agent system prompt contains necessary guidance."""

    def test_git_add_all_guidance_in_prompt(self):
        """Test that the system prompt contains guidance about using 'git add .'."""
        # Get the path to the system prompt template
        repo_root = Path(__file__).parent.parent.parent
        system_prompt_path = repo_root / "openhands" / "agenthub" / "codeact_agent" / "prompts" / "system_prompt.j2"
        
        # Ensure the file exists
        self.assertTrue(system_prompt_path.exists(), f"System prompt file not found at {system_prompt_path}")
        
        # Read the file content
        with open(system_prompt_path, "r") as f:
            content = f.read()
        
        # Check if the guidance about using 'git add .' is in the content
        self.assertIn(
            "prefer using `git add .` to stage all modified files", 
            content,
            "System prompt should contain guidance about using 'git add .' to stage all modified files"
        )
        
        # Check if the guidance is in the VERSION_CONTROL section
        version_control_section = content.split("<VERSION_CONTROL>")[1].split("</VERSION_CONTROL>")[0]
        self.assertIn(
            "prefer using `git add .` to stage all modified files", 
            version_control_section,
            "Guidance about using 'git add .' should be in the VERSION_CONTROL section"
        )


if __name__ == "__main__":
    unittest.main()