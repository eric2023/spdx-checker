"""
Command-line interface for SPDX Scanner.

This module provides the CLI interface for the SPDX scanner tool, including
subcommands for scanning, correcting, and validating SPDX license declarations.
"""

import sys
from pathlib import Path
from typing import Optional, List
import logging

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.logging import RichHandler

from . import __version__
from .config import ConfigManager, Configuration
from .scanner import FileScanner, create_default_scanner
from .parser import SPDXParser, create_default_parser
from .validator import SPDXValidator, create_default_validator
from .corrector import SPDXCorrector, create_default_corrector
from .reporter import Reporter, create_default_reporter
from .models import ScanResult, ScanSummary


# Initialize rich console
console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="spdx-scanner")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Configuration file path",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress output except errors",
)
@click.pass_context
def main(ctx: click.Context, config: Optional[Path], verbose: bool, quiet: bool) -> None:
    """SPDX License Scanner - Automatic license declaration scanner and corrector."""
    # Configure logging
    log_level = logging.WARNING
    if verbose:
        log_level = logging.DEBUG
    elif quiet:
        log_level = logging.ERROR

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )

    # Load configuration
    config_manager = ConfigManager(config)
    configuration = config_manager.load_config()

    # Store in context
    ctx.ensure_object(dict)
    ctx.obj['config'] = configuration
    ctx.obj['config_manager'] = config_manager
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "html", "markdown", "csv"]),
    default="text",
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.option(
    "--include",
    multiple=True,
    help="Include file patterns (can be used multiple times)",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Exclude file patterns (can be used multiple times)",
)
@click.option(
    "--follow-symlinks",
    is_flag=True,
    help="Follow symbolic links",
)
@click.option(
    "--max-file-size",
    type=int,
    default=10 * 1024 * 1024,  # 10MB
    help="Maximum file size to process (bytes)",
)
@click.pass_context
def scan(
    ctx: click.Context,
    path: Path,
    format: str,
    output: Optional[Path],
    include: tuple,
    exclude: tuple,
    follow_symlinks: bool,
    max_file_size: int,
) -> None:
    """Scan directory for SPDX license issues."""
    config: Configuration = ctx.obj['config']
    verbose: bool = ctx.obj['verbose']
    quiet: bool = ctx.obj['quiet']

    if not quiet:
        console.print(f"[bold blue]SPDX Scanner v{__version__}[/bold blue]")
        console.print(f"Scanning: {path}")

    try:
        # Create scanner with configuration
        scanner = create_default_scanner(
            include_patterns=list(include) if include else None,
            exclude_patterns=list(exclude) if exclude else None,
        )
        scanner.follow_symlinks = follow_symlinks
        scanner.max_file_size = max_file_size

        # Create parser and validator
        parser = create_default_parser()
        validator = create_default_validator()

        # Scan files
        results = []
        file_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task("Scanning files...", total=None)

            for file_info in scanner.scan_directory(path):
                # Parse SPDX information
                spdx_info = parser.parse_file(file_info)
                file_info.spdx_info = spdx_info

                # Validate SPDX information
                validation_result = validator.validate(spdx_info)

                # Create scan result
                scan_result = ScanResult(
                    file_info=file_info,
                    validation_result=validation_result,
                )
                results.append(scan_result)
                file_count += 1

                progress.update(task, description=f"Scanned {file_count} files")

        if not quiet:
            console.print(f"Scanned {file_count} files")

        # Generate summary
        reporter = create_default_reporter()
        summary = reporter.create_summary(results)

        # Generate report
        if output:
            report_path = reporter.generate_report(results, summary, format, str(output))
            if not quiet:
                console.print(f"Report saved to: {report_path}")
        else:
            report_content = reporter.generate_report(results, summary, format)
            if not quiet:
                console.print(report_content)

        # Show summary
        if not quiet:
            _show_summary(summary)

        # Exit with appropriate code
        sys.exit(0 if summary.invalid_files == 0 else 1)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(2)


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without modifying files",
)
@click.option(
    "--backup/--no-backup",
    default=True,
    help="Create backup files before correction",
)
@click.option(
    "--license",
    help="Default license identifier",
)
@click.option(
    "--copyright-holder",
    help="Default copyright holder",
)
@click.option(
    "--project-name",
    help="Default project name",
)
@click.option(
    "--include",
    multiple=True,
    help="Include file patterns (can be used multiple times)",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Exclude file patterns (can be used multiple times)",
)
@click.pass_context
def correct(
    ctx: click.Context,
    path: Path,
    dry_run: bool,
    backup: bool,
    license: Optional[str],
    copyright_holder: Optional[str],
    project_name: Optional[str],
    include: tuple,
    exclude: tuple,
) -> None:
    """Automatically correct SPDX license issues."""
    config: Configuration = ctx.obj['config']
    verbose: bool = ctx.obj['verbose']
    quiet: bool = ctx.obj['quiet']

    if not quiet:
        console.print(f"[bold blue]SPDX Scanner v{__version__} - Correct Mode[/bold blue]")
        console.print(f"Correcting: {path}")
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No files will be modified[/yellow]")

    try:
        # Create scanner with configuration
        scanner = create_default_scanner(
            include_patterns=list(include) if include else None,
            exclude_patterns=list(exclude) if exclude else None,
        )

        # Create parser, validator, and corrector
        parser = create_default_parser()
        validator = create_default_validator()

        # Configure corrector
        corrector_config = {
            'create_backups': backup,
            'dry_run': dry_run,
        }
        if license:
            corrector_config['default_license'] = license
        if copyright_holder:
            corrector_config['default_copyright_holder'] = copyright_holder
        if project_name:
            corrector_config['default_project_name'] = project_name

        corrector = create_default_corrector(corrector_config)

        # Scan and correct files
        results = []
        file_count = 0
        corrected_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task("Processing files...", total=None)

            for file_info in scanner.scan_directory(path):
                # Parse SPDX information
                spdx_info = parser.parse_file(file_info)
                file_info.spdx_info = spdx_info

                # Validate SPDX information
                validation_result = validator.validate(spdx_info)

                # Create scan result
                scan_result = ScanResult(
                    file_info=file_info,
                    validation_result=validation_result,
                )

                # Correct if needed
                if scan_result.needs_correction():
                    correction_result = corrector.correct_file(file_info, dry_run=dry_run)
                    scan_result.correction_result = correction_result

                    if correction_result.success and correction_result.has_changes():
                        corrected_count += 1
                        if not quiet:
                            console.print(f"[green]Corrected:[/green] {file_info.filepath}")

                results.append(scan_result)
                file_count += 1

                progress.update(task, description=f"Processed {file_count} files")

        if not quiet:
            console.print(f"Processed {file_count} files, corrected {corrected_count} files")

        # Generate summary
        reporter = create_default_reporter()
        summary = reporter.create_summary(results)

        # Show summary
        if not quiet:
            _show_summary(summary)

        # Exit with appropriate code
        sys.exit(0)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(2)


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "html", "markdown", "csv"]),
    default="text",
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.pass_context
def validate(
    ctx: click.Context,
    path: Path,
    format: str,
    output: Optional[Path],
) -> None:
    """Validate SPDX license declarations."""
    config: Configuration = ctx.obj['config']
    verbose: bool = ctx.obj['verbose']
    quiet: bool = ctx.obj['quiet']

    if not quiet:
        console.print(f"[bold blue]SPDX Scanner v{__version__} - Validate Mode[/bold blue]")
        console.print(f"Validating: {path}")

    try:
        # Create scanner and validator
        scanner = create_default_scanner()
        parser = create_default_parser()
        validator = create_default_validator()

        # Scan and validate files
        results = []
        file_count = 0
        invalid_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task("Validating files...", total=None)

            for file_info in scanner.scan_directory(path):
                # Parse SPDX information
                spdx_info = parser.parse_file(file_info)
                file_info.spdx_info = spdx_info

                # Validate SPDX information
                validation_result = validator.validate(spdx_info)

                # Create scan result
                scan_result = ScanResult(
                    file_info=file_info,
                    validation_result=validation_result,
                )
                results.append(scan_result)
                file_count += 1

                if not scan_result.is_valid():
                    invalid_count += 1

                progress.update(task, description=f"Validated {file_count} files")

        if not quiet:
            console.print(f"Validated {file_count} files, found {invalid_count} invalid files")

        # Generate report
        reporter = create_default_reporter()
        summary = reporter.create_summary(results)

        if output:
            report_path = reporter.generate_report(results, summary, format, str(output))
            if not quiet:
                console.print(f"Report saved to: {report_path}")
        else:
            report_content = reporter.generate_report(results, summary, format)
            if not quiet:
                console.print(report_content)

        # Show validation summary
        if not quiet:
            _show_validation_summary(results)

        # Exit with appropriate code
        sys.exit(0 if invalid_count == 0 else 1)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(2)


