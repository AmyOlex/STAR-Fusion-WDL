# STAR-Fusion Terra WDL (with Junction File Input and HPC Support)

[![Dockstore](https://img.shields.io/badge/Dockstore-STAR--Fusion--WDL--hg38v22-blue)](https://dockstore.org)

A modified version of the [STAR-Fusion Terra WDL pipeline](https://github.com/STAR-Fusion/STAR-Fusion/blob/Terra/WDL/star_fusion_hg38_wf.wdl) that adds support for re-running fusion analysis from an existing `Chimeric.out.junction` file, bypassing the need to repeat STAR alignment, and for running on HPC clusters with a pre-extracted CTAT genome library.

## Overview

The original STAR-Fusion Terra pipeline requires FASTQ files as input, which means re-running fusion analysis requires re-downloading raw data and repeating the full alignment step. This modified version allows you to skip alignment entirely by providing the `Chimeric.out.junction` file from a prior run as input, saving significant time and compute cost.

Additionally, an HPC-specific wrapper (`star_fusion_hg38_hpc_wf.wdl`) is provided for running the pipeline on SLURM-based clusters using Cromwell and Singularity, with a pre-extracted CTAT genome library to avoid repeated extraction and conserve storage.

## WDL Files

| File | Purpose |
|------|---------|
| `star_fusion_workflow.wdl` | Sub-workflow containing the STAR-Fusion task logic. Shared by both wrappers. |
| `star_fusion_hg38_wf.wdl` | **Terra/Cloud wrapper.** Accepts `genome_plug_n_play_tar_gz` with a default GCS path. Extracts the genome at runtime. |
| `star_fusion_hg38_hpc_wf.wdl` | **HPC wrapper.** Accepts `local_genome_dir` (String path to a pre-extracted CTAT genome library). No runtime extraction. |

## Changes from the Original Pipeline

- Added `input_chimeric_junction` as an optional input (`File?`) — accepts plain or gzipped (`.gz`) junction files
- When a junction file is provided, STAR-Fusion is invoked with `-J` instead of `--left_fq`/`--right_fq`, skipping STAR alignment entirely
- BAM, junction, SJ, and STAR log outputs are now optional (`File?`) since they are only produced during full alignment runs
- Disk size calculation uses junction file size rather than the FASTQ multiplier when running in junction mode
- Added `local_genome_dir` (`String?`) input to the sub-workflow for passing a pre-extracted CTAT genome library path, bypassing tar.gz extraction
- Made `genome_plug_n_play_tar_gz` optional in the sub-workflow to support HPC mode
- Added `star_fusion_hg38_hpc_wf.wdl` wrapper for HPC/SLURM execution with `local_genome_dir` as a required input

## Input Modes

### Mode 1: FASTQ Input (original behavior)
Provide one of the following as in the original pipeline:
- `left_fq` + `right_fq` — paired FASTQ files
- `fastq_pair_tar_gz` — a tarball of paired FASTQs

### Mode 2: Junction File Input (new)
Provide:
- `input_chimeric_junction` — the `Chimeric.out.junction` or `Chimeric.out.junction.gz` file from a prior STAR-Fusion run

> **Note:** The `Chimeric.out.junction.gz` file is produced as an output of this pipeline, so it can be fed directly back in for re-analysis runs.

### Genome Input: Cloud vs. HPC
- **Terra/Cloud (`star_fusion_hg38_wf.wdl`):** Provide `genome_plug_n_play_tar_gz` — the CTAT genome library tar.gz (default points to the GCS-hosted March 2021 build). Extracted at runtime.
- **HPC (`star_fusion_hg38_hpc_wf.wdl`):** Provide `local_genome_dir` — the full path to a pre-extracted `ctat_genome_lib_build_dir` on the local filesystem. No extraction occurs, saving disk space and runtime.

## Inputs

### Terra/Cloud Wrapper (`star_fusion_hg38_wf.wdl`)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `sample_id` | String | Yes | | Sample identifier |
| `genome_plug_n_play_tar_gz` | File | Yes | GCS path | CTAT genome resource library (tar.gz) |
| `left_fq` | File? | No | | Left FASTQ file |
| `right_fq` | File? | No | | Right FASTQ file |
| `fastq_pair_tar_gz` | File? | No | | Tarball of paired FASTQs |
| `input_chimeric_junction` | File? | No | | Chimeric.out.junction(.gz) from prior run |
| `fusion_inspector` | String? | No | | `inspect` or `validate` |
| `examine_coding_effect` | Boolean | No | `false` | Annotate coding effect of fusions |
| `coord_sort_bam` | Boolean | No | `false` | Coordinate-sort the output BAM |
| `min_FFPM` | Float | No | `0.1` | Minimum fusion fragments per million |
| `docker` | String | No | `trinityctat/starfusion:latest` | Docker image |
| `num_cpu` | Int | No | `12` | Number of CPUs |
| `memory` | String | No | `50G` | Memory allocation |
| `preemptible` | Int | No | `2` | Number of preemptible retries |
| `extra_disk_space` | Float | No | `10` | Extra disk space in GB |
| `use_ssd` | Boolean | No | `true` | Use SSD storage |

### HPC Wrapper (`star_fusion_hg38_hpc_wf.wdl`)

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `sample_id` | String | Yes | | Sample identifier |
| `local_genome_dir` | String | Yes | | Path to pre-extracted `ctat_genome_lib_build_dir` |
| `left_fq` | File? | No | | Left FASTQ file |
| `right_fq` | File? | No | | Right FASTQ file |
| `fastq_pair_tar_gz` | File? | No | | Tarball of paired FASTQs |
| `input_chimeric_junction` | File? | No | | Chimeric.out.junction(.gz) from prior run |
| `fusion_inspector` | String? | No | | `inspect` or `validate` |
| `examine_coding_effect` | Boolean | No | `false` | Annotate coding effect of fusions |
| `coord_sort_bam` | Boolean | No | `false` | Coordinate-sort the output BAM |
| `min_FFPM` | Float | No | `0.1` | Minimum fusion fragments per million |
| `docker` | String | No | `trinityctat/starfusion:latest` | Docker image |
| `num_cpu` | Int | No | `12` | Number of CPUs |
| `memory` | String | No | `50G` | Memory allocation |

> **Note:** Cloud-specific parameters (`preemptible`, `use_ssd`, `extra_disk_space`, disk space multipliers) are not included in the HPC wrapper as they are not relevant to SLURM-based execution.

## Outputs

| Output | Type | Description |
|---|---|---|
| `fusion_predictions` | File | STAR-Fusion predictions (gzipped TSV) |
| `fusion_predictions_abridged` | File | Abridged fusion predictions (gzipped TSV) |
| `junction` | File? | Chimeric.out.junction (gzipped) |
| `bam` | File? | Aligned BAM file |
| `bai` | File? | BAM index (if coord-sorted) |
| `sj` | File? | SJ.out.tab splice junction file (gzipped) |
| `star_log_final` | File? | STAR alignment log |
| `coding_effect` | File? | Coding effect annotations |
| `extract_fusion_reads` | Array[File]? | Fusion evidence reads |
| `fusion_inspector_validate_fusions_abridged` | File? | FusionInspector validate results |
| `fusion_inspector_validate_web` | File? | FusionInspector validate web report |
| `fusion_inspector_inspect_fusions_abridged` | File? | FusionInspector inspect results |
| `fusion_inspector_inspect_web` | File? | FusionInspector inspect web report |

## Usage on Terra

1. Upload `star_fusion_hg38_wf.wdl` and `star_fusion_workflow.wdl` to your Terra workspace via the **Workflows** tab
2. For a fresh run, populate `left_fq`/`right_fq` (or `fastq_pair_tar_gz`) in your data table as usual
3. For a re-run from an existing junction file, populate `input_chimeric_junction` in your data table with the `Chimeric.out.junction.gz` path from the prior run, and leave the FASTQ columns empty

## Usage on HPC (Cromwell + Singularity + SLURM)

### Prerequisites

- Cromwell 91+ (`java -jar cromwell-91.jar`)
- Java 17+
- Singularity or Apptainer available via `module load`
- CTAT genome library pre-extracted on the local filesystem

### Setup

1. Pre-extract the CTAT genome library once to a shared location:
   ```bash
   tar xzf GRCh38_gencode_v22_CTAT_lib_Mar012021.plug-n-play.tar.gz
   ```

2. Create a run directory with a `cromwell.conf` (SLURM backend configuration) and an `inputs.json` pointing to your data and the pre-extracted genome:
   ```json
   {
     "star_fusion_hg38_wf.sample_id": "SAMPLE_001",
     "star_fusion_hg38_wf.left_fq": "/path/to/sample_R1.fq.gz",
     "star_fusion_hg38_wf.right_fq": "/path/to/sample_R2.fq.gz",
     "star_fusion_hg38_wf.local_genome_dir": "/path/to/ctat_genome_lib_build_dir",
     "star_fusion_hg38_wf.fusion_inspector": "validate",
     "star_fusion_hg38_wf.examine_coding_effect": true,
     "star_fusion_hg38_wf.memory": "100G",
     "star_fusion_hg38_wf.docker": "trinityctat/starfusion:latest"
   }
   ```

3. Run with Cromwell:
   ```bash
   java -Dconfig.file=/path/to/cromwell.conf \
     -jar ~/.cromwell/lib/cromwell-91.jar \
     run star_fusion_hg38_hpc_wf.wdl \
     --inputs inputs.json 2>&1 | tee cromwell_run.log
   ```

> **Note:** Cromwell configuration for SLURM with Singularity requires cluster-specific settings (partition names, bind paths, submit script format). See the accompanying installation documentation for detailed setup instructions.

## AI Disclaimer

Portions of this pipeline, including the modified WDL code and documentation, were developed with the assistance of [Claude Opus 4.6](https://www.anthropic.com) (Anthropic). All AI-generated code has been reviewed for correctness, but users are encouraged to validate pipeline behavior in their own environment before use in production analyses.

## Authors

- **Brian Haas** (bhaas@broadinstitute.org) — Original STAR-Fusion pipeline
- **Amy Olex** (alolex@vcu.edu) — Junction file input modifications, HPC execution support

## Credits

This pipeline is a modification of the original STAR-Fusion Terra WDL developed by the [Trinity CTAT project](https://github.com/STAR-Fusion/STAR-Fusion). Please cite the original STAR-Fusion publication if you use this pipeline in your work:

> Haas BJ, et al. *Accuracy assessment of fusion transcript detection via read-mapping and de novo fusion transcript assembly-based methods.* Genome Biology, 2019.
