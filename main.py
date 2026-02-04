from __future__ import annotations

from mcp_app import create_server


def main() -> None:
    server = create_server()
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
