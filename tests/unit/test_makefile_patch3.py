from openhands.resolver.patching.apply import apply_diff
from openhands.resolver.patching.patch import parse_patch


def test_makefile_parsing():
    """Test that we can correctly parse a Makefile with tabs."""
    # Create a simple Makefile with a tab
    makefile_content = "all:\n\techo hello\n"
    lines = makefile_content.splitlines()
    assert lines == ['all:', '\techo hello']
    
    # Create a patch that adds a new target
    patch_text = """diff --git a/Makefile b/Makefile
index 1234567..89abcdef 100
--- a/Makefile
+++ b/Makefile
@@ -1,2 +1,4 @@
 all:
-	echo hello
+	echo hello
+test:
+	echo test"""

    patch = next(parse_patch(patch_text))
    new_content = apply_diff(patch, makefile_content)
    
    # Verify that tabs are preserved in the output
    expected = [
        'all:',
        '\techo hello',
        'test:',
        '\techo test',
    ]
    assert new_content == expected


def test_makefile_whitespace_normalization():
    """Test that whitespace normalization is disabled for Makefiles."""
    # Create a simple Makefile with a tab
    makefile_content = "all:\n\techo hello\n"
    lines = makefile_content.splitlines()
    assert lines == ['all:', '\techo hello']
    
    # Create a patch that has spaces instead of tabs
    patch_text = """diff --git a/Makefile b/Makefile
index 1234567..89abcdef 100
--- a/Makefile
+++ b/Makefile
@@ -1,2 +1,4 @@
 all:
-    echo hello
+    echo hello
+test:
+    echo test"""

    patch = next(parse_patch(patch_text))
    try:
        new_content = apply_diff(patch, makefile_content)
        assert False, "Expected HunkApplyException due to tab vs space mismatch"
    except Exception as e:
        assert "does not match" in str(e)
