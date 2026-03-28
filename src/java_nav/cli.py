"""java-nav: CLI tools for IDE-like Java navigation in AI agents."""

import click

from java_nav.commands.api import api
from java_nav.commands.deps import deps
from java_nav.commands.grep import grep
from java_nav.commands.impls import impls, subtypes
from java_nav.commands.source import source


@click.group()
@click.version_option()
def main() -> None:
    """CLI tools for IDE-like Java navigation in AI agents.

    Provides tiered Java code navigation — from instant javap lookups
    to full semantic analysis via LSP.

    \b
    Prerequisites: JDK 17+, Maven. Optional: ripgrep (for faster grep).
    """


main.add_command(api)
main.add_command(deps)
main.add_command(grep)
main.add_command(impls)
main.add_command(source)
main.add_command(subtypes)
