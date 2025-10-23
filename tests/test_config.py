"""
Tests for SPDX Scanner configuration management.
"""

import pytest
import tempfile
import json
import toml
from pathlib import Path

from spdx_scanner.config import (
    Configuration,
    ValidationRules,
    CorrectionSettings,
    ScannerSettings,
    OutputSettings,
    GitSettings,
    TemplateSettings,
    ConfigManager,
    create_default_config_manager,
)


class TestValidationRules:
    """Test validation rules configuration."""

    def test_default_validation_rules(self):
        """Test default validation rules."""
        rules = ValidationRules()

        assert rules.require_license_identifier is True
        assert rules.require_copyright is True
        assert rules.require_project_attribution is False
        assert rules.allow_unknown_licenses is False
        assert rules.require_osi_approved is False
        assert rules.require_spdx_version is False
        assert rules.min_copyright_year == 1970
        assert rules.max_copyright_year == 2030
        assert rules.copyright_format == "standard"
        assert rules.license_format == "strict"

    def test_custom_validation_rules(self):
        """Test custom validation rules."""
        rules = ValidationRules(
            require_license_identifier=False,
            require_copyright=False,
            allow_unknown_licenses=True,
            min_copyright_year=2000,
            max_copyright_year=2025,
        )

        assert rules.require_license_identifier is False
        assert rules.require_copyright is False
        assert rules.allow_unknown_licenses is True
        assert rules.min_copyright_year == 2000
        assert rules.max_copyright_year == 2025


class TestCorrectionSettings:
    """Test correction settings configuration."""

    def test_default_correction_settings(self):
        """Test default correction settings."""
        settings = CorrectionSettings()

        assert settings.create_backups is True
        assert settings.backup_suffix == ".spdx-backup"
        assert settings.preserve_existing is True
        assert settings.default_license == "MIT"
        assert settings.default_copyright_holder == "Unknown"
        assert settings.default_project_name == "Unknown Project"
        assert settings.dry_run is False

    def test_custom_correction_settings(self):
        """Test custom correction settings."""
        settings = CorrectionSettings(
            create_backups=False,
            backup_suffix=".backup",
            default_license="Apache-2.0",
            default_copyright_holder="Test Corp",
            dry_run=True,
        )

        assert settings.create_backups is False
        assert settings.backup_suffix == ".backup"
        assert settings.default_license == "Apache-2.0"
        assert settings.default_copyright_holder == "Test Corp"
        assert settings.dry_run is True


class TestScannerSettings:
    """Test scanner settings configuration."""

    def test_default_scanner_settings(self):
        """Test default scanner settings."""
        settings = ScannerSettings()

        assert settings.follow_symlinks is False
        assert settings.max_file_size == 10 * 1024 * 1024  # 10MB
        assert len(settings.include_patterns) > 0
        assert len(settings.exclude_patterns) > 0
        assert "**/*.py" in settings.include_patterns
        assert "**/node_modules/**" in settings.exclude_patterns

    def test_custom_scanner_settings(self):
        """Test custom scanner settings."""
        settings = ScannerSettings(
            follow_symlinks=True,
            max_file_size=5 * 1024 * 1024,  # 5MB
            include_patterns=["**/*.py", "**/*.js"],
            exclude_patterns=["**/test_*"],
        )

        assert settings.follow_symlinks is True
        assert settings.max_file_size == 5 * 1024 * 1024
        assert settings.include_patterns == ["**/*.py", "**/*.js"]
        assert settings.exclude_patterns == ["**/test_*"]


class TestOutputSettings:
    """Test output settings configuration."""

    def test_default_output_settings(self):
        """Test default output settings."""
        settings = OutputSettings()

        assert settings.format == "text"
        assert settings.output_file is None
        assert settings.verbose is False
        assert settings.quiet is False
        assert settings.show_progress is True
        assert settings.include_summary is True
        assert settings.include_details is True

    def test_custom_output_settings(self):
        """Test custom output settings."""
        settings = OutputSettings(
            format="json",
            output_file="report.json",
            verbose=True,
            quiet=True,
            show_progress=False,
        )

        assert settings.format == "json"
        assert settings.output_file == "report.json"
        assert settings.verbose is True
        assert settings.quiet is True
        assert settings.show_progress is False


class TestGitSettings:
    """Test Git settings configuration."""

    def test_default_git_settings(self):
        """Test default Git settings."""
        settings = GitSettings()

        assert settings.enabled is True
        assert settings.respect_gitignore is True
        assert settings.use_git_timestamps is True
        assert settings.check_uncommitted is False
        assert settings.check_untracked is False

    def test_custom_git_settings(self):
        """Test custom Git settings."""
        settings = GitSettings(
            enabled=False,
            respect_gitignore=False,
            check_uncommitted=True,
            check_untracked=True,
        )

        assert settings.enabled is False
        assert settings.respect_gitignore is False
        assert settings.check_uncommitted is True
        assert settings.check_untracked is True


