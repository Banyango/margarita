"""Command-line interface for margarita template rendering."""

import contextlib
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Optional

import click

from margarita.parser import Parser
from margarita.renderer import Renderer
from margarita.resources.skill import skill
from margarita.resources.syntax import syntax


@click.group()
@click.version_option(version=version("margarita"), prog_name="margarita")
def main():
    """Margarita template rendering tool.

    Render margarita template files with variable substitution.
    """
    pass


@main.command()
def install_claude_skill():
    """Install the claude skill for margarita."""
    margarita_dir = Path(os.getcwd()) / ".claude" / "skills" / "margarita"
    if not margarita_dir.exists():
        try:
            margarita_dir.mkdir(parents=True)
        except Exception as e:
            click.echo(f"Error creating margarita directory: {e}", err=True)
            sys.exit(1)

    # Copy SKILL.md to the margarita skill directory
    skill_md = margarita_dir / "SKILL.md"
    try:
        skill_md.write_text(skill)
    except Exception as e:
        click.echo(f"Error writing skill file: {e}", err=True)
        sys.exit(1)

    syntax_md = margarita_dir / "references" / "syntax.md"
    try:
        syntax_md.parent.mkdir(parents=True, exist_ok=True)
        syntax_md.write_text(syntax)
    except Exception as e:
        click.echo(f"Error writing syntax reference: {e}", err=True)
        sys.exit(1)

    click.echo(f"Margarita skill installed successfully")


@main.command()
@click.argument("template_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output file/directory path (default: stdout)",
)
@click.option("-c", "--context", type=str, help="JSON string with variables for rendering")
@click.option(
    "-f",
    "--context-file",
    type=click.Path(exists=True, path_type=Path),
    help="JSON file with variables for rendering",
)
@click.option("--show-metadata", is_flag=True, help="Display template metadata before rendering")
def render(
    template_path: Path,
    output: Optional[Path],
    context: Optional[str],
    context_file: Optional[Path],
    show_metadata: bool,
):
    """Render a margarita template file or directory to markdown.

    TEMPLATE_PATH is the path to a .mg template file or a directory containing .mg files.

    Examples:

        # Render with variables from JSON string
        margarita render template.mg -c '{"name": "World"}'

        # Render with variables from JSON file
        margarita render template.mg -f context.json

        # Save output to file
        margarita render template.mg -o output.md -c '{"name": "World"}'

        # Render all templates in a directory
        margarita render templates/ -o output/

        # Show metadata
        margarita render template.mg --show-metadata
    """
    # Parse context
    context_dict = {}
    if context:
        try:
            context_dict = json.loads(context)
        except json.JSONDecodeError as e:
            click.echo(f"Error parsing context JSON: {e}", err=True)
            sys.exit(1)
    elif context_file:
        try:
            context_dict = json.loads(context_file.read_text())
        except json.JSONDecodeError as e:
            click.echo(f"Error parsing context file JSON: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error reading context file: {e}", err=True)
            sys.exit(1)
    elif template_path.is_file():
        # Try to find a context file with the same name but .json extension
        auto_context_file = template_path.with_suffix(".json")
        if auto_context_file.exists():
            try:
                context_dict = json.loads(auto_context_file.read_text())
            except json.JSONDecodeError as e:
                click.echo(
                    f"Error parsing auto-detected context file {auto_context_file}: {e}", err=True
                )
                sys.exit(1)
            except Exception as e:
                click.echo(
                    f"Error reading auto-detected context file {auto_context_file}: {e}", err=True
                )
                sys.exit(1)

    # Determine if we're processing a file or directory
    if template_path.is_file():
        _render_single_file(template_path, output, context_dict, show_metadata)
    elif template_path.is_dir():
        _render_directory(template_path, output, context_dict, show_metadata)
    else:
        click.echo(f"Error: {template_path} is neither a file nor a directory", err=True)
        sys.exit(1)


def _build_uv_package_paths(base_dir: Path) -> dict[str, Path]:
    """Build a mapping of package name -> templates/ directory from the .venv tree.

    Walks up from base_dir to the filesystem root looking for a .venv/ directory,
    then reads each dist-info's METADATA to extract the package Name and maps it
    to its templates/ directory. If two packages share a name the duplicate is
    skipped and a warning is printed — callers can use ``[[ <name>/<file> ]]`` safely.
    """
    search = base_dir.resolve()
    while True:
        venv = search / ".venv"
        if venv.is_dir():
            site_packages_matches = sorted(venv.glob("lib/python*/site-packages"))
            if site_packages_matches:
                site_packages = site_packages_matches[0]
                result: dict[str, Path] = {}
                for dist_info in sorted(site_packages.glob("*.dist-info")):
                    metadata_file = dist_info / "METADATA"
                    if not metadata_file.is_file():
                        continue
                    name = ""
                    try:
                        for line in metadata_file.read_text().splitlines():
                            if line.lower().startswith("name:"):
                                name = line.split(":", 1)[1].strip()
                                break
                    except Exception:
                        continue
                    if not name:
                        continue

                    module_name = ""
                    top_level_file = dist_info / "top_level.txt"
                    if top_level_file.is_file():
                        with contextlib.suppress(Exception):
                            module_name = top_level_file.read_text().strip().splitlines()[0].strip()
                    if not module_name:
                        stem = dist_info.name[: -len(".dist-info")]
                        module_name = stem.rsplit("-", 1)[0].replace("-", "_")

                    templates_dir = site_packages / module_name / "templates"
                    if not templates_dir.is_dir():
                        continue

                    if name in result:
                        click.echo(
                            f"Warning: uv package '{name}' appears more than once in site-packages; "
                            f"skipping duplicate at {dist_info}",
                            err=True,
                        )
                        continue
                    result[name] = templates_dir
                return result
        parent = search.parent
        if parent == search:
            break
        search = parent
    return {}


