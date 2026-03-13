from __future__ import annotations

from mcp_server import create_server

mcp = create_server()


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