@main.command()
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Project path for configuration",
)
@click.option(
    "--format",
    type=click.Choice(["json", "toml"]),
    default="json",
    help="Configuration file format",
)
@click.pass_context
def init(ctx: click.Context, path: Path, format: str) -> None:
    """Initialize configuration file."""
    config_manager: ConfigManager = ctx.obj['config_manager']
    quiet: bool = ctx.obj['quiet']

    try:
        # Create default configuration
        config_manager.create_default_config(path / f"spdx-scanner.config.{format}")

        if not quiet:
            console.print(f"[green]Configuration file created:[/green] {path / f'spdx-scanner.config.{format}'}")
            console.print("Edit the configuration file to customize the scanner settings.")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(2)


@main.command()
@click.pass_context
def install_hook(ctx: click.Context) -> None:
    """Install Git pre-commit hook."""
    quiet: bool = ctx.obj['quiet']

    try:
        # Check if we're in a Git repository
        git_dir = Path(".git")
        if not git_dir.exists():
            console.print("[bold red]Error:[/bold red] Not in a Git repository")
            sys.exit(1)

        # Create pre-commit hook
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        pre_commit_hook = hooks_dir / "pre-commit"
        hook_content = """#!/bin/sh
# SPDX Scanner pre-commit hook
# This hook validates SPDX license declarations before commits

if command -v spdx-scanner >/dev/null 2>&1; then
    echo "Validating SPDX license declarations..."
    spdx-scanner validate --format text .
    if [ $? -ne 0 ]; then
        echo "SPDX validation failed. Please fix license declarations before committing."
        exit 1
    fi
else
    echo "Warning: spdx-scanner not found in PATH. Skipping SPDX validation."
fi
"""

        pre_commit_hook.write_text(hook_content)
        pre_commit_hook.chmod(0o755)

        if not quiet:
            console.print("[green]Pre-commit hook installed successfully[/green]")
            console.print("The hook will validate SPDX license declarations before each commit.")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(2)


def _show_summary(summary: ScanSummary) -> None:
    """Show scan summary."""
    table = Table(title="Scan Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Files", str(summary.total_files))
    table.add_row("Valid Files", f"{summary.valid_files} ({summary.get_success_rate():.1f}%)")
    table.add_row("Invalid Files", str(summary.invalid_files))
    table.add_row("Corrected Files", str(summary.corrected_files))
    table.add_row("Failed Corrections", str(summary.failed_corrections))

    console.print(table)


def _show_validation_summary(results: List[ScanResult]) -> None:
    """Show validation summary."""
    invalid_files = [r for r in results if not r.is_valid()]

    if not invalid_files:
        console.print("[green]All files have valid SPDX declarations![/green]")
        return

    console.print(f"[yellow]Found {len(invalid_files)} files with validation issues:[/yellow]")

    for result in invalid_files[:10]:  # Show first 10 invalid files
        console.print(f"  [red]✗[/red] {result.file_info.filepath}")
        for error in result.validation_result.errors:
            console.print(f"    - {error.message}")

    if len(invalid_files) > 10:
        console.print(f"  ... and {len(invalid_files) - 10} more files")


if __name__ == "__main__":
    main()