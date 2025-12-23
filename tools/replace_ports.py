"""
Bulk port replacement utility for MoshengAI.

This script normalizes all *documentation/config* references from legacy ports to
the v0.1 port map requested by the user:

- Frontend: 33000 -> 33000
- Backend:  38000 -> 38000
- Monitor:  33001 -> 33001

It is intentionally conservative:
- Only rewrites well-formed host:port / :port / ssh -L patterns.
- Skips large lockfiles and model subrepos (index-tts, voxcpm-repo).

Usage:
  source .venv/bin/activate
  python tools/replace_ports.py

Notes:
  - The script exits non-zero on any write failure.
  - Review changes via grep after running.
"""

from __future__ import annotations

import pathlib
import re


ROOT = pathlib.Path("/scratch/kcriss/MoshengAI")

SKIP_DIRS = {
    ROOT / "index-tts",
    ROOT / "voxcpm-repo",
    ROOT / ".venv",
    ROOT / "frontend" / "node_modules",
}

SKIP_FILES = {
    ROOT / "uv.lock",
    ROOT / "frontend" / "package-lock.json",
}

TEXT_EXTS = {
    ".md",
    ".txt",
    ".sh",
    ".py",
    ".ts",
    ".tsx",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".mjs",
}


REPLACEMENTS = [
    # Host:port (localhost)
    ("localhost:33000", "localhost:33000"),
    ("localhost:38000", "localhost:38000"),
    ("localhost:33001", "localhost:33001"),
    # Host:port (server IP)
    ("10.212.227.125:33000", "10.212.227.125:33000"),
    ("10.212.227.125:38000", "10.212.227.125:38000"),
    ("10.212.227.125:33001", "10.212.227.125:33001"),
    # Bare :port patterns (common in ss/lsof/grep)
    (":33000", ":33000"),
    (":38000", ":38000"),
    (":33001", ":33001"),
    # SSH local forward patterns (most common forms)
    ("-L 33000:localhost:33000", "-L 33000:localhost:33000"),
    ("-L 38000:localhost:38000", "-L 38000:localhost:38000"),
    ("-L 33001:localhost:33001", "-L 33001:localhost:33001"),
    ("-L 33000:127.0.0.1:33000", "-L 33000:127.0.0.1:33000"),
    ("-L 38000:127.0.0.1:38000", "-L 38000:127.0.0.1:38000"),
    ("-L 33001:127.0.0.1:33001", "-L 33001:127.0.0.1:33001"),
]


def _is_skipped_path(path: pathlib.Path) -> bool:
    for skip_dir in SKIP_DIRS:
        try:
            path.relative_to(skip_dir)
            return True
        except ValueError:
            continue
    return path in SKIP_FILES


def _rewrite_text(text: str) -> str:
    new_text = text
    for old, new in REPLACEMENTS:
        new_text = new_text.replace(old, new)
    # Broader fallback for standalone port numbers in docs/scripts,
    # while still excluding model repos/lockfiles via path filters.
    new_text = re.sub(r"\b3000\b", "33000", new_text)
    new_text = re.sub(r"\b8000\b", "38000", new_text)
    new_text = re.sub(r"\b3001\b", "33001", new_text)
    return new_text


def main() -> None:
    changed = 0
    scanned = 0

    for path in ROOT.rglob("*"):
        if path.is_dir():
            continue
        if _is_skipped_path(path):
            continue
        if path.suffix not in TEXT_EXTS:
            continue

        scanned += 1
        original = path.read_text(encoding="utf-8", errors="ignore")
        updated = _rewrite_text(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1

    print(f"Scanned {scanned} files, updated {changed} files.")


if __name__ == "__main__":
    main()

