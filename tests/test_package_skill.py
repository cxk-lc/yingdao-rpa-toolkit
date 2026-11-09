# -*- coding: utf-8 -*-
"""发布包只包含 Skill 运行所需文件。"""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_package_skill_is_lean(tmp_path):
    output = tmp_path / "yingdao-rpa-toolkit.zip"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "package_skill.py"),
            "--ref",
            "HEAD",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(output) as archive:
        names = [
            name.split("yingdao-rpa-toolkit/", 1)[1]
            for name in archive.namelist()
            if "yingdao-rpa-toolkit/" in name and not name.endswith("/")
        ]

    relative = set(names)
    assert "SKILL.md" in relative
    assert "scripts/yd.py" in relative
    assert "references/auth.md" in relative
    assert "config.example.json" in relative

    top_level = {name.split("/")[0] for name in relative}
    assert top_level == {
        "SKILL.md",
        "LICENSE",
        "config.example.json",
        ".env.example",
        "requirements.txt",
        "scripts",
        "references",
    }

    for forbidden in (
        "README.md",
        "USAGE.md",
        "AGENTS.md",
        "pyproject.toml",
        "requirements-dev.txt",
        ".gitignore",
        "影刀RPA开放API接口文档.md",
    ):
        assert forbidden not in relative
    assert not any(name.startswith(("docs/", "tests/", "tools/")) for name in relative)
    assert not any(name.endswith(".pyc") or "__pycache__" in name for name in relative)
