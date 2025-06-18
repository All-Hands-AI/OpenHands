"""Test for ImageContent validation of empty URLs."""

from openhands.core.message import ImageContent


def test_image_content_filters_empty_urls():
    """Test that ImageContent filters out empty URLs during serialization."""

    # Create ImageContent with mixed valid and invalid URLs
    image_content = ImageContent(
        image_urls=[
            'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
            '',  # Empty string
            '   ',  # Whitespace only
            'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA==',
        ]
    )

    # Serialize the content
    serialized = image_content.model_dump()

    # Check that only valid URLs are included (empty and whitespace-only should be filtered out)
    assert len(serialized) == 2, f'Expected 2 valid URLs, got {len(serialized)}'

    for item in serialized:
        assert item['type'] == 'image_url'
        assert 'image_url' in item
        assert 'url' in item['image_url']
        url = item['image_url']['url']
        assert url != '', 'Empty URL should be filtered out'
        assert url.strip() != '', 'Whitespace-only URL should be filtered out'
        assert url.startswith('data:image/'), f'Invalid URL format: {url}'


def test_image_content_all_empty_urls():
    """Test that ImageContent handles the case where all URLs are empty."""

    # Create ImageContent with only empty URLs
    image_content = ImageContent(image_urls=['', '   '])

    # Serialize the content
    serialized = image_content.model_dump()

    # Should result in an empty list
    assert len(serialized) == 0, f'Expected empty list, got {serialized}'


def test_image_content_all_valid_urls():
    """Test that ImageContent preserves all valid URLs."""

    valid_urls = [
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA==',
    ]

    # Create ImageContent with valid URLs
    image_content = ImageContent(image_urls=valid_urls)

    # Serialize the content
    serialized = image_content.model_dump()

    # Should preserve all valid URLs
    assert len(serialized) == len(valid_urls), (
        f'Expected {len(valid_urls)} URLs, got {len(serialized)}'
    )

    for i, item in enumerate(serialized):
        assert item['type'] == 'image_url'
        assert item['image_url']['url'] == valid_urls[i]
