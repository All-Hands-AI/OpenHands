"""Content creation tool for the Automation Agent."""

from typing import Any, Optional

from litellm import ChatCompletionToolParam

ContentCreationTool: ChatCompletionToolParam = {
    'type': 'function',
    'function': {
        'name': 'create_content',
        'description': """
        Create various types of content including reports, documents, presentations, and more.

        This tool can:
        - Generate comprehensive reports
        - Create structured documents
        - Write articles and blog posts
        - Generate presentations
        - Create technical documentation
        - Write marketing copy
        - Generate code documentation
        - Create data visualizations

        Use this tool when you need to create any form of written or visual content.
        """,
        'parameters': {
            'type': 'object',
            'properties': {
                'content_type': {
                    'type': 'string',
                    'enum': [
                        'report',
                        'document',
                        'presentation',
                        'article',
                        'blog_post',
                        'documentation',
                        'marketing_copy',
                        'email',
                        'proposal',
                        'summary',
                    ],
                    'description': 'Type of content to create',
                },
                'topic': {
                    'type': 'string',
                    'description': 'Main topic or subject of the content',
                },
                'audience': {
                    'type': 'string',
                    'description': 'Target audience for the content',
                },
                'tone': {
                    'type': 'string',
                    'enum': [
                        'professional',
                        'casual',
                        'academic',
                        'technical',
                        'persuasive',
                        'informative',
                        'creative',
                    ],
                    'description': 'Tone and style of the content',
                },
                'length': {
                    'type': 'string',
                    'enum': ['short', 'medium', 'long', 'comprehensive'],
                    'description': 'Desired length of the content',
                },
                'format': {
                    'type': 'string',
                    'enum': ['markdown', 'html', 'pdf', 'docx', 'txt', 'json', 'csv'],
                    'description': 'Output format for the content',
                },
                'sections': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Specific sections to include (optional)',
                },
                'data_sources': {
                    'type': 'array',
                    'items': {'type': 'object'},
                    'description': 'Data sources to incorporate into the content',
                },
                'template': {
                    'type': 'string',
                    'description': 'Template or structure to follow (optional)',
                },
            },
            'required': ['content_type', 'topic'],
        },
    },
}


def execute_content_creation(
    content_type: str,
    topic: str,
    audience: str = 'general',
    tone: str = 'professional',
    length: str = 'medium',
    format: str = 'markdown',
    sections: Optional[list[str]] = None,
    data_sources: Optional[list[dict[str, Any]]] = None,
    template: Optional[str] = None,
) -> dict[str, Any]:
    """
    Execute a content creation task.

    Args:
        content_type: Type of content to create
        topic: Main topic or subject
        audience: Target audience
        tone: Tone and style
        length: Desired length
        format: Output format
        sections: Specific sections to include
        data_sources: Data sources to incorporate
        template: Template to follow

    Returns:
        Dictionary containing the created content
    """
    # This would be implemented to actually create content
    # For now, return a placeholder structure
    return {
        'content_type': content_type,
        'topic': topic,
        'audience': audience,
        'tone': tone,
        'length': length,
        'format': format,
        'content': f'Generated {content_type} about {topic}',
        'word_count': 1000,
        'sections_included': sections or [],
        'data_sources_used': data_sources or [],
        'template_used': template,
        'created_at': '2024-01-01T00:00:00Z',
    }
