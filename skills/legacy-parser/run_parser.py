#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path.home() / "csce465-agentsec" / "hw3"
INBOX = BASE / "inbox"
PARSER = BASE / "legacy_log_parser"
AUDIT = BASE / "task2-evidence" / "parser-invocations.jsonl"


def log_event(event):
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    event["timestamp"] = datetime.now(timezone.utc).isoformat()

    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: run_parser.py <file-path>", file=sys.stderr)
        return 2

    requested = sys.argv[1]

    try:
        root = INBOX.resolve(strict=True)
        target = Path(os.path.expanduser(requested)).resolve(strict=True)

        if not target.is_relative_to(root) or target == root:
            raise PermissionError("File must be inside inbox/")

        if not target.is_file():
            raise ValueError("Target must be a regular file")

    except (OSError, ValueError) as exc:
        log_event({
            "requested": requested,
            "decision": "BLOCKED",
            "reason": str(exc)
        })

        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    log_event({
        "requested": requested,
        "resolved": str(target),
        "decision": "ALLOWED"
    })

    try:
        result = subprocess.run(
            [str(PARSER), str(target)],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=10,
            shell=False,
        )

        print(result.stdout, end="")

        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)

        print(f"\nPARSER_EXIT_CODE={result.returncode}")

        log_event({
            "resolved": str(target),
            "decision": "EXECUTED",
            "exit_code": result.returncode
        })

        return 0 if result.returncode == 0 else 1

    except subprocess.TimeoutExpired:
        log_event({
            "resolved": str(target),
            "decision": "TIMEOUT"
        })
        print("Parser timed out", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
