"""CLI entrypoint for generating synthetic financial reconciliation datasets."""

import argparse
import sys
import time
from pathlib import Path

# Ensure backend package is on sys.path
backend_path = Path(__file__).resolve().parents[2] / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.domain.sanitization import DatasetIdValidationError, validate_dataset_id
from app.services.data_generator import (
    SyntheticFinancialGenerator,
    export_dataset,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic financial datasets with isolated ground truth."
    )
    parser.add_argument(
        "--size",
        type=int,
        default=500,
        help="Number of logical transactions (default: 500)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default="dev_500",
        help="Dataset identifier (default: dev_500)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=None, help="Base data output directory"
    )

    args = parser.parse_args()

    try:
        validated_dataset_id = validate_dataset_id(args.dataset_id)
    except DatasetIdValidationError as e:
        print(f"Error: Invalid --dataset-id: {e}", file=sys.stderr)
        sys.exit(1)

    print("=== METFI Synthetic Data Generator ===")
    print(f"Dataset ID : {validated_dataset_id}")
    print(f"Size       : {args.size} transactions")
    print(f"Seed       : {args.seed}")

    start_time = time.perf_counter()
    generator = SyntheticFinancialGenerator(seed=args.seed)
    result = generator.generate(size=args.size, dataset_id=args.dataset_id)
    gen_time = time.perf_counter() - start_time

    export_paths = export_dataset(result, base_dir=args.output_dir)
    total_time = time.perf_counter() - start_time

    print(
        f"\nGeneration completed in {gen_time:.4f}s ({args.size / gen_time:.1f} rec/s)"
    )
    print(f"Total time with disk serialization: {total_time:.4f}s")
    print("\nExported Files:")
    print(f"  Payments       : {export_paths['payments']}")
    print(f"  Settlements    : {export_paths['settlements']}")
    print(f"  Ledger         : {export_paths['ledger']}")
    print(f"  Input Manifest : {export_paths['input_manifest']}")
    print(f"  Ground Truth   : {export_paths['ground_truth']}")
    print(f"  GT Manifest    : {export_paths['gt_manifest']}")

    print("\nClass Distribution:")
    for cls_name, count in result.manifest.class_distribution.items():
        pct = (count / args.size) * 100
        print(f"  {cls_name:<22} : {count:>5} ({pct:>5.1f}%)")


if __name__ == "__main__":
    main()
