"""
Tests for SPDX Scanner Git integration.
"""

import pytest
import tempfile
from pathlib import Path
import subprocess
import os

from spdx_scanner.git_integration import GitRepository, GitIntegrationError, create_git_integration


class TestGitRepository:
    """Test Git repository functionality."""

    def test_git_repository_initialization_no_git(self):
        """Test initialization when not in a Git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repo = GitRepository(temp_path)

            assert repo.is_git_repository() is False
            assert repo.get_git_root() is None
            assert repo.get_current_branch() is None

    def test_git_repository_initialization_with_git(self):
        """Test initialization when in a Git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_path, check=True)

            repo = GitRepository(temp_path)

            assert repo.is_git_repository() is True
            assert repo.get_git_root() == temp_path

    def test_get_current_branch(self):
        """Test getting current Git branch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_path, check=True)

            repo = GitRepository(temp_path)

            # Should get default branch (main or master)
            branch = repo.get_current_branch()
            assert branch in ["main", "master", None]  # None if git version doesn't support default branch

            # Create and switch to new branch
            subprocess.run(["git", "checkout", "-b", "test-branch"], cwd=temp_path, check=True, capture_output=True)
            branch = repo.get_current_branch()
            assert branch == "test-branch"

    def test_get_gitignore_patterns_empty(self):
        """Test getting gitignore patterns from empty .gitignore."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)

            repo = GitRepository(temp_path)
            patterns = repo.get_gitignore_patterns()

            assert patterns == []

    def test_get_gitignore_patterns_with_content(self):
        """Test getting gitignore patterns from .gitignore with content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)

            # Create .gitignore file
            gitignore_path = temp_path / ".gitignore"
            gitignore_content = """# Python
__pycache__/
*.pyc
*.pyo

# Node.js
node_modules/
*.log

# Build directories
build/
dist/
"""
            gitignore_path.write_text(gitignore_content)

            repo = GitRepository(temp_path)
            patterns = repo.get_gitignore_patterns()

            expected_patterns = [
                "__pycache__/",
                "*.pyc",
                "*.pyo",
                "node_modules/",
                "*.log",
                "build/",
                "dist/",
            ]

            assert len(patterns) == len(expected_patterns)
            for pattern in expected_patterns:
                assert pattern in patterns

    def test_is_ignored_by_gitignore_simple_patterns(self):
        """Test checking if files are ignored by simple gitignore patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)

            # Create .gitignore file
            gitignore_path = temp_path / ".gitignore"
            gitignore_path.write_text("""*.pyc
__pycache__/
node_modules/
""")

            repo = GitRepository(temp_path)

            # Test ignored files
            assert repo.is_ignored_by_gitignore(temp_path / "test.pyc") is True
            assert repo.is_ignored_by_gitignore(temp_path / "__pycache__" / "file.py") is True
            assert repo.is_ignored_by_gitignore(temp_path / "node_modules" / "package.json") is True

            # Test non-ignored files
            assert repo.is_ignored_by_gitignore(temp_path / "test.py") is False
            assert repo.is_ignored_by_gitignore(temp_path / "README.md") is False

    def test_get_tracked_files_empty_repo(self):
        """Test getting tracked files from empty repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)

            repo = GitRepository(temp_path)
            tracked_files = repo.get_tracked_files()

            assert tracked_files == []

    def test_get_tracked_files_with_files(self):
        """Test getting tracked files from repository with files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_path, check=True)

            # Create and add files
            file1 = temp_path / "file1.py"
            file1.write_text("print('hello')")

            file2 = temp_path / "file2.js"
            file2.write_text("console.log('hello');")

            subprocess.run(["git", "add", "file1.py", "file2.js"], cwd=temp_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_path, check=True, capture_output=True)

            repo = GitRepository(temp_path)
            tracked_files = repo.get_tracked_files()

            assert len(tracked_files) == 2
            assert file1 in tracked_files
            assert file2 in tracked_files

    def test_get_modified_files_no_changes(self):
        """Test getting modified files when no changes exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_path, check=True)

            # Create and commit a file
            file1 = temp_path / "file1.py"
            file1.write_text("print('hello')")
            subprocess.run(["git", "add", "file1.py"], cwd=temp_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_path, check=True, capture_output=True)

            repo = GitRepository(temp_path)
            modified_files = repo.get_modified_files()

            assert modified_files == []

    def test_get_modified_files_with_changes(self):
        """Test getting modified files with changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_path, check=True)

            # Create and commit a file
            file1 = temp_path / "file1.py"
            file1.write_text("print('hello')")
            subprocess.run(["git", "add", "file1.py"], cwd=temp_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_path, check=True, capture_output=True)

            # Modify the file
            file1.write_text("print('modified')")

            # Create new file
            file2 = temp_path / "file2.py"
            file2.write_text("print('new file')")

            repo = GitRepository(temp_path)
            modified_files = repo.get_modified_files(include_untracked=True)

            # Should include modified file and untracked file
            assert file1 in modified_files
            assert file2 in modified_files

    def test_get_file_git_info(self):
        """Test getting Git information for a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_path, check=True)

            # Create and commit a file
            file1 = temp_path / "file1.py"
            file1.write_text("print('hello')")
            subprocess.run(["git", "add", "file1.py"], cwd=temp_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_path, check=True, capture_output=True)

            repo = GitRepository(temp_path)
            info = repo.get_file_git_info(file1)

            assert 'last_commit_hash' in info
            assert 'last_commit_author' in info
            assert 'last_commit_email' in info
            assert 'last_commit_date' in info
            assert info['git_status'] == 'clean'

    def test_install_pre_commit_hook(self):
        """Test installing pre-commit hook."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)

            repo = GitRepository(temp_path)

            # Install pre-commit hook
            success = repo.install_pre_commit_hook()
            assert success is True

            # Verify hook was created
            assert repo.has_pre_commit_hook() is True

            # Check hook content
            content = repo.get_pre_commit_hook_content()
            assert content is not None
            assert "spdx-scanner" in content
            assert "SPDX validation" in content

    def test_install_pre_commit_hook_custom_content(self):
        """Test installing pre-commit hook with custom content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)

            repo = GitRepository(temp_path)

            # Custom hook content
            custom_content = """#!/bin/sh
