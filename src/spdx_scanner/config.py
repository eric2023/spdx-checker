"""
Configuration management for SPDX Scanner.

This module provides functionality to load, validate, and manage configuration
for the SPDX scanner tool, supporting JSON, TOML, and command-line arguments.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict

try:
    import toml
except ImportError:
    # Use local minimal implementation if toml package is not available
    from . import toml


logger = logging.getLogger(__name__)


@dataclass
class ValidationRules:
    """Validation rules configuration."""
    require_license_identifier: bool = True
    require_copyright: bool = True
    require_project_attribution: bool = False
    allow_unknown_licenses: bool = False
    require_osi_approved: bool = False
    require_spdx_version: bool = False
    min_copyright_year: int = 1970
    max_copyright_year: int = 2030
    copyright_format: str = "standard"  # 'standard', 'flexible', 'any'
    license_format: str = "strict"  # 'strict', 'flexible'


@dataclass
class CorrectionSettings:
    """Correction settings configuration."""
    create_backups: bool = True
    backup_suffix: str = ".spdx-backup"
    preserve_existing: bool = True
    default_license: str = "MIT"
    default_copyright_holder: str = "Unknown"
    default_project_name: str = "Unknown Project"
    dry_run: bool = False


@dataclass
class ScannerSettings:
    """Scanner settings configuration."""
    follow_symlinks: bool = False
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    source_file_extensions: List[str] = field(default_factory=lambda: [
        ".h",      # C/C++ header files
        ".cpp",    # C++ source files
        ".c",      # C source files
        ".go",     # Go source files
    ])
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "**/node_modules/**",
        "**/build/**",
        "**/dist/**",
        "**/.git/**",
        "**/__pycache__/**",
        "**/*.egg-info/**",
        "**/venv/**",
        "**/env/**",
        "**/.venv/**",
        "**/.env/**",
        "**/target/**",
        "**/out/**",
        "**/bin/**",
        "**/obj/**",
        "**/.pytest_cache/**",
        "**/.mypy_cache/**",
        "**/coverage/**",
        "**/htmlcov/**",
        "**/.tox/**",
        "**/.nox/**",
    ])

    def __post_init__(self):
        """Generate include_patterns from source_file_extensions if not set."""
        if not self.include_patterns:
            self.include_patterns = [f"**/*{ext}" for ext in self.source_file_extensions]


@dataclass
class OutputSettings:
    """Output settings configuration."""
    format: str = "text"  # 'text', 'json', 'html', 'markdown', 'csv'
    output_file: Optional[str] = None
    verbose: bool = False
    quiet: bool = False
    show_progress: bool = True
    include_summary: bool = True
    include_details: bool = True


@dataclass
class GitSettings:
    """Git integration settings."""
    enabled: bool = True
    respect_gitignore: bool = True
    use_git_timestamps: bool = True
    check_uncommitted: bool = False
    check_untracked: bool = False


@dataclass
class TemplateSettings:
    """License header template settings."""
    templates: Dict[str, str] = field(default_factory=dict)
    use_custom_templates: bool = False
    template_directory: Optional[str] = None


@dataclass
class Configuration:
    """Main configuration class for SPDX Scanner."""
    project_name: str = "Unknown Project"
    project_version: str = "1.0.0"
    copyright_holder: str = "Unknown"
    default_license: str = "MIT"
    validation_rules: ValidationRules = field(default_factory=ValidationRules)
    correction_settings: CorrectionSettings = field(default_factory=CorrectionSettings)
    scanner_settings: ScannerSettings = field(default_factory=ScannerSettings)
    output_settings: OutputSettings = field(default_factory=OutputSettings)
    git_settings: GitSettings = field(default_factory=GitSettings)
    template_settings: TemplateSettings = field(default_factory=TemplateSettings)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Configuration":
        """Create configuration from dictionary."""
        config = cls()

        # Set basic fields
        config.project_name = data.get('project_name', config.project_name)
        config.project_version = data.get('project_version', config.project_version)
        config.copyright_holder = data.get('copyright_holder', config.copyright_holder)
        config.default_license = data.get('default_license', config.default_license)

        # Set nested configurations
        if 'validation_rules' in data:
            config.validation_rules = ValidationRules(**data['validation_rules'])

        if 'correction_settings' in data:
            config.correction_settings = CorrectionSettings(**data['correction_settings'])

        if 'scanner_settings' in data:
            scanner_data = data['scanner_settings'].copy()
            # Handle source_file_extensions if present
            if 'source_file_extensions' in scanner_data and scanner_data['source_file_extensions']:
                # Ensure extensions start with dot
                scanner_data['source_file_extensions'] = [
                    ext if ext.startswith('.') else f'.{ext}'
                    for ext in scanner_data['source_file_extensions']
                ]
            config.scanner_settings = ScannerSettings(**scanner_data)

        if 'output_settings' in data:
            config.output_settings = OutputSettings(**data['output_settings'])

        if 'git_settings' in data:
            config.git_settings = GitSettings(**data['git_settings'])

        if 'template_settings' in data:
            config.template_settings = TemplateSettings(**data['template_settings'])

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # Validate basic fields
        if not self.project_name or not self.project_name.strip():
            errors.append("project_name cannot be empty")

        if not self.copyright_holder or not self.copyright_holder.strip():
            errors.append("copyright_holder cannot be empty")

        if not self.default_license or not self.default_license.strip():
            errors.append("default_license cannot be empty")

        # Validate license format
        if not self._is_valid_spdx_license(self.default_license):
            errors.append(f"default_license '{self.default_license}' is not a valid SPDX license identifier")

        # Validate validation rules
        if self.validation_rules.min_copyright_year < 1900:
            errors.append("min_copyright_year must be >= 1900")

        if self.validation_rules.max_copyright_year > 2100:
            errors.append("max_copyright_year must be <= 2100")

        if self.validation_rules.min_copyright_year >= self.validation_rules.max_copyright_year:
            errors.append("min_copyright_year must be less than max_copyright_year")

        # Validate scanner settings
        if self.scanner_settings.max_file_size <= 0:
            errors.append("max_file_size must be positive")

        # Validate output settings
        valid_formats = ['text', 'json', 'html', 'markdown', 'csv']
        if self.output_settings.format not in valid_formats:
            errors.append(f"output format must be one of: {valid_formats}")

        return errors

    def _is_valid_spdx_license(self, license_id: str) -> bool:
        """Basic validation of SPDX license identifier."""
        # Simple validation - in production, you'd use a proper SPDX license list
        valid_pattern = r'^[A-Za-z0-9\-\+\.\(\)]+$'
        return bool(re.match(valid_pattern, license_id))


class ConfigManager:
    """Configuration manager for SPDX Scanner."""

    DEFAULT_CONFIG_FILES = [
        'spdx-scanner.config.json',
        'spdx-scanner.config.toml',
        '.spdx-scanner.json',
        '.spdx-scanner.toml',
        'pyproject.toml',  # Look for [tool.spdx-scanner] section
    ]

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager."""
        self.config_path = config_path
        self.config = Configuration()

    def load_config(self, config_path: Optional[Path] = None) -> Configuration:
        """Load configuration from file."""
        if config_path:
            self.config_path = config_path

        if not self.config_path:
            # Try to find config file automatically
            self.config_path = self._find_config_file()

        if not self.config_path or not self.config_path.exists():
            logger.info("No configuration file found, using defaults")
            return self.config

        try:
            config_data = self._read_config_file(self.config_path)
            self.config = Configuration.from_dict(config_data)

            # Validate loaded configuration
            errors = self.config.validate()
            if errors:
                logger.warning(f"Configuration validation errors: {errors}")

            logger.info(f"Loaded configuration from: {self.config_path}")
            return self.config

        except Exception as e:
            logger.error(f"Failed to load configuration from {self.config_path}: {e}")
            logger.info("Using default configuration")
            return self.config

    def save_config(self, config_path: Optional[Path] = None) -> None:
        """Save current configuration to file."""
        if config_path:
            self.config_path = config_path

        if not self.config_path:
            self.config_path = Path('spdx-scanner.config.json')

        try:
            config_data = self.config.to_dict()

            if self.config_path.suffix.lower() == '.toml':
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    toml.dump(config_data, f)
            else:
                # Default to JSON
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2)

            logger.info(f"Saved configuration to: {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration to {self.config_path}: {e}")
            raise

    def create_default_config(self, config_path: Optional[Path] = None) -> None:
        """Create a default configuration file."""
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = Path('spdx-scanner.config.json')

        # Create default configuration
        self.config = Configuration()

        # Save default configuration
        self.save_config()

        logger.info(f"Created default configuration file: {self.config_path}")

    def update_from_args(self, args: Dict[str, Any]) -> None:
        """Update configuration from command-line arguments."""
        # Update basic settings
        if 'project_name' in args and args['project_name'] is not None:
            self.config.project_name = args['project_name']

        if 'copyright_holder' in args and args['copyright_holder'] is not None:
            self.config.copyright_holder = args['copyright_holder']

        if 'default_license' in args and args['default_license'] is not None:
            self.config.default_license = args['default_license']

        # Update output settings
        if 'format' in args and args['format'] is not None:
            self.config.output_settings.format = args['format']

        if 'output_file' in args and args['output_file'] is not None:
            self.config.output_settings.output_file = args['output_file']

        if 'verbose' in args and args['verbose'] is not None:
            self.config.output_settings.verbose = args['verbose']

        if 'quiet' in args and args['quiet'] is not None:
            self.config.output_settings.quiet = args['quiet']

        # Update scanner settings
        if 'include_patterns' in args and args['include_patterns'] is not None:
            self.config.scanner_settings.include_patterns = args['include_patterns']

        if 'exclude_patterns' in args and args['exclude_patterns'] is not None:
            self.config.scanner_settings.exclude_patterns = args['exclude_patterns']

        if 'source_file_extensions' in args and args['source_file_extensions'] is not None:
            # Ensure extensions start with dot
            extensions = args['source_file_extensions']
            if extensions:
                self.config.scanner_settings.source_file_extensions = [
                    ext if ext.startswith('.') else f'.{ext}'
                    for ext in extensions
                ]
                # Regenerate include_patterns from extensions
                self.config.scanner_settings.include_patterns = [
                    f"**/*{ext}" for ext in self.config.scanner_settings.source_file_extensions
                ]

        if 'follow_symlinks' in args and args['follow_symlinks'] is not None:
            self.config.scanner_settings.follow_symlinks = args['follow_symlinks']

        if 'max_file_size' in args and args['max_file_size'] is not None:
            self.config.scanner_settings.max_file_size = args['max_file_size']

        # Update correction settings
        if 'create_backups' in args and args['create_backups'] is not None:
            self.config.correction_settings.create_backups = args['create_backups']

        if 'dry_run' in args and args['dry_run'] is not None:
            self.config.correction_settings.dry_run = args['dry_run']

        # Update validation rules
        if 'allow_unknown_licenses' in args and args['allow_unknown_licenses'] is not None:
            self.config.validation_rules.allow_unknown_licenses = args['allow_unknown_licenses']

        if 'require_osi_approved' in args and args['require_osi_approved'] is not None:
            self.config.validation_rules.require_osi_approved = args['require_osi_approved']

        # Update Git settings
        if 'respect_gitignore' in args and args['respect_gitignore'] is not None:
            self.config.git_settings.respect_gitignore = args['respect_gitignore']

    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in current directory or parent directories."""
        current_dir = Path.cwd()

        # Search up the directory tree
        while current_dir != current_dir.parent:
            for config_file in self.DEFAULT_CONFIG_FILES:
                config_path = current_dir / config_file
                if config_path.exists():
                    return config_path

            current_dir = current_dir.parent

        return None

    def _read_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Read configuration from file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        suffix = config_path.suffix.lower()

        if suffix == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        elif suffix == '.toml':
            with open(config_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
                # Check for tool.spdx-scanner section in pyproject.toml
                if config_path.name == 'pyproject.toml' and 'tool' in data and 'spdx-scanner' in data['tool']:
                    return data['tool']['spdx-scanner']
                return data

        else:
            raise ValueError(f"Unsupported configuration file format: {suffix}")

    def get_config(self) -> Configuration:
        """Get current configuration."""
        return self.config


def create_default_config_manager(config_path: Optional[Path] = None) -> ConfigManager:
    """Create a default configuration manager."""
    return ConfigManager(config_path)