class TestTemplateSettings:
    """Test template settings configuration."""

    def test_default_template_settings(self):
        """Test default template settings."""
        settings = TemplateSettings()

        assert settings.templates == {}
        assert settings.use_custom_templates is False
        assert settings.template_directory is None

    def test_custom_template_settings(self):
        """Test custom template settings."""
        templates = {
            "python": "# Custom Python Template\n",
            "javascript": "// Custom JavaScript Template\n",
        }
        settings = TemplateSettings(
            templates=templates,
            use_custom_templates=True,
            template_directory="/path/to/templates",
        )

        assert settings.templates == templates
        assert settings.use_custom_templates is True
        assert settings.template_directory == "/path/to/templates"


class TestConfiguration:
    """Test main configuration class."""

    def test_default_configuration(self):
        """Test default configuration."""
        config = Configuration()

        assert config.project_name == "Unknown Project"
        assert config.project_version == "1.0.0"
        assert config.copyright_holder == "Unknown"
        assert config.default_license == "MIT"
        assert isinstance(config.validation_rules, ValidationRules)
        assert isinstance(config.correction_settings, CorrectionSettings)
        assert isinstance(config.scanner_settings, ScannerSettings)
        assert isinstance(config.output_settings, OutputSettings)
        assert isinstance(config.git_settings, GitSettings)
        assert isinstance(config.template_settings, TemplateSettings)

    def test_configuration_from_dict(self):
        """Test creating configuration from dictionary."""
        data = {
            "project_name": "Test Project",
            "copyright_holder": "Test Corp",
            "default_license": "Apache-2.0",
            "validation_rules": {
                "require_license_identifier": False,
                "min_copyright_year": 2000,
            },
            "correction_settings": {
                "create_backups": False,
                "dry_run": True,
            },
        }

        config = Configuration.from_dict(data)

        assert config.project_name == "Test Project"
        assert config.copyright_holder == "Test Corp"
        assert config.default_license == "Apache-2.0"
        assert config.validation_rules.require_license_identifier is False
        assert config.validation_rules.min_copyright_year == 2000
        assert config.correction_settings.create_backups is False
        assert config.correction_settings.dry_run is True

    def test_configuration_to_dict(self):
        """Test converting configuration to dictionary."""
        config = Configuration(
            project_name="Test Project",
            copyright_holder="Test Corp",
        )

        data = config.to_dict()

        assert data["project_name"] == "Test Project"
        assert data["copyright_holder"] == "Test Corp"
        assert data["default_license"] == "MIT"
        assert data["validation_rules"]["require_license_identifier"] is True

    def test_configuration_validation_valid(self):
        """Test configuration validation with valid settings."""
        config = Configuration(
            project_name="Test Project",
            copyright_holder="Test Corp",
            default_license="MIT",
        )

        errors = config.validate()
        assert len(errors) == 0

    def test_configuration_validation_empty_project_name(self):
        """Test configuration validation with empty project name."""
        config = Configuration(project_name="")

        errors = config.validate()
        assert len(errors) >= 1
        assert any("project_name cannot be empty" in error for error in errors)

    def test_configuration_validation_empty_copyright_holder(self):
        """Test configuration validation with empty copyright holder."""
        config = Configuration(copyright_holder="")

        errors = config.validate()
        assert len(errors) >= 1
        assert any("copyright_holder cannot be empty" in error for error in errors)

    def test_configuration_validation_invalid_license(self):
        """Test configuration validation with invalid license."""
        config = Configuration(default_license="INVALID LICENSE WITH SPACES")

        errors = config.validate()
        assert len(errors) >= 1
        assert any("default_license" in error and "not a valid SPDX license identifier" in error for error in errors)

    def test_configuration_validation_invalid_years(self):
        """Test configuration validation with invalid copyright years."""
        config = Configuration()
        config.validation_rules.min_copyright_year = 2025
        config.validation_rules.max_copyright_year = 2020

        errors = config.validate()
        assert len(errors) >= 1
        assert any("min_copyright_year must be less than max_copyright_year" in error for error in errors)

    def test_configuration_validation_invalid_output_format(self):
        """Test configuration validation with invalid output format."""
        config = Configuration()
        config.output_settings.format = "invalid_format"

        errors = config.validate()
        assert len(errors) >= 1
        assert any("output format must be one of" in error for error in errors)


