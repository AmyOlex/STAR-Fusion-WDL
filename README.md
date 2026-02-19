# STAR-Fusion Terra WDL (with Junction File Input)

A modified version of the [STAR-Fusion Terra WDL pipeline](https://github.com/STAR-Fusion/STAR-Fusion/blob/Terra/WDL/star_fusion_hg38_wf.wdl) that adds support for re-running fusion analysis from an existing `Chimeric.out.junction` file, bypassing the need to repeat STAR alignment.

## Overview

The original STAR-Fusion Terra pipeline requires FASTQ files as input, which means re-running fusion analysis requires re-downloading raw data and repeating the full alignment step. This modified version allows you to skip alignment entirely by providing the `Chimeric.out.junction` file from a prior run as input, saving significant time and compute cost.

## Changes from the Original Pipeline

- Added `input_chimeric_junction` as an optional input (`File?`) — accepts plain or gzipped (`.gz`) junction files
- When a junction file is provided, STAR-Fusion is invoked with `-J` instead of `--left_fq`/`--right_fq`, skipping STAR alignment entirely
- BAM, junction, SJ, and STAR log outputs are now optional (`File?`) since they are only produced during full alignment runs
- Disk size calculation uses junction file size rather than the FASTQ multiplier when running in junction mode

## Input Modes

### Mode 1: FASTQ Input (original behavior)
Provide one of the following as in the original pipeline:
- `left_fq` + `right_fq` — paired FASTQ files
- `fastq_pair_tar_gz` — a tarball of paired FASTQs

### Mode 2: Junction File Input (new)
Provide:
- `input_chimeric_junction` — the `Chimeric.out.junction` or `Chimeric.out.junction.gz` file from a prior STAR-Fusion run

> **Note:** The `Chimeric.out.junction.gz` file is produced as an output of this pipeline, so it can be fed directly back in for re-analysis runs.

## Inputs

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `sample_id` | String | Yes | | Sample identifier |
| `genome_plug_n_play_tar_gz` | File | Yes | | CTAT genome resource library |
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

## AI Disclaimer

Portions of this pipeline, including the modified WDL code and documentation, were developed with the assistance of [Claude Sonnet 4.6](https://www.anthropic.com) (Anthropic). All AI-generated code has been reviewed for correctness, but users are encouraged to validate pipeline behavior in their own environment before use in production analyses.

## Credits

This pipeline is a modification of the original STAR-Fusion Terra WDL developed by the [Trinity CTAT project](https://github.com/STAR-Fusion/STAR-Fusion). Please cite the original STAR-Fusion publication if you use this pipeline in your work:

> Haas BJ, et al. *Accuracy assessment of fusion transcript detection via read-mapping and de novo fusion transcript assembly-based methods.* Genome Biology, 2019.

