"""java-nav: CLI tools for IDE-like Java navigation in AI agents."""

import click

from java_nav.commands.api import api


@click.group()
@click.version_option()
def main() -> None:
    """CLI tools for IDE-like Java navigation in AI agents.

    Provides tiered Java code navigation — from instant javap lookups
    to full semantic analysis via LSP.
    """


main.add_command(api)
