"""Tests for microagent integration in resolver workflow."""
import tempfile
from unittest import mock

import pytest

from openhands.microagent.microagent import BaseMicroAgent
from openhands.resolver.interfaces.github import GithubIssueHandler
from openhands.resolver.interfaces.issue import Issue, ReviewThread


def test_resolver_uses_knowledge_microagents():
    """Test that resolver picks up relevant knowledge microagents based on triggers."""
    # Create a test resolver
    resolver = GithubIssueHandler(
        owner="test",
        repo="test",
        token="test-token"
    )
    
    # Create a test knowledge microagent
    test_knowledge_content = """---
name: flarglebargle
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- flarglebargle
- bargling
---
When discussing flarglebargle, remember:
- It's a critical component for widget optimization
- Always check the flargle settings before bargling
- Never bargle without proper flargle protection
"""
    
    # Create a temporary microagent file
    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(test_knowledge_content.encode())
        f.flush()
        
        # Load the microagent using the proper system
        agent = BaseMicroAgent.load(f.name)
        
        # Mock the microagents registry
        with mock.patch('openhands.agenthub.micro.registry.all_microagents', 
                       {agent.name: agent}):
            
            # Create a test issue that should trigger the microagent
            issue = Issue(
                owner="test",
                repo="test",
                number=1,
                title="Problem with flarglebargle settings",
                body="The flarglebargle optimization isn't working correctly"
            )
            
            # Get context from resolver
            contexts = resolver.get_context_from_external_issues_references(
                closing_issues=[],
                closing_issue_numbers=[],
                issue_body=issue.body,
                review_comments=None,
                review_threads=[],
                thread_comments=None
            )
            
            # Verify the knowledge was included when trigger matched
            assert any("flargle settings before bargling" in ctx for ctx in contexts)
            
            # Test with an issue that doesn't match any triggers
            unrelated_issue = Issue(
                owner="test",
                repo="test",
                number=2,
                title="Some other issue",
                body="Nothing about that topic here"
            )
            
            # Get context for unrelated issue
            unrelated_contexts = resolver.get_context_from_external_issues_references(
                closing_issues=[],
                closing_issue_numbers=[],
                issue_body=unrelated_issue.body,
                review_comments=None,
                review_threads=[],
                thread_comments=None
            )
            
            # Verify the knowledge was NOT included when no trigger matched
            assert not any("flargle settings before bargling" in ctx for ctx in unrelated_contexts)


def test_resolver_uses_knowledge_microagents_with_comments():
    """Test that resolver checks triggers in comments and review threads."""
    # Create a test resolver
    resolver = GithubIssueHandler(
        owner="test",
        repo="test",
        token="test-token"
    )
    
    test_knowledge_content = """---
name: performance
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- performance
- optimization
---
When reviewing performance-related changes:
- Profile before optimizing
- Consider algorithmic complexity
- Document performance implications
"""
    
    with tempfile.NamedTemporaryFile(suffix='.md') as f:
        f.write(test_knowledge_content.encode())
        f.flush()
        agent = BaseMicroAgent.load(f.name)
        
        with mock.patch('openhands.agenthub.micro.registry.all_microagents',
                       {agent.name: agent}):
            
            # Create issue with performance discussion in comments
            issue = Issue(
                owner="test",
                repo="test",
                number=1,
                title="Update widget implementation",
                body="Updated the widget implementation"
            )
            
            review_comments = [
                "We should check the performance impact of this change",
                "Good point about optimization"
            ]
            
            review_threads = [
                ReviewThread(
                    comment="This might affect performance",
                    files=["widget.py"]
                )
            ]
            
            # Get context with comments
            contexts = resolver.get_context_from_external_issues_references(
                closing_issues=[],
                closing_issue_numbers=[],
                issue_body=issue.body,
                review_comments=review_comments,
                review_threads=review_threads,
                thread_comments=None
            )
            
            # Verify performance knowledge was included due to comments
            assert any("Profile before optimizing" in ctx for ctx in contexts)