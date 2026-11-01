"""Export reviewed original metrics from the preserved paper kit, never PDF numbers."""

import argparse
import json
import zipfile
from pathlib import Path

from tsfm_crossover.analysis.paper import digest, load_scope, validate_records
from tsfm_crossover.analysis.public_results import write_csv, write_json
from tsfm_crossover.experiments.main_review import compact_result


def export(kit, output):
    root = Path.cwd()
    scope = load_scope(root / "configs/analysis/primary5_h96.yaml")
    with zipfile.ZipFile(kit) as archive:
        hashes = json.loads(archive.read("SHA256SUMS.json"))
        import hashlib

        missing = sorted(set(hashes) - set(archive.namelist()))
        # The local kit has one missing editorial checklist. Scientific evidence
        # must still be present and checked; preserve and report the damaged kit.
        if set(missing) - {"claims_and_checklist.txt"}:
            raise ValueError(f"missing kit members: {missing}")
        for name, expected in hashes.items():
            if name in missing:
                continue
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError(f"kit member checksum mismatch: {name}")
        records = json.loads(archive.read("evidence/final_results.json"))
        validate_records(records, scope)
        canonical = {}
        for ref in scope["reviews"]:
            path = root / ref["path"]
            if digest(path) != ref["sha256"]:
                raise ValueError("pinned review checksum mismatch")
            for row in json.loads(path.read_text(encoding="utf-8"))["conditions"]:
                canonical[row["identity"]["condition"]["id"]] = row
        rows, settings = [], {}
        for index, record in enumerate(records):
            identity = record["identity"]
            c = identity["condition"]
            review = canonical[c["id"]]
            if compact_result(record) != review:
                raise ValueError(f"raw record differs from canonical review: {c['id']}")
            training, provenance = record["training"], record["provenance"]
            rows.append(
                {
                    "condition_id": c["id"],
                    "model": c["family"],
                    "dataset": c["dataset"],
                    "rate": c["rate"],
                    "seed": c["seed"],
                    "context": 512,
                    "horizon": c["horizon"],
                    "status": record["status"],
                    "nmae": record["test"]["metrics"]["macro"]["normalized_mae"],
                    "actual_optimizer_steps": training["actual_optimizer_steps"],
                    "best_validation_step": training.get("best_validation_step"),
                    "stopping_step": training.get("stopping_step"),
                    "selected_train_windows": provenance["selected_train_windows"],
                    "total_train_windows": provenance["total_train_windows"],
                    "test_windows": record["test"]["number_of_test_windows"],
                    "execution_commit": identity["commit"],
                    "protocol_hash": identity["protocol_hash"],
                    "data_sha256": identity["data_sha256"],
                    "test_window_hash": record["test"]["window_hash"],
                    "sampling_manifest_hash": provenance["sampling_manifest_hash"],
                    "runtime_hash": record["runtime_hash"],
                    "gpu": record["runtime"]["gpu"],
                    "source_review": (
                        f"results/manifests/study/primary5_h96_{c['family']}_review.json"
                    ),
                    "source_member": f"evidence/final_results.json#/{index}",
                    "source_result_path": f"{c['id']}/result.json",
                    "source_record_hash": review["record_hash"],
                    "model_revision": identity["model_pin"]["revision"],
                }
            )
            settings[c["family"]] = {
                "model_pin": identity["model_pin"],
                "adapter_settings": {
                    k: v
                    for k, v in record["adapter_settings"].items()
                    if k
                    not in {
                        "condition_id",
                        "dataset_fingerprint",
                        "sampling_manifest_hash",
                        "channel_names",
                        "training_seed",
                        "prediction_seed",
                    }
                },
            }
        output.mkdir(parents=True, exist_ok=False)
        write_csv(output / "conditions.csv", sorted(rows, key=lambda r: r["condition_id"]))
        write_json(output / "model_settings.json", settings)
        # Runtime records contain package versions, no machine paths or credentials.
        environments = {r["runtime_hash"]: r["runtime"] for r in records}
        write_json(output / "environments.json", environments)
        write_json(
            output / "source_archive_hashes.json",
            json.loads(archive.read("evidence/source_archive_hashes.json")),
        )
        write_json(
            output / "provenance.json",
            {
                "schema_version": 1,
                "source": "reviewed raw result JSONs in preserved writing kit",
                "source_kit_name": kit.name,
                "source_kit_sha256": digest(kit),
                "source_member_sha256": hashes["evidence/final_results.json"],
                "kit_missing_editorial_members": missing,
                "conditions": len(records),
                "execution_commit": scope["execution_commit"],
                "checks": [
                    "kit member checksums",
                    "pinned canonical review checksums",
                    "raw records equal canonical compact records",
                    "paired data/windows/sampling",
                ],
                "original_execution_archives_reopened": False,
                "prediction_arrays_recomputed": False,
                "new_gpu_execution": False,
                "files": {p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()},
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    export(args.kit, args.output)
