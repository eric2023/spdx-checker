"""
Git integration for SPDX Scanner.

This module provides functionality to integrate with Git repositories,
including pre-commit hooks, .gitignore respect, and Git-aware scanning.
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Set, Iterator
import os


logger = logging.getLogger(__name__)


class GitIntegrationError(Exception):
    """Exception raised for Git integration errors."""
    pass


class GitRepository:
    """Represents a Git repository and provides Git-related functionality."""

    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize Git repository integration."""
        self.repo_path = repo_path or Path.cwd()
        self.git_dir = None
        self._gitignore_patterns = None
        self._gitignore_path = None

        # Find Git repository root
        self._find_git_repository()

    def _find_git_repository(self) -> None:
        """Find the Git repository root."""
        current_path = self.repo_path.resolve()

        while current_path != current_path.parent:
            git_dir = current_path / ".git"
            if git_dir.exists() and git_dir.is_dir():
                self.git_dir = git_dir
                self.repo_path = current_path
                self._gitignore_path = current_path / ".gitignore"
                logger.info(f"Found Git repository at: {current_path}")
                return

            current_path = current_path.parent

        # No Git repository found
        self.git_dir = None
        logger.debug("No Git repository found")

    def is_git_repository(self) -> bool:
        """Check if the current directory is a Git repository."""
        return self.git_dir is not None

    def get_git_root(self) -> Optional[Path]:
        """Get the Git repository root path."""
        return self.repo_path if self.is_git_repository() else None

    def get_current_branch(self) -> Optional[str]:
        """Get the current Git branch name."""
        if not self.is_git_repository():
            return None

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Failed to get current Git branch")
            return None

    def get_gitignore_patterns(self) -> List[str]:
        """Get patterns from .gitignore file."""
        if not self.is_git_repository() or not self._gitignore_path or not self._gitignore_path.exists():
            return []

        if self._gitignore_patterns is not None:
            return self._gitignore_patterns

        patterns = []
        try:
            with open(self._gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except (IOError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to read .gitignore: {e}")

        self._gitignore_patterns = patterns
        return patterns

    def is_ignored_by_gitignore(self, file_path: Path) -> bool:
        """Check if a file is ignored by .gitignore patterns."""
        if not self.is_git_repository():
            return False

        patterns = self.get_gitignore_patterns()
        if not patterns:
            return False

        try:
            # Convert to relative path from repo root
            if file_path.is_absolute():
                try:
                    relative_path = file_path.relative_to(self.repo_path)
                except ValueError:
                    # File is outside repository
                    return False
            else:
                relative_path = file_path

            relative_str = str(relative_path)

            # Use git check-ignore if available
            try:
                result = subprocess.run(
                    ["git", "check-ignore", relative_str],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=False  # Don't raise on non-zero exit
                )
                # git check-ignore exits with 0 if file is ignored
                return result.returncode == 0
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to pattern matching
                return self._match_gitignore_patterns(relative_str, patterns)

        except Exception as e:
            logger.warning(f"Error checking gitignore for {file_path}: {e}")
            return False

    def _match_gitignore_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Match file path against gitignore patterns (simplified implementation)."""
        import fnmatch

        for pattern in patterns:
            try:
                # Handle directory patterns
                if pattern.endswith('/'):
                    if file_path.startswith(pattern.rstrip('/')):
                        return True
                # Handle negation patterns
                elif pattern.startswith('!'):
                    negated_pattern = pattern[1:]
                    if fnmatch.fnmatch(file_path, negated_pattern):
                        return False
                # Handle regular patterns
                else:
                    if fnmatch.fnmatch(file_path, pattern):
                        return True
                    # Also check if pattern matches any parent directory
                    path_parts = file_path.split('/')
                    for i in range(len(path_parts)):
                        partial_path = '/'.join(path_parts[:i+1])
                        if fnmatch.fnmatch(partial_path, pattern):
                            return True
            except Exception as e:
                logger.warning(f"Error matching pattern '{pattern}': {e}")

        return False

    def get_tracked_files(self) -> List[Path]:
        """Get list of files tracked by Git."""
        if not self.is_git_repository():
            return []

        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            tracked_files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    file_path = self.repo_path / line
                    if file_path.exists():
                        tracked_files.append(file_path)

            return tracked_files

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to get tracked files: {e}")
            return []

    def get_modified_files(self, include_untracked: bool = False) -> List[Path]:
        """Get list of modified files."""
        if not self.is_git_repository():
            return []

        try:
            # Get modified files
            cmd = ["git", "diff", "--name-only"]
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            modified_files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    file_path = self.repo_path / line
                    if file_path.exists():
                        modified_files.append(file_path)

            # Get staged files
            cmd = ["git", "diff", "--cached", "--name-only"]
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            for line in result.stdout.strip().split('\n'):
                if line:
                    file_path = self.repo_path / line
                    if file_path.exists() and file_path not in modified_files:
                        modified_files.append(file_path)

            # Get untracked files if requested
            if include_untracked:
                cmd = ["git", "ls-files", "--others", "--exclude-standard"]
                result = subprocess.run(
                    cmd,
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )

                for line in result.stdout.strip().split('\n'):
                    if line:
                        file_path = self.repo_path / line
                        if file_path.exists() and file_path not in modified_files:
                            modified_files.append(file_path)

            return modified_files

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to get modified files: {e}")
            return []

    def get_file_git_info(self, file_path: Path) -> dict:
        """Get Git information for a specific file."""
        if not self.is_git_repository():
            return {}

        info = {}

        try:
            # Get last commit info
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%an|%ae|%ad", "--", str(file_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False  # Don't fail if file has no commits
            )

            if result.returncode == 0 and result.stdout.strip():
                commit_hash, author_name, author_email, commit_date = result.stdout.strip().split('|')
                info.update({
                    'last_commit_hash': commit_hash,
                    'last_commit_author': author_name,
                    'last_commit_email': author_email,
                    'last_commit_date': commit_date,
                })

            # Get file status
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", str(file_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout.strip():
                status_line = result.stdout.strip()
                status_code = status_line[:2]
                info['git_status'] = self._interpret_git_status(status_code)
            else:
                info['git_status'] = 'clean'

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to get Git info for {file_path}: {e}")

        return info

    def _interpret_git_status(self, status_code: str) -> str:
        """Interpret Git status code."""
        status_map = {
            '??': 'untracked',
            'M ': 'modified',
            ' M': 'modified_in_index',
            'MM': 'modified_in_both',
            'A ': 'added',
            ' D': 'deleted_in_index',
            'D ': 'deleted',
            'DD': 'deleted_in_both',
            'R ': 'renamed',
            'C ': 'copied',
            'U ': 'updated_but_unmerged',
        }
        return status_map.get(status_code, 'unknown')

    def install_pre_commit_hook(self, hook_content: Optional[str] = None) -> bool:
        """Install pre-commit hook for SPDX validation."""
        if not self.is_git_repository():
            raise GitIntegrationError("Not in a Git repository")

        hooks_dir = self.git_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        pre_commit_hook = hooks_dir / "pre-commit"

        if hook_content is None:
            hook_content = self._get_default_pre_commit_hook()

        try:
            with open(pre_commit_hook, 'w', encoding='utf-8') as f:
                f.write(hook_content)

            # Make hook executable
            os.chmod(pre_commit_hook, 0o755)

            logger.info(f"Installed pre-commit hook: {pre_commit_hook}")
            return True

        except (IOError, OSError) as e:
            raise GitIntegrationError(f"Failed to install pre-commit hook: {e}")

    def _get_default_pre_commit_hook(self) -> str:
        """Get default pre-commit hook content."""
        return """#!/bin/sh
# SPDX Scanner pre-commit hook
# This hook validates SPDX license declarations before commits

# Check if spdx-scanner is available
if ! command -v spdx-scanner >/dev/null 2>&1; then
    echo "Warning: spdx-scanner not found in PATH. Skipping SPDX validation."
    echo "Install spdx-scanner with: pip install spdx-scanner"
    exit 0
fi

# Get list of staged files
staged_files=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$staged_files" ]; then
    exit 0
fi

echo "Validating SPDX license declarations..."

# Validate each staged file
validation_failed=0
for file in $staged_files; do
    # Only validate source code files (add more extensions as needed)
    case "$file" in
        *.py|*.js|*.ts|*.java|*.c|*.cpp|*.h|*.hpp|*.go|*.rs|*.rb|*.php|*.swift|*.kt|*.scala|*.m|*.mm|*.pl|*.lua|*.dart|*.vue|*.svelte|*.sh|*.bash|*.zsh|*.fish|*.html|*.htm|*.css|*.scss|*.sass|*.less|*.json|*.yaml|*.yml|*.toml|*.xml)
            echo "Validating: $file"
            if ! spdx-scanner validate --quiet "$file" 2>/dev/null; then
                echo "SPDX validation failed for: $file"
                validation_failed=1
            fi
            ;;
    esac
done

if [ $validation_failed -ne 0 ]; then
    echo ""
    echo "SPDX validation failed for some files."
    echo "Please fix the SPDX license declarations before committing."
    echo "You can use 'spdx-scanner correct' to automatically fix issues."
    exit 1
fi

echo "SPDX validation completed successfully."
exit 0
"""

    def remove_pre_commit_hook(self) -> bool:
        """Remove pre-commit hook."""
        if not self.is_git_repository():
            return False

        pre_commit_hook = self.git_dir / "hooks" / "pre-commit"

        if pre_commit_hook.exists():
            try:
                pre_commit_hook.unlink()
                logger.info(f"Removed pre-commit hook: {pre_commit_hook}")
                return True
            except OSError as e:
                logger.warning(f"Failed to remove pre-commit hook: {e}")

        return False

    def has_pre_commit_hook(self) -> bool:
        """Check if pre-commit hook exists."""
        if not self.is_git_repository():
            return False

        pre_commit_hook = self.git_dir / "hooks" / "pre-commit"
        return pre_commit_hook.exists()

    def get_pre_commit_hook_content(self) -> Optional[str]:
        """Get current pre-commit hook content."""
        if not self.has_pre_commit_hook():
            return None

        pre_commit_hook = self.git_dir / "hooks" / "pre-commit"

        try:
            with open(pre_commit_hook, 'r', encoding='utf-8') as f:
                return f.read()
        except (IOError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to read pre-commit hook: {e}")
            return None

    def is_spdx_hook_installed(self) -> bool:
        """Check if SPDX scanner pre-commit hook is installed."""
        content = self.get_pre_commit_hook_content()
        if content is None:
            return False

        return "spdx-scanner" in content and "SPDX validation" in content


def create_git_integration(repo_path: Optional[Path] = None) -> GitRepository:
    """Create Git integration instance."""
    return GitRepository(repo_path)