#!/usr/bin/env python3
"""
Recover results from a Cromwell batch run where some samples succeeded
but the gather step did not complete.

This script walks the Cromwell execution tree, identifies which samples
completed successfully, copies their output files to the configured
output directory, and generates a report of failed samples.

Usage:
  python recover_batch_results.py \
    --config batch_config.json \
    --exec-dir cromwell-executions \
    --keep-bam-and-junction   (optional, default: false)

The output directory is read from the batch_config.json file.
A failed_samples_report.tsv is saved in the current working directory.
"""

import argparse
import glob
import json
import os
import shutil
import sys
from datetime import datetime


def find_sample_executions(exec_dir):
    """
    Walk the Cromwell execution tree to find per-sample execution directories.
    Returns a dict of {sample_id: execution_path}.
    """
    samples = {}

    # The batch WDL scatters, creating shard directories.
    # Structure: cromwell-executions/<batch_wf>/<hash>/call-per_sample/
    #   shard-N/<hpc_wf>/<hash>/call-star_fusion_hg38/<sub_wf>/<hash>/
    #   call-star_fusion/execution/

    # Find all star_fusion execution dirs by looking for the script file
    script_files = glob.glob(
        os.path.join(exec_dir, "**", "call-star_fusion", "execution", "script"),
        recursive=True
    )

    for script_path in script_files:
        exec_path = os.path.dirname(script_path)

        # Extract sample_id from the script file
        try:
            with open(script_path, "r") as f:
                script_content = f.read()

            # The script contains "mkdir -p <sample_id>" near the top
            for line in script_content.split("\n"):
                line = line.strip()
                if line.startswith("mkdir -p ") and not line.startswith("mkdir -p genome_dir"):
                    sample_id = line.replace("mkdir -p ", "").strip()
                    if sample_id and "/" not in sample_id:
                        samples[sample_id] = exec_path
                        break
        except Exception as e:
            print(f"WARNING: Could not parse script at {script_path}: {e}", file=sys.stderr)

    return samples


def check_sample_success(exec_path):
    """Check if a sample's execution completed successfully (rc = 0)."""
    rc_path = os.path.join(exec_path, "rc")
    if not os.path.exists(rc_path):
        return False, "No rc file found (task may not have completed)"

    with open(rc_path, "r") as f:
        rc = f.read().strip()

    if rc == "0":
        return True, "Success"
    else:
        # Try to get error info from stderr
        stderr_path = os.path.join(exec_path, "stderr")
        error_msg = f"Exit code {rc}"
        if os.path.exists(stderr_path):
            with open(stderr_path, "r") as f:
                stderr_content = f.read().strip()
            # Get last few lines of stderr for the report
            stderr_lines = stderr_content.split("\n")
            last_lines = "\n".join(stderr_lines[-3:]) if len(stderr_lines) > 3 else stderr_content
            if last_lines:
                error_msg += f" | {last_lines}"
        return False, error_msg


def gather_sample_outputs(sample_id, exec_path, output_dir, keep_bam_and_junction):
    """Copy output files for a successful sample to the output directory."""
    sample_dir = os.path.join(output_dir, sample_id)
    os.makedirs(sample_dir, exist_ok=True)

    copied_files = []

    # Define which files to look for
    # Core outputs (always gather)
    core_patterns = [
        f"{sample_id}.star-fusion.fusion_predictions.tsv.gz",
        f"{sample_id}.star-fusion.fusion_predictions.abridged.tsv.gz",
        f"{sample_id}.star-fusion.fusion_candidates.preliminary.tsv.gz",
        f"{sample_id}.Log.final.out",
    ]

    # Outputs inside the sample subdirectory
    subdir_patterns = [
        f"{sample_id}/star-fusion.fusion_predictions.abridged.coding_effect.tsv",
        f"{sample_id}/FusionInspector-validate/finspector.FusionInspector.fusions.abridged.tsv",
        f"{sample_id}/FusionInspector-validate/finspector.fusion_inspector_web.html",
        f"{sample_id}/FusionInspector-inspect/finspector.FusionInspector.fusions.abridged.tsv",
        f"{sample_id}/FusionInspector-inspect/finspector.fusion_inspector_web.html",
    ]

    # Optional large files
    bam_junction_patterns = [
        f"{sample_id}.Chimeric.out.junction.gz",
        f"{sample_id}.STAR.aligned.UNsorted.bam",
        f"{sample_id}.STAR.aligned.coordsorted.bam",
        f"{sample_id}.SJ.out.tab.gz",
    ]

    # Copy core files from execution directory
    for pattern in core_patterns:
        src = os.path.join(exec_path, pattern)
        if os.path.exists(src):
            dst = os.path.join(sample_dir, os.path.basename(pattern))
            shutil.copy2(src, dst)
            copied_files.append(os.path.basename(pattern))

    # Copy files from sample subdirectory
    for pattern in subdir_patterns:
        src = os.path.join(exec_path, pattern)
        if os.path.exists(src):
            dst = os.path.join(sample_dir, os.path.basename(pattern))
            shutil.copy2(src, dst)
            copied_files.append(os.path.basename(pattern))

    # Copy BAM and junction files if requested
    if keep_bam_and_junction:
        for pattern in bam_junction_patterns:
            src = os.path.join(exec_path, pattern)
            if os.path.exists(src):
                dst = os.path.join(sample_dir, os.path.basename(pattern))
                shutil.copy2(src, dst)
                copied_files.append(os.path.basename(pattern))

    return copied_files


