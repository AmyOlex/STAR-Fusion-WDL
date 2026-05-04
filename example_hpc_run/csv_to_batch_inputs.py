#!/usr/bin/env python3
"""
Convert a CSV sample sheet to a Cromwell batch inputs JSON file.

Usage:
  python csv_to_batch_inputs.py sample_sheet.csv --config batch_config.json --output batch_inputs.json

The CSV must have columns: sample_id, left_fq, right_fq
(header row required)

The config JSON provides shared parameters that are the same for all samples.
See batch_config_TEMPLATE.json for the format.
"""

import csv
import json
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Convert CSV sample sheet to Cromwell batch inputs JSON")
    parser.add_argument("csv_file", help="Path to CSV sample sheet (columns: sample_id, left_fq, right_fq)")
    parser.add_argument("--config", required=True, help="Path to shared config JSON (non-sample-specific parameters)")
    parser.add_argument("--output", default="batch_inputs.json", help="Output JSON filename (default: batch_inputs.json)")
    args = parser.parse_args()

    # Read CSV
    sample_ids = []
    left_fqs = []
    right_fqs = []

    with open(args.csv_file, "r") as f:
        reader = csv.DictReader(f)

        # Validate columns
        required_cols = {"sample_id", "left_fq", "right_fq"}
        if not required_cols.issubset(set(reader.fieldnames)):
            missing = required_cols - set(reader.fieldnames)
            print(f"ERROR: CSV missing required columns: {missing}", file=sys.stderr)
            print(f"Found columns: {reader.fieldnames}", file=sys.stderr)
            sys.exit(1)

        for row in reader:
            sample_ids.append(row["sample_id"].strip())
            left_fqs.append(row["left_fq"].strip())
            right_fqs.append(row["right_fq"].strip())

    if len(sample_ids) == 0:
        print("ERROR: No samples found in CSV", file=sys.stderr)
        sys.exit(1)

    # Read shared config
    with open(args.config, "r") as f:
        shared_config = json.load(f)

    # Build batch inputs
    prefix = "star_fusion_hg38_batch_hpc_wf"
    batch_inputs = {
        f"{prefix}.sample_ids": sample_ids,
        f"{prefix}.left_fqs": left_fqs,
        f"{prefix}.right_fqs": right_fqs,
    }

    # Add shared config (already prefixed in the config file)
    batch_inputs.update(shared_config)

    # Write output
    with open(args.output, "w") as f:
        json.dump(batch_inputs, f, indent=2)

    print(f"Generated {args.output} with {len(sample_ids)} samples")

if __name__ == "__main__":
    main()
