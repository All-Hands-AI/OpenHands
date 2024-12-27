import pytest
from openhands.utils.search_utils import offset_to_page_id, page_id_to_offset


def test_offset_to_page_id():
    # Test with has_next=True
    assert offset_to_page_id(10, True) == "MTA="  # base64 encoding of "10"
    assert offset_to_page_id(0, True) == "MA=="   # base64 encoding of "0"
    assert offset_to_page_id(100, True) == "MTAw"  # base64 encoding of "100"

    # Test with has_next=False should return None
    assert offset_to_page_id(10, False) is None
    assert offset_to_page_id(0, False) is None


def test_page_id_to_offset():
    # Test with valid page_ids
    assert page_id_to_offset("MTA=") == 10   # base64 decoding of "10"
    assert page_id_to_offset("MA==") == 0    # base64 decoding of "0"
    assert page_id_to_offset("MTAw") == 100  # base64 decoding of "100"

    # Test with None should return 0
    assert page_id_to_offset(None) == 0


def test_bidirectional_conversion():
    # Test converting offset to page_id and back
    test_offsets = [0, 1, 10, 100, 1000]
    for offset in test_offsets:
        page_id = offset_to_page_id(offset, True)
        assert page_id_to_offset(page_id) == offset