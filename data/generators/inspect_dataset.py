"""Developer inspection tool for generated datasets and isolated ground truth."""

import argparse
import json
from pathlib import Path
import sys


def inspect(dataset_id: str, base_dir: Path | str | None = None) -> None:
    root_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parents[2] / "data"
    input_dir = root_dir / "generated" / dataset_id / "input"
    gt_dir = root_dir / "ground_truth" / dataset_id

    if not input_dir.exists():
        print(f"Error: Input directory for dataset '{dataset_id}' not found at: {input_dir}")
        sys.exit(1)

    print(f"\n=======================================================")
    print(f"       METFI DATASET INSPECTOR — {dataset_id}")
    print(f"=======================================================")

    # 1. Inspect Input Manifest
    input_manifest_file = input_dir / "manifest.json"
    if input_manifest_file.exists():
        with open(input_manifest_file, "r", encoding="utf-8") as f:
            in_manifest = json.load(f)
        print(f"\n[INFERENCE INPUT MANIFEST]")
        print(f"  Dataset ID        : {in_manifest.get('dataset_id')}")
        print(f"  Generator Version : {in_manifest.get('generator_version')}")
        print(f"  Schema Version    : {in_manifest.get('schema_version')}")
        print(f"  Random Seed       : {in_manifest.get('seed')}")
        print(f"  Record Count      : {in_manifest.get('record_count')}")
        print(f"  Source Counts     : {in_manifest.get('source_counts')}")

    # 2. Source Record Counts
    for source in ["payments", "settlements", "ledger"]:
        src_file = input_dir / f"{source}.json"
        if src_file.exists():
            with open(src_file, "r", encoding="utf-8") as f:
                records = json.load(f)
            print(f"  {source.capitalize():<18}: {len(records)} records ({src_file.stat().st_size / 1024:.1f} KB)")

    # 3. Inspect Ground Truth Manifest
    gt_manifest_file = gt_dir / "manifest.json"
    if gt_manifest_file.exists():
        with open(gt_manifest_file, "r", encoding="utf-8") as f:
            gt_manifest = json.load(f)
        print(f"\n[ISOLATED GROUND TRUTH MANIFEST]")
        print(f"  Class Distribution:")
        dist = gt_manifest.get("class_distribution", {})
        total = sum(dist.values())
        for cls_name, count in dist.items():
            pct = (count / total * 100) if total else 0
            print(f"    - {cls_name:<22}: {count:>5} ({pct:>5.1f}%)")

        print(f"\n  File Checksums (SHA256):")
        for k, v in gt_manifest.get("checksums", {}).items():
            print(f"    - {k:<22}: {v}")

    # 4. Sample Record Inspection
    gt_file = gt_dir / "ground_truth.json"
    if gt_file.exists():
        with open(gt_file, "r", encoding="utf-8") as f:
            gt_records = json.load(f)
        print(f"\n[SAMPLE GROUND TRUTH RECORDS (First 3)]")
        for sample in gt_records[:3]:
            print(f"  Case ID: {sample.get('case_id')} | Order: {sample.get('order_id')}")
            print(f"    Expected Class : {sample.get('expected_classification')}")
            print(f"    Expected Policy: {sample.get('expected_policy_outcome')}")
            if sample.get("injected_fault"):
                print(f"    Fault Info     : {sample['injected_fault'].get('description')}")
            print()

    print(f"=======================================================\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect generated METFI dataset and ground truth.")
    parser.add_argument("--dataset-id", type=str, default="dev_500", help="Dataset identifier to inspect")
    parser.add_argument("--base-dir", type=str, default=None, help="Base data directory")
    args = parser.parse_args()

    inspect(args.dataset_id, base_dir=args.base_dir)


if __name__ == "__main__":
    main()
