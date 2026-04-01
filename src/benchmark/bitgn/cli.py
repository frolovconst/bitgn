from __future__ import annotations

import argparse

from .config import BitgnRunConfig
from .runner import run_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Columbarium BitGN baseline agent against a benchmark."
    )
    parser.add_argument(
        "task_ids",
        nargs="*",
        help="Optional BitGN task ids to run instead of the full benchmark.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = BitgnRunConfig.from_env(task_ids=args.task_ids)
    return run_benchmark(config)


if __name__ == "__main__":
    raise SystemExit(main())
