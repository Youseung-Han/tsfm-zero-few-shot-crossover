"""Prepare an auditable CPU Space folder. Does not upload or publish."""

import argparse
import re
import shutil
from pathlib import Path
from urllib.parse import unquote

from tsfm_crossover.analysis.public_results import digest, write_json


def package(root, output):
    output.mkdir(parents=True, exist_ok=False)
    paths = [
        "app.py",
        "pyproject.toml",
        "requirements.txt",
        "CITATION.cff",
        "src/tsfm_crossover/__init__.py",
        "src/tsfm_crossover/analysis/__init__.py",
        "src/tsfm_crossover/analysis/public_results.py",
        "docs/deployment.md",
        "docs/public-result-schema.md",
        "docs/reproducibility.md",
        "docs/final-protocol.md",
        "docs/versions.md",
    ]
    paths += [
        p.relative_to(root).as_posix()
        for p in sorted((root / "results/public").glob("*"))
        if p.is_file()
    ]
    for name in paths:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
    # Keep the runtime small while making references to full-repository files usable.
    for path in (output / "docs").glob("*.md"):

        def resolve_link(match, path=path):
            target = match[2]
            if "://" in target or target.startswith("#"):
                return match[0]
            relative = (path.parent / unquote(target.split("#")[0])).resolve()
            if relative.exists():
                return match[0]
            source = relative.relative_to(output.resolve()).as_posix()
            url = f"https://github.com/Han-Youseung/tsfm-zero-few-shot-crossover/blob/main/{source}"
            return f"[{match[1]}]({url})"

        path.write_text(
            re.sub(r"\[([^\]]*)\]\(([^)]+)\)", resolve_link, path.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
    shutil.copyfile(root / "spaces/README.md", output / "README.md")
    write_json(
        output / "bundle-manifest.json",
        {
            "kind": "saved_results_cpu_space",
            "uploaded": False,
            "license_decision": "required before public distribution",
            "files": {
                p.relative_to(output).as_posix(): digest(p)
                for p in sorted(output.rglob("*"))
                if p.is_file()
            },
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package(Path.cwd(), args.output)
