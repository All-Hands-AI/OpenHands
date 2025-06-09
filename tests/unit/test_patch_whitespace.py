from openhands.resolver.patching.apply import apply_diff
from openhands.resolver.patching.patch import parse_patch


def test_patch_whitespace_mismatch():
    """Test that the patch application succeeds even when whitespace doesn't match."""
    # Original content has a line with spaces
    original_content = """class Example:
    def method(self):
        pass

    def another(self):
        pass"""

    # Patch expects an empty line (no spaces)
    patch_text = """diff --git a/example.py b/example.py
index 1234567..89abcdef 100644
--- a/example.py
+++ b/example.py
@@ -2,6 +2,10 @@ class Example:
     def method(self):
        pass

+    new_field: str = "value"
+
     def another(self):
        pass"""

    patch = next(parse_patch(patch_text))
    # The patch should still work because we normalize whitespace
    new_content = apply_diff(patch, original_content)
    assert new_content == [
        'class Example:',
        '    def method(self):',
        '        pass',
        '',
        '    new_field: str = "value"',
        '',
        '    def another(self):',
        '        pass',
    ]


def test_patch_whitespace_match():
    """Test that the patch application succeeds when whitespace matches."""
    # Original content has an empty line (no spaces)
    original_content = """class Example:
    def method(self):
        pass

    def another(self):
        pass"""

    # Patch expects an empty line (no spaces)
    patch_text = """diff --git a/example.py b/example.py
index 1234567..89abcdef 100644
--- a/example.py
+++ b/example.py
@@ -2,6 +2,10 @@ class Example:
     def method(self):
        pass

+    new_field: str = "value"
+
     def another(self):
        pass"""

    patch = next(parse_patch(patch_text))
    new_content = apply_diff(patch, original_content)
    assert new_content == [
        'class Example:',
        '    def method(self):',
        '        pass',
        '',
        '    new_field: str = "value"',
        '',
        '    def another(self):',
        '        pass',
    ]