echo "Custom SPDX hook"
exit 0
"""

            # Install pre-commit hook with custom content
            success = repo.install_pre_commit_hook(custom_content)
            assert success is True

            # Verify hook content
            content = repo.get_pre_commit_hook_content()
            assert content == custom_content

    def test_remove_pre_commit_hook(self):
        """Test removing pre-commit hook."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)

            repo = GitRepository(temp_path)

            # Install and then remove hook
            repo.install_pre_commit_hook()
            assert repo.has_pre_commit_hook() is True

            success = repo.remove_pre_commit_hook()
            assert success is True
            assert repo.has_pre_commit_hook() is False

    def test_is_spdx_hook_installed(self):
        """Test checking if SPDX hook is installed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)

            repo = GitRepository(temp_path)

            # Initially no SPDX hook
            assert repo.is_spdx_hook_installed() is False

            # Install SPDX hook
            repo.install_pre_commit_hook()
            assert repo.is_spdx_hook_installed() is True

            # Install non-SPDX hook
            repo.install_pre_commit_hook("#!/bin/sh\necho 'Not SPDX'\n")
            assert repo.is_spdx_hook_installed() is False

    def test_install_pre_commit_hook_not_in_repo(self):
        """Test installing pre-commit hook when not in Git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            repo = GitRepository(temp_path)

            with pytest.raises(GitIntegrationError, match="Not in a Git repository"):
                repo.install_pre_commit_hook()

    def test_find_git_repository_nested(self):
        """Test finding Git repository from nested directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)

            # Create nested directory
            nested_path = temp_path / "sub" / "nested"
            nested_path.mkdir(parents=True)

            # Change to nested directory and create repository
            original_cwd = os.getcwd()
            try:
                os.chdir(nested_path)
                repo = GitRepository()

                # Should find the Git repository in parent directory
                assert repo.is_git_repository() is True
                assert repo.get_git_root() == temp_path

            finally:
                os.chdir(original_cwd)


class TestCreateGitIntegration:
    """Test creating Git integration instance."""

    def test_create_git_integration_default(self):
        """Test creating Git integration with default path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_path)
                git_integration = create_git_integration()

                assert isinstance(git_integration, GitRepository)
                assert git_integration.is_git_repository() is True

            finally:
                os.chdir(original_cwd)

    def test_create_git_integration_with_path(self):
        """Test creating Git integration with specific path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)

            git_integration = create_git_integration(temp_path)

            assert isinstance(git_integration, GitRepository)
            assert git_integration.is_git_repository() is True
            assert git_integration.repo_path == temp_path