import os
import shutil
import tempfile
from unittest import TestCase

from openhands.resolver.send_pull_request import apply_patch


class TestSendPullRequest(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_apply_patch_with_symlink_deletion(self):
        # Create a test directory structure with a symlink
        source_dir = os.path.join(self.test_dir, "source")
        target_dir = os.path.join(self.test_dir, "target")
        os.makedirs(source_dir)
        os.makedirs(target_dir)

        # Create a symlink
        symlink_path = os.path.join(self.test_dir, "products")
        os.symlink(target_dir, symlink_path)

        # Create a patch that deletes the symlink
        patch = """diff --git a/products b/products
deleted file mode 120000
index b1586c4d4..000000000
--- a/products
+++ /dev/null
@@ -1 +0,0 @@
-target"""

        # Apply the patch
        apply_patch(self.test_dir, patch)

        # Verify the symlink was deleted but target directory still exists
        self.assertFalse(os.path.exists(symlink_path))
        self.assertTrue(os.path.exists(target_dir))

    def test_apply_patch_with_directory_deletion(self):
        # Create a test directory to be deleted
        dir_to_delete = os.path.join(self.test_dir, "dir_to_delete")
        os.makedirs(dir_to_delete)
        with open(os.path.join(dir_to_delete, "test.txt"), "w") as f:
            f.write("test content")

        # Create a patch that deletes the directory
        patch = """diff --git a/dir_to_delete b/dir_to_delete
deleted file mode 755
index 1234567..000000000
--- a/dir_to_delete
+++ /dev/null
@@ -1 +0,0 @@
-test content"""

        # Apply the patch
        apply_patch(self.test_dir, patch)

        # Verify the directory was deleted
        self.assertFalse(os.path.exists(dir_to_delete))

    def test_apply_patch_with_file_deletion(self):
        # Create a test file to be deleted
        file_to_delete = os.path.join(self.test_dir, "file.txt")
        with open(file_to_delete, "w") as f:
            f.write("test content")

        # Create a patch that deletes the file
        patch = """diff --git a/file.txt b/file.txt
deleted file mode 644
index 1234567..000000000
--- a/file.txt
+++ /dev/null
@@ -1 +0,0 @@
-test content"""

        # Apply the patch
        apply_patch(self.test_dir, patch)

        # Verify the file was deleted
        self.assertFalse(os.path.exists(file_to_delete))
