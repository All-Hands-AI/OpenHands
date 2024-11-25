from evaluation.utils.shared import codeact_user_response

INSTRUCTIONS_ADDENDUM = """
####

Use the above instructions to modify the supplied files: {signature_file}
Don't change the names of existing functions or classes, as they may be referenced from other code like unit tests, etc.

Only use standard python libraries, don't suggest installing any packages.
"""


FAKE_RESPONSES = {
    'CodeActAgent': codeact_user_response,
}

INST_SUFFIXES: dict[str, str] = {
    'CodeActAgent': (
        'REMEMBER: All edits must be made directly in the files. Do NOT send'
        ' the edited file as output to the user.\n'
    )
}
