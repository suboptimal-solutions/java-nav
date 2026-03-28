"""java-nav: CLI tools for IDE-like Java navigation in AI agents."""

import click

from java_nav.commands.api import api
from java_nav.commands.definition import definition
from java_nav.commands.deps import deps
from java_nav.commands.find import find
from java_nav.commands.grep import grep
from java_nav.commands.impls import impls, subtypes
from java_nav.commands.install import install_skill
from java_nav.commands.lsp_cmd import lsp
from java_nav.commands.refs import refs
from java_nav.commands.source import source
from java_nav.commands.symbols import symbols


@click.group()
@click.version_option()
def main() -> None:
    """CLI tools for IDE-like Java navigation in AI agents.

    Provides tiered Java code navigation — from instant javap lookups
    to full semantic analysis via jdtls.

    \b
    Prerequisites: JDK 17+, Maven. JDK 21+ for LSP commands (refs, def, find, symbols).
    """


# Tier 1
main.add_command(api)
main.add_command(deps)
main.add_command(grep)
main.add_command(source)

# Tier 2
main.add_command(impls)
main.add_command(subtypes)

# Tier 3
main.add_command(definition)
main.add_command(find)
main.add_command(lsp)
main.add_command(refs)
main.add_command(symbols)

# Setup
main.add_command(install_skill)