def _render_single_file(
    template_file: Path, output: Optional[Path], context_dict: dict, show_metadata: bool
):
    """Render a single template file."""
    # Read the template file
    try:
        template_content = template_file.read_text()
    except Exception as e:
        click.echo(f"Error reading template file: {e}", err=True)
        sys.exit(1)

    # Parse the template
    try:
        parser = Parser()
        metadata, nodes = parser.parse(template_content)

        if parser.is_mgx:
            click.echo(
                "Error: cannot render .mgx — we can't render .mgx files, you need to execute them.",
                err=True,
            )
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error parsing template: {e}", err=True)
        sys.exit(1)

    # Show metadata if requested
    if show_metadata and metadata:
        click.echo("=== Template Metadata ===", err=True)
        for key, value in metadata.items():
            click.echo(f"{key}: {value}", err=True)
        click.echo("=== Rendered Output ===", err=True)

    # Render the template
    try:
        package_paths = _build_uv_package_paths(template_file.parent)
        renderer = Renderer(
            context=context_dict,
            base_path=template_file.parent,
            package_paths=package_paths,
        )
        result = renderer.render(nodes)
    except Exception as e:
        click.echo(f"Error rendering template: {e}", err=True)
        sys.exit(1)

    # Output the result
    if output is None and template_file.is_file():
        output = template_file.with_suffix(".md")
    else:
        return

    try:
        output.write_text(result)
        click.echo(f"Output written to: {output}", err=True)
    except Exception as e:
        click.echo(f"Error writing output file: {e}", err=True)
        sys.exit(1)


def _render_directory(
    template_dir: Path, output_dir: Path | None, context_dict: dict, show_metadata: bool
):
    margarita_files = list(template_dir.glob("*.mg"))

    if not margarita_files:
        click.echo(f"No .mg files found in directory: {template_dir}", err=True)
        sys.exit(1)

    if output_dir:
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            click.echo(f"Error creating output directory: {e}", err=True)
            sys.exit(1)

    for template_file in margarita_files:
        if show_metadata:
            click.echo(f"\n=== Processing: {template_file.name} ===", err=True)

        if output_dir:
            output_file = output_dir / template_file.with_suffix(".md").name
        else:
            output_file = None

        file_context = context_dict.copy()
        if not context_dict:
            auto_context_file = template_file.with_suffix(".json")

            if auto_context_file.exists():
                try:
                    file_context = json.loads(auto_context_file.read_text())
                except json.JSONDecodeError as e:
                    click.echo(
                        f"Error parsing auto-detected context file {auto_context_file}: {e}",
                        err=True,
                    )
                    sys.exit(1)
                except Exception as e:
                    click.echo(
                        f"Error reading auto-detected context file {auto_context_file}: {e}",
                        err=True,
                    )
                    sys.exit(1)

        _render_single_file(template_file, output_file, file_context, show_metadata)

        if not output_file and len(margarita_files) > 1:
            click.echo(f"\n--- End of {template_file.name} ---\n")


@main.command()
@click.argument("template_path", type=click.Path(exists=True, path_type=Path))
def metadata(template_path: Path):
    """Show metadata from a margarita template file or directory.

    TEMPLATE_PATH is the path to a .mg template file or a directory containing .mg files.

    Examples:

        margarita metadata template.mg
        margarita metadata templates/
    """
    # Determine if we're processing a file or directory
    if template_path.is_file():
        _show_metadata_single_file(template_path)
    elif template_path.is_dir():
        _show_metadata_directory(template_path)
    else:
        click.echo(f"Error: {template_path} is neither a file nor a directory", err=True)
        sys.exit(1)


def _show_metadata_single_file(template_file: Path):
    """Show metadata from a single template file."""
    # Read the template file
    try:
        template_content = template_file.read_text()
    except Exception as e:
        click.echo(f"Error reading template file: {e}", err=True)
        sys.exit(1)

    # Parse the template
    try:
        parser = Parser()
        metadata_dict, _ = parser.parse(template_content)
    except Exception as e:
        click.echo(f"Error parsing template: {e}", err=True)
        sys.exit(1)

    # Display metadata
    if metadata_dict:
        for key, value in metadata_dict.items():
            click.echo(f"{key}: {value}")
    else:
        click.echo("No metadata found in template.", err=True)


def _show_metadata_directory(template_dir: Path):
    """Show metadata from all .mg files in a directory."""
    # Find all .mg files
    margarita_files = list(template_dir.glob("*.mg"))

    if not margarita_files:
        click.echo(f"No .mg files found in directory: {template_dir}", err=True)
        sys.exit(1)

    # Process each file
    for i, template_file in enumerate(margarita_files):
        if i > 0:
            click.echo()  # Blank line between files

        click.echo(f"=== {template_file.name} ===")

        try:
            template_content = template_file.read_text()
            parser = Parser()
            metadata_dict, _ = parser.parse(template_content)

            if metadata_dict:
                for key, value in metadata_dict.items():
                    click.echo(f"{key}: {value}")
            else:
                click.echo("No metadata found")
        except Exception as e:
            click.echo(f"Error processing file: {e}", err=True)


if __name__ == "__main__":
    main()