def main():
    parser = argparse.ArgumentParser(
        description="Recover results from a partially failed Cromwell batch run"
    )
    parser.add_argument(
        "--config", required=True,
        help="Path to batch_config.json (output_dir is read from this)"
    )
    parser.add_argument(
        "--exec-dir", default="cromwell-executions",
        help="Path to Cromwell execution directory (default: cromwell-executions)"
    )
    parser.add_argument(
        "--keep-bam-and-junction", action="store_true", default=False,
        help="Also gather BAM, junction, and SJ files"
    )
    args = parser.parse_args()

    # Read output directory from config
    with open(args.config, "r") as f:
        config = json.load(f)

    output_dir_key = "star_fusion_hg38_batch_hpc_wf.output_dir"
    if output_dir_key not in config:
        print(f"ERROR: '{output_dir_key}' not found in {args.config}", file=sys.stderr)
        sys.exit(1)

    output_dir = config[output_dir_key]

    # Check for keep_bam_and_junction in config as well
    keep_key = "star_fusion_hg38_batch_hpc_wf.keep_bam_and_junction"
    keep_bam = args.keep_bam_and_junction or config.get(keep_key, False)

    print(f"Output directory: {output_dir}")
    print(f"Execution directory: {args.exec_dir}")
    print(f"Keep BAM and junction: {keep_bam}")
    print()

    # Find all sample executions
    print("Scanning execution directory for sample runs...")
    samples = find_sample_executions(args.exec_dir)

    if not samples:
        print("ERROR: No sample executions found. Check the --exec-dir path.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(samples)} sample(s)")
    print()

    # Check each sample and gather results
    succeeded = []
    failed = []

    for sample_id, exec_path in sorted(samples.items()):
        success, message = check_sample_success(exec_path)

        if success:
            print(f"  [PASS] {sample_id} — gathering results...")
            copied = gather_sample_outputs(sample_id, exec_path, output_dir, keep_bam)
            print(f"         Copied {len(copied)} files to {output_dir}/{sample_id}/")
            succeeded.append(sample_id)
        else:
            print(f"  [FAIL] {sample_id} — {message}")
            failed.append((sample_id, message))

    # Summary
    print()
    print("=" * 60)
    print(f"Recovery Summary")
    print(f"  Succeeded: {len(succeeded)}")
    print(f"  Failed:    {len(failed)}")
    print(f"  Output:    {output_dir}")
    print("=" * 60)

    # Write failed samples report
    report_path = "failed_samples_report.tsv"
    with open(report_path, "w") as f:
        f.write("sample_id\tstatus\terror_details\trecovery_date\n")
        for sample_id, message in failed:
            # Clean up message for TSV (replace tabs and newlines)
            clean_msg = message.replace("\t", " ").replace("\n", " | ")
            f.write(f"{sample_id}\tFAILED\t{clean_msg}\t{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        # Also log succeeded for completeness
        for sample_id in succeeded:
            f.write(f"{sample_id}\tSUCCEEDED\t\t{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    print(f"\nFull report saved to: {report_path}")

    if failed:
        print(f"\nFailed samples that need to be re-run:")
        for sample_id, _ in failed:
            print(f"  - {sample_id}")


if __name__ == "__main__":
    main()
