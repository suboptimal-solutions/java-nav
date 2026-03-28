"""LSP client — queries jdtls via daemon or on-demand."""

import json
import os
import socket
import sys

from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger

from java_nav.lsp.server import get_port, is_running

# LSP symbol kinds (subset)
SYMBOL_KINDS = {
    1: "file",
    2: "module",
    3: "namespace",
    4: "package",
    5: "class",
    6: "method",
    7: "property",
    8: "field",
    9: "constructor",
    10: "enum",
    11: "interface",
    12: "function",
    13: "variable",
    14: "constant",
    22: "struct",
    23: "event",
    26: "type_parameter",
}


def _query_daemon(project_dir: str, method: str, params: dict) -> list | dict:
    """Send a query to the running daemon and return the result."""
    port = get_port(project_dir)
    if port is None:
        print("jdtls daemon not running.", file=sys.stderr)
        sys.exit(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("127.0.0.1", port))
        payload = json.dumps({"method": method, "params": params}) + "\n"
        sock.sendall(payload.encode())
        # Read response
        data = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
            if b"\n" in data:
                break
        result = json.loads(data.decode().strip())
        if isinstance(result, dict) and "error" in result:
            print(f"LSP error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        return result
    finally:
        sock.close()


def _query_on_demand(project_dir: str, method: str, params: dict) -> list | dict:
    """Start jdtls inline, execute one query, exit."""
    logger = MultilspyLogger()
    config = MultilspyConfig.from_dict({"code_language": "java"})
    lsp = SyncLanguageServer.create(config, logger, project_dir)

    with lsp.start_server():
        if method == "references":
            return lsp.request_references(params["file"], params["line"], params["col"])
        elif method == "definition":
            return lsp.request_definition(params["file"], params["line"], params["col"])
        elif method == "document_symbols":
            return lsp.request_document_symbols(params["file"])
        elif method == "hover":
            return lsp.request_hover(params["file"], params["line"], params["col"])
        elif method == "workspace_symbol":
            return lsp.request_workspace_symbol(params["query"])
        else:
            print(f"Unknown method: {method}", file=sys.stderr)
            sys.exit(1)


def query(project_dir: str, method: str, params: dict) -> list | dict:
    """Route query to daemon if running, otherwise start on-demand."""
    if is_running(project_dir):
        return _query_daemon(project_dir, method, params)
    return _query_on_demand(project_dir, method, params)


def resolve_symbol_to_position(
    project_dir: str, class_name: str, method_name: str | None = None
) -> tuple[str, int, int] | None:
    """Resolve a text-based symbol reference (e.g. 'UserService.createUser') to file:line:col.

    Returns (relative_path, line, col) or None if not found.
    """
    # Step 1: Find the class via workspace/symbol
    symbols = query(project_dir, "workspace_symbol", {"query": class_name})
    if not symbols:
        return None

    # Find best match (exact name match preferred)
    target = None
    for sym in symbols:
        if sym.get("name") == class_name.split(".")[-1]:
            target = sym
            break
    if target is None:
        target = symbols[0]

    uri = target.get("location", {}).get("uri", "")
    rel_path = uri.replace(f"file://{os.path.abspath(project_dir)}/", "")

    if method_name is None:
        line = target["location"]["range"]["start"]["line"]
        col = target["location"]["range"]["start"]["character"]
        return rel_path, line, col

    # Step 2: Find the method within the class file via document_symbols
    doc_symbols = query(project_dir, "document_symbols", {"file": rel_path})
    # doc_symbols is a list of lists (nested)
    for sym in _flatten_symbols(doc_symbols):
        name = sym.get("name", "")
        # Match method name (e.g. "createUser" matches "createUser(String, String)")
        if name == method_name or name.startswith(method_name + "("):
            line = sym["selectionRange"]["start"]["line"]
            col = sym["selectionRange"]["start"]["character"]
            return rel_path, line, col

    return None


def _flatten_symbols(symbols: list) -> list:
    """Flatten nested document symbol structure from multilspy."""
    result = []
    for item in symbols:
        if isinstance(item, list):
            result.extend(_flatten_symbols(item))
        elif isinstance(item, dict):
            result.append(item)
            if "children" in item:
                result.extend(_flatten_symbols(item["children"]))
    return result
