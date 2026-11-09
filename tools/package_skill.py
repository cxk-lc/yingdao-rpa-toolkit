# -*- coding: utf-8 -*-
"""构建精简的 Skill 发布包。

只打包 Skill 运行所需文件，避免把 tests/docs/AGENTS 等仓库文件带进 Release。
用法：
    python tools/package_skill.py --ref v0.1.1 --output .workbuddy/dist/yingdao-rpa-toolkit-v0.1.1.zip
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

ALLOWLIST = (
    "SKILL.md",
    "LICENSE",
    "config.example.json",
    ".env.example",
    "requirements.txt",
    "scripts",
    "references",
)
FORBIDDEN_NAMES = {
    "README.md",
    "USAGE.md",
    "AGENTS.md",
    "pyproject.toml",
    "requirements-dev.txt",
    ".gitignore",
    "影刀RPA开放API接口文档.md",
}
FORBIDDEN_DIRS = {
    "docs",
    "tests",
    "tools",
    ".git",
    ".github",
    ".workbuddy",
    ".yingdao",
    "__pycache__",
}
REQUIRED = {
    "SKILL.md",
    "LICENSE",
    "config.example.json",
    ".env.example",
    "requirements.txt",
    "scripts/yd.py",
    "references/auth.md",
}


def _fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def _relative_entries(zip_path: Path, prefix: str) -> list[str]:
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
    root = prefix.rstrip("/") + "/"
    return [name[len(root):] for name in names if name.startswith(root) and not name.endswith("/")]


def _verify(zip_path: Path, prefix: str) -> list[str]:
    entries = _relative_entries(zip_path, prefix)
    missing = sorted(REQUIRED - set(entries))
    if missing:
        _fail("缺少必需文件：" + "、".join(missing))

    bad: list[str] = []
    for entry in entries:
        parts = entry.split("/")
        if parts[0] in FORBIDDEN_DIRS:
            bad.append(entry)
        elif entry in FORBIDDEN_NAMES:
            bad.append(entry)
        elif entry == ".env" or entry.startswith(".env/"):
            bad.append(entry)
        elif entry.endswith(".pyc") or "__pycache__" in parts:
            bad.append(entry)

    if bad:
        _fail("包含不允许的文件：" + "、".join(sorted(bad)))

    top_levels = {entry.split("/")[0] for entry in entries}
    extra = sorted(top_levels - set(ALLOWLIST))
    if extra:
        _fail("包含白名单之外的顶层项：" + "、".join(extra))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="构建精简的 Skill 发布包")
    parser.add_argument("--ref", default="HEAD", help="Git ref，默认 HEAD")
    parser.add_argument("--output", required=True, help="输出 zip 路径")
    parser.add_argument("--prefix", default="yingdao-rpa-toolkit", help="压缩包顶层目录名")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    command = [
        "git",
        "archive",
        "--format=zip",
        f"--prefix={args.prefix.rstrip('/')}/",
        "-o",
        str(output),
        args.ref,
        "--",
        *ALLOWLIST,
    ]
    print("+ " + " ".join(command))
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        _fail(f"git archive 失败（退出码 {exc.returncode}）")

    entries = _verify(output, args.prefix)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"entries={len(entries)} size={output.stat().st_size} sha256={digest}")
    print(f"output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
