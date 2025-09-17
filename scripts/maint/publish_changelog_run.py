#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path


def run_cmd(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Publish a changelog run: review → append → optional commit/tag/release"
        )
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--auto-approve", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--tag", type=str)
    parser.add_argument("--release", action="store_true")
    parser.add_argument(
        "--operator", type=str, default=os.environ.get("USER", "system")
    )
    parser.add_argument("--changelog", type=Path, default=Path("data/changelog.csv"))
    return parser.parse_args()


def run_review(run_dir: Path, auto_approve: bool) -> int:
    cmd = [
        "python",
        "scripts/maint/review_changes.py",
        "--run-dir",
        str(run_dir),
    ]
    # auto-approve is default; flag kept for explicitness
    return run_cmd(cmd)


def run_append(run_dir: Path, changelog: Path, operator: str) -> int:
    cmd = [
        "python",
        "scripts/maint/append_changelog.py",
        "--run-dir",
        str(run_dir),
        "--changelog",
        str(changelog),
        "--operator",
        operator,
    ]
    return run_cmd(cmd)


def read_appended_count(run_dir: Path) -> int:
    summary_path = run_dir / "run_summary.json"
    if not summary_path.exists():
        return 0
    try:
        summary = json.loads(summary_path.read_text())
        return int(summary.get("counts", {}).get("appended", 0))
    except Exception:
        return 0


def do_commit(changelog: Path, appended: int, run_dir: Path) -> int:
    if run_cmd(["git", "add", str(changelog)]) != 0:
        return 1
    msg = f"chore(changelog): append {appended} changes from {run_dir.name}"
    return run_cmd(["git", "commit", "-m", msg])


def do_tag(tag: str) -> int:
    return run_cmd(["git", "tag", tag])


def do_release(tag: str, run_dir: Path) -> int:
    if not os.environ.get("GH_TOKEN"):
        print("GH_TOKEN not set; skipping GitHub release.")
        return 0
    return run_cmd(
        [
            "gh",
            "release",
            "create",
            tag,
            "--notes",
            f"NYC GO pipeline release for {run_dir.name}",
        ]
    )


def finalize(
    apply: bool,
    do_commit_flag: bool,
    tag: str | None,
    do_release_flag: bool,
    changelog: Path,
    appended: int,
    run_dir: Path,
) -> int:
    if not apply:
        print("Dry-run: not committing/tagging. Next steps:")
        print(f"- Review {run_dir}/reviewed_changes.csv")
        print(
            "- Re-run with --apply (and optionally --commit --tag vX.Y.Z --release) "
            "when satisfied."
        )
        return 0

    if appended == 0:
        print("Nothing to append. Exiting with code 2 as --apply was set.")
        return 2

    if do_commit_flag:
        if do_commit(changelog, appended, run_dir) != 0:
            return 1

    if tag:
        if do_tag(tag) != 0:
            return 1

    if do_release_flag and tag:
        if do_release(tag, run_dir) != 0:
            return 1

    return 0


def main() -> int:
    args = parse_args()

    run_dir = args.run_dir
    proposed = run_dir / "proposed_changes.csv"
    if not proposed.exists():
        print(f"Error: not found {proposed}. Prepare proposed changes first.")
        return 2

    if run_review(run_dir, args.auto_approve) != 0:
        print("Review step failed.")
        return 1

    if run_append(run_dir, args.changelog, args.operator) != 0:
        print("Append step failed.")
        return 1

    appended = read_appended_count(run_dir)

    print(f"Appended {appended} rows from {run_dir.name}.")

    return finalize(
        apply=args.apply,
        do_commit_flag=args.commit,
        tag=args.tag,
        do_release_flag=args.release,
        changelog=args.changelog,
        appended=appended,
        run_dir=run_dir,
    )


if __name__ == "__main__":
    raise SystemExit(main())
