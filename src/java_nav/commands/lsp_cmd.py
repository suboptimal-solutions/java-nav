"""Tier 3: jdtls daemon management commands."""

import os

import click

from java_nav.lsp.server import is_running, start_daemon, stop_daemon


@click.group()
def lsp() -> None:
    """Manage the jdtls language server daemon.

    Start a persistent jdtls daemon for fast semantic queries.
    Without a daemon, commands like refs/def/find/symbols start jdtls on-demand (~5-15s).
    With a daemon, they respond in <200ms.
    """


@lsp.command()
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
def start(project_dir: str) -> None:
    """Start jdtls daemon for a project."""
    project_dir = os.path.abspath(project_dir)

    if is_running(project_dir):
        print("jdtls daemon is already running.")
        return

    print("Starting jdtls daemon (this may take 30s-2min for first indexing)...")
    pid = start_daemon(project_dir)
    print(f"jdtls daemon started (PID {pid}).")


@lsp.command()
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
def stop(project_dir: str) -> None:
    """Stop jdtls daemon for a project."""
    project_dir = os.path.abspath(project_dir)

    if stop_daemon(project_dir):
        print("jdtls daemon stopped.")
    else:
        print("No jdtls daemon running.")


@lsp.command()
@click.option(
    "--project-dir",
    "-d",
    default=".",
    help="Path to the Maven project root.",
)
def status(project_dir: str) -> None:
    """Check jdtls daemon status."""
    project_dir = os.path.abspath(project_dir)

    if is_running(project_dir):
        from java_nav.lsp.server import get_port

        port = get_port(project_dir)
        print(f"jdtls daemon is running (port {port}).")
    else:
        print("jdtls daemon is not running.")
