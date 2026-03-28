"""Daemon subprocess — starts jdtls and serves queries over a socket.

Launched by server.py:start_daemon(). Not meant to be run directly.
"""

import json
import os
import signal
import socketserver
import sys
import threading

from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger

from java_nav.classpath import CACHE_DIR


class QueryHandler(socketserver.StreamRequestHandler):
    """Handle one JSON query from the client."""

    def handle(self):
        try:
            raw = self.rfile.readline().decode().strip()
            if not raw:
                return
            request = json.loads(raw)
            method = request["method"]
            params = request.get("params", {})

            lsp = self.server.lsp  # type: ignore[attr-defined]
            if method == "references":
                result = lsp.request_references(params["file"], params["line"], params["col"])
            elif method == "definition":
                result = lsp.request_definition(params["file"], params["line"], params["col"])
            elif method == "document_symbols":
                result = lsp.request_document_symbols(params["file"])
            elif method == "hover":
                result = lsp.request_hover(params["file"], params["line"], params["col"])
            elif method == "workspace_symbol":
                result = lsp.request_workspace_symbol(params["query"])
            elif method == "shutdown":
                self.wfile.write(json.dumps({"ok": True}).encode() + b"\n")
                threading.Thread(target=self.server.shutdown).start()
                return
            else:
                result = {"error": f"Unknown method: {method}"}

            self.wfile.write(json.dumps(result, default=str).encode() + b"\n")
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode() + b"\n")


def main():
    project_dir = sys.argv[1]
    state_dir = os.path.join(project_dir, CACHE_DIR)

    logger = MultilspyLogger()
    config = MultilspyConfig.from_dict({"code_language": "java"})
    lsp = SyncLanguageServer.create(config, logger, project_dir)

    with lsp.start_server():
        server = socketserver.TCPServer(("127.0.0.1", 0), QueryHandler)
        server.lsp = lsp  # type: ignore[attr-defined]
        port = server.server_address[1]

        # Signal readiness by writing port file
        os.makedirs(state_dir, exist_ok=True)
        port_path = os.path.join(state_dir, "jdtls.port")
        with open(port_path, "w") as f:
            f.write(str(port))

        def cleanup(signum, frame):
            server.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGTERM, cleanup)
        signal.signal(signal.SIGINT, cleanup)

        server.serve_forever()


if __name__ == "__main__":
    main()