class TestConfigManager:
    """Test configuration manager."""

    def test_config_manager_initialization(self):
        """Test configuration manager initialization."""
        manager = ConfigManager()
        assert manager.config_path is None
        assert isinstance(manager.config, Configuration)

    def test_config_manager_with_path(self):
        """Test configuration manager with path."""
        config_path = Path("test_config.json")
        manager = ConfigManager(config_path)
        assert manager.config_path == config_path

    def test_load_config_no_file(self):
        """Test loading configuration when no file exists."""
        manager = ConfigManager()
        config = manager.load_config()

        # Should return default configuration
        assert isinstance(config, Configuration)
        assert config.project_name == "Unknown Project"

    def test_load_config_json_file(self):
        """Test loading configuration from JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "project_name": "Test Project",
                "copyright_holder": "Test Corp",
                "default_license": "Apache-2.0",
            }
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            config = manager.load_config()

            assert config.project_name == "Test Project"
            assert config.copyright_holder == "Test Corp"
            assert config.default_license == "Apache-2.0"

        finally:
            temp_path.unlink()

    def test_load_config_toml_file(self):
        """Test loading configuration from TOML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            config_data = {
                "project_name": "Test Project",
                "copyright_holder": "Test Corp",
                "default_license": "Apache-2.0",
            }
            toml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            config = manager.load_config()

            assert config.project_name == "Test Project"
            assert config.copyright_holder == "Test Corp"
            assert config.default_license == "Apache-2.0"

        finally:
            temp_path.unlink()

    def test_save_config_json(self):
        """Test saving configuration to JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "config.json"

            manager = ConfigManager()
            manager.config.project_name = "Test Project"
            manager.config.copyright_holder = "Test Corp"

            manager.save_config(temp_path)

            # Verify file was created and contains correct data
            assert temp_path.exists()
            with open(temp_path, 'r') as f:
                data = json.load(f)

            assert data["project_name"] == "Test Project"
            assert data["copyright_holder"] == "Test Corp"

    def test_save_config_toml(self):
        """Test saving configuration to TOML file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "config.toml"

            manager = ConfigManager()
            manager.config.project_name = "Test Project"
            manager.config.copyright_holder = "Test Corp"

            manager.save_config(temp_path)

            # Verify file was created and contains correct data
            assert temp_path.exists()
            with open(temp_path, 'r') as f:
                data = toml.load(f)

            assert data["project_name"] == "Test Project"
            assert data["copyright_holder"] == "Test Corp"

    def test_create_default_config(self):
        """Test creating default configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "spdx-scanner.config.json"

            manager = ConfigManager()
            manager.create_default_config(config_file)

            # Verify file was created
            assert config_file.exists()

            # Load and verify configuration
            config = manager.load_config(config_file)
            assert isinstance(config, Configuration)
            assert config.project_name == "Unknown Project"

    def test_update_from_args(self):
        """Test updating configuration from command-line arguments."""
        manager = ConfigManager()

        args = {
            "project_name": "CLI Project",
            "copyright_holder": "CLI Corp",
            "default_license": "GPL-3.0",
            "format": "json",
            "output_file": "report.json",
            "verbose": True,
            "quiet": False,
            "include_patterns": ["**/*.py"],
            "exclude_patterns": ["**/test_*"],
            "follow_symlinks": True,
            "max_file_size": 5 * 1024 * 1024,
            "create_backups": False,
            "dry_run": True,
            "allow_unknown_licenses": True,
            "require_osi_approved": True,
            "respect_gitignore": False,
        }

        manager.update_from_args(args)

        config = manager.get_config()
        assert config.project_name == "CLI Project"
        assert config.copyright_holder == "CLI Corp"
        assert config.default_license == "GPL-3.0"
        assert config.output_settings.format == "json"
        assert config.output_settings.output_file == "report.json"
        assert config.output_settings.verbose is True
        assert config.output_settings.quiet is False
        assert config.scanner_settings.include_patterns == ["**/*.py"]
        assert config.scanner_settings.exclude_patterns == ["**/test_*"]
        assert config.scanner_settings.follow_symlinks is True
        assert config.scanner_settings.max_file_size == 5 * 1024 * 1024
        assert config.correction_settings.create_backups is False
        assert config.correction_settings.dry_run is True
        assert config.validation_rules.allow_unknown_licenses is True
        assert config.validation_rules.require_osi_approved is True
        assert config.git_settings.respect_gitignore is False

    def test_find_config_file(self):
        """Test finding configuration file in directory tree."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create nested directory structure
            nested_dir = temp_path / "sub" / "nested"
            nested_dir.mkdir(parents=True)

            # Create config file in root
            config_file = temp_path / "spdx-scanner.config.json"
            config_data = {"project_name": "Found Project"}
            with open(config_file, 'w') as f:
                json.dump(config_data, f)

            # Test finding from nested directory
            manager = ConfigManager()
            manager.config_path = None  # Reset to force search

            # Change to nested directory and search
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(nested_dir)
                found_path = manager._find_config_file()
                assert found_path is not None
                assert found_path.name == "spdx-scanner.config.json"
            finally:
                os.chdir(original_cwd)

    def test_get_config(self):
        """Test getting current configuration."""
        manager = ConfigManager()
        config = manager.get_config()

        assert isinstance(config, Configuration)
        assert config.project_name == "Unknown Project"


class TestCreateDefaultConfigManager:
    """Test default configuration manager creation."""

    def test_create_default_config_manager(self):
        """Test creating default configuration manager."""
        manager = create_default_config_manager()
        assert isinstance(manager, ConfigManager)
        assert manager.config_path is None

    def test_create_default_config_manager_with_path(self):
        """Test creating default configuration manager with path."""
        config_path = Path("test_config.json")
        manager = create_default_config_manager(config_path)
        assert isinstance(manager, ConfigManager)
        assert manager.config_path == config_path