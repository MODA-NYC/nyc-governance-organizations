#!/usr/bin/env python3
import subprocess
from datetime import datetime, timezone


def main():
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H-%MZ")
    try:
        git_sha = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], timeout=5)
            .decode("utf-8")
            .strip()
        )
    except Exception:
        git_sha = "nogit"
    print(f"{ts}_{git_sha}")


if __name__ == "__main__":
    main()
