"""Verify public artifacts, provenance, notebook syntax, links and publication hygiene."""

import argparse
import ast
import csv
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

import yaml

from tsfm_crossover.analysis.public_results import analyze, compare_paper, digest, load_conditions

CURRENT_DOCS = [
    "README.md",
    "README.en.md",
    "docs/reproducibility.md",
    "docs/final-protocol.md",
    "docs/data-preparation.md",
    "docs/public-result-schema.md",
    "docs/versions.md",
    "docs/deployment.md",
    "docs/verification.md",
    "docs/provenance.md",
    "scripts/README.md",
    "notebooks/README.md",
    "requirements/README.md",
    "spaces/README.md",
]


def verify(root):
    rows = load_conditions(root / "results/public/conditions.csv")
    comparison = compare_paper(
        analyze(rows), json.loads((root / "docs/paper-reference.json").read_text(encoding="utf-8"))
    )
    if not comparison["all_match"]:
        raise ValueError("paper table comparison failed; inspect differences")
    provenance = json.loads((root / "results/public/provenance.json").read_text(encoding="utf-8"))
    for name, expected in provenance["files"].items():
        if digest(root / "results/public" / name) != expected:
            raise ValueError(f"public source checksum: {name}")
    # Bind every exported NMAE/step/identity to the already-pinned compact review.
    reviews = {}
    for family in ("ttm", "moirai1"):
        path = root / f"results/manifests/study/primary5_h96_{family}_review.json"
        for record in json.loads(path.read_text(encoding="utf-8"))["conditions"]:
            reviews[record["identity"]["condition"]["id"]] = record
    for row in rows:
        original = reviews[row["condition_id"]]
        if row["nmae"] != original["test_metrics"]["normalized_mae"]:
            raise ValueError("export changed original metric precision")
        if int(row["actual_optimizer_steps"]) != original["actual_optimizer_steps"]:
            raise ValueError("export changed training steps")
        if row["source_record_hash"] != original["record_hash"]:
            raise ValueError("source record hash mismatch")
    link_count, broken = 0, []
    for name in CURRENT_DOCS:
        path = root / name
        for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            target = match[1].strip("<>")
            if "://" in target or target.startswith("#"):
                continue
            target = unquote(target.split("#")[0])
            if not target:
                continue
            link_count += 1
            if not (path.parent / target).exists():
                broken.append({"document": name, "target": target})
    if broken:
        raise ValueError(f"broken current-document links: {broken}")
    notebook_cells = 0
    for name in ("50_results_analysis.ipynb", "51_minimal_ttm_etth1.ipynb"):
        doc = json.loads((root / "notebooks" / name).read_text(encoding="utf-8"))
        for cell in doc["cells"]:
            if cell["cell_type"] == "code":
                ast.parse("".join(cell["source"]))
                if cell["outputs"] or cell["execution_count"] is not None:
                    raise ValueError("notebook contains saved machine output")
                notebook_cells += 1
    cff = yaml.safe_load((root / "CITATION.cff").read_text(encoding="utf-8"))
    if cff["cff-version"] != "1.2.0" or cff["type"] != "software":
        raise ValueError("invalid software citation metadata")
    # Scan tracked + not-ignored new text; never inspect or print ignored credential files.
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).splitlines()
    personal = re.compile(
        r"""(?:[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s"']+|/(?:Users|home)/[^/\s"']+)"""
    )
    credential = re.compile(
        r"(?:hf_"
        + r"[A-Za-z0-9]{20,}|gh[pousr]_"
        + r"[A-Za-z0-9]{25,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)"
    )
    privacy_hits = []
    scanned = 0
    suffixes = {
        ".py",
        ".md",
        ".json",
        ".csv",
        ".yaml",
        ".yml",
        ".ipynb",
        ".txt",
        ".toml",
        ".cff",
        ".html",
        ".svg",
    }
    for name in names:
        path = root / name
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        scanned += 1
        if personal.search(text) or credential.search(text):
            privacy_hits.append(name)
    if privacy_hits:
        raise ValueError(f"publication hygiene requires review: {privacy_hits}")
    # Retained research source must remain byte-identical; obsolete modules may be removed.
    modified = subprocess.check_output(
        ["git", "diff", "--diff-filter=M", "--name-only", "4840fbf", "--", "src/tsfm_crossover"],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).splitlines()
    if modified:
        raise ValueError(f"existing research implementation changed: {modified}")
    with (root / "results/paper/table1.csv").open(encoding="utf-8", newline="") as stream:
        table1_rows = len(list(csv.DictReader(stream)))
    return {
        "status": "passed",
        "conditions": len(rows),
        "pdf_comparisons": len(comparison["checks"]),
        "pdf_all_match": comparison["all_match"],
        "table1_rows": table1_rows,
        "internal_links_checked": link_count,
        "broken_links": broken,
        "notebook_code_cells_parsed": notebook_cells,
        "text_files_privacy_scanned": scanned,
        "privacy_hits": privacy_hits,
        "existing_research_source_changed": modified,
        "raw_prediction_recomputation": False,
        "new_gpu_execution": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(Path.cwd())
    print(json.dumps(result, ensure_ascii=False))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
