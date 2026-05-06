from __future__ import annotations

import argparse

import uvicorn

from .server import build_app


def main() -> None:
    parser = argparse.ArgumentParser(prog="redmine-mcp")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()
    uvicorn.run(build_app(), host=args.host, port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
