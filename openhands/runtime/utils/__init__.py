from openhands.runtime.utils.system import (
    display_number_matrix,
    find_available_tcp_port,
)

"""
Utils for the client-side runtime.

The fenced diff editing logic, primarily in `edit.py`, is adapted from Aider (Apache 2.0 License).
- Original source: https://github.com/paul-gauthier/aider/blob/main/aider/coders/editblock_fenced_coder.py
- Please see fenced edit at https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/utils/edit.py
"""
__all__ = ['display_number_matrix', 'find_available_tcp_port']
