# Example HPC Execution Directory

This directory contains template configuration files for running the STAR-Fusion HPC pipeline using Cromwell on a SLURM-based cluster with Singularity. Templates are provided for both single-sample and batch (multi-sample) execution.

## Directory Contents

| File | Purpose |
|------|---------|
| `cromwell_TEMPLATE.conf` | Cromwell SLURM backend configuration template |
| `inputs_TEMPLATE.json` | Single-sample inputs template |
| `batch_inputs_TEMPLATE.json` | Batch (multi-sample) inputs template |
| `batch_config_TEMPLATE.json` | Shared parameters for batch runs (used by helper script) |
| `sample_sheet_EXAMPLE.csv` | Example CSV sample sheet format |
| `csv_to_batch_inputs.py` | Helper script to convert CSV sample sheet to batch inputs JSON |

## Prerequisites

Before setting up a run, ensure the following are in place:

1. **Java 17+** available in your PATH
2. **Cromwell 91** installed (e.g., at `~/.cromwell/lib/cromwell-91.jar`)
3. **Singularity or Apptainer** available via `module load` on compute nodes
4. **CTAT genome library** downloaded and pre-extracted to a shared location:
   ```bash
   wget https://data.broadinstitute.org/Trinity/CTAT_RESOURCE_LIB/__genome_libs_StarFv1.10/GRCh38_gencode_v22_CTAT_lib_Mar012021.plug-n-play.tar.gz
   tar xzf GRCh38_gencode_v22_CTAT_lib_Mar012021.plug-n-play.tar.gz
   ```
   Note the path to the `ctat_genome_lib_build_dir` subdirectory — this is what you will provide as `local_genome_dir`.

## Setup

### 1. Create a Run Directory

Create a new directory for each analysis run. Copy the template files you need:

```bash
mkdir -p /path/to/your/run_directory
cd /path/to/your/run_directory

# Always needed:
cp /path/to/repo/example_hpc_run/cromwell_TEMPLATE.conf cromwell.conf

# For single-sample runs:
cp /path/to/repo/example_hpc_run/inputs_TEMPLATE.json inputs.json

# For batch runs:
cp /path/to/repo/example_hpc_run/batch_config_TEMPLATE.json batch_config.json
# (also prepare your sample_sheet.csv — see Batch Execution below)
```

### 2. Edit `cromwell.conf`

Open `cromwell.conf` and replace the following placeholders:

| Placeholder | Replace With | How to Find It |
|-------------|-------------|----------------|
| `YOUR_PARTITION` | Your SLURM partition name | Run `sinfo -s` to list available partitions |
| `YOUR_SINGULARITY_MODULE` | The module name that provides `singularity` | Run `module avail singularity` or `module avail apptainer` |
| `YOUR_BASE_DATA_PATH` | The base filesystem path where your data, references, and run directories live | Must cover all paths referenced in your inputs JSON |

The `YOUR_BASE_DATA_PATH` bind mount appears twice on the same line (source:destination) so that paths inside the container match the host. For example, if all your data is under `/lustre/home/mylab/`, the bind would be `--bind /lustre/home/mylab:/lustre/home/mylab`.

**Additional settings you may want to adjust:**

- `memory = "100G"` — Default memory per task. STAR-Fusion typically needs 50-100 GB.
- `cpu = 12` — Default CPUs per task.
- `time_limit = "24:00:00"` — Maximum wall time. Adjust based on your partition limits and expected runtime.

### 3. Create a `run_command.sh` Script

Create a shell script to record the exact execution command for this run. This serves as documentation and makes it easy to re-run:

```bash
cat > run_command.sh << 'EOF'
java -Dconfig.file=/path/to/your/run_directory/cromwell.conf \
  -jar ~/.cromwell/lib/cromwell-91.jar \
  run /path/to/repo/star_fusion_hg38_batch_hpc_wf.wdl \
  --inputs batch_inputs.json 2>&1 | tee cromwell_run.log
EOF
```

Update the paths to match your run directory and repo location. For a single-sample run, change the WDL to `star_fusion_hg38_hpc_wf.wdl` and the inputs to `inputs.json`.

## Single-Sample Execution

### Edit `inputs.json`

Replace the placeholder values:

| Placeholder | Replace With |
|-------------|-------------|
| `YOUR_SAMPLE_ID` | A unique identifier for this sample |
| `/path/to/your/sample_R1.fq.gz` | Full path to the R1 FASTQ file |
| `/path/to/your/sample_R2.fq.gz` | Full path to the R2 FASTQ file |
| `/path/to/...ctat_genome_lib_build_dir` | Full path to the pre-extracted CTAT genome library |

**All paths must be absolute** and must be accessible from compute nodes via the bind mount configured in `cromwell.conf`.

**Alternative input mode — junction file re-run:**

To run from an existing junction file instead of FASTQs, replace the FASTQ entries:

```json
{
  "star_fusion_hg38_wf.sample_id": "YOUR_SAMPLE_ID",
  "star_fusion_hg38_wf.input_chimeric_junction": "/path/to/Chimeric.out.junction",
  "star_fusion_hg38_wf.local_genome_dir": "/path/to/ctat_genome_lib_build_dir",
  "star_fusion_hg38_wf.fusion_inspector": "validate",
  "star_fusion_hg38_wf.examine_coding_effect": true,
  "star_fusion_hg38_wf.memory": "100G",
  "star_fusion_hg38_wf.docker": "trinityctat/starfusion:latest"
}
```

### Run

```bash
tmux new -s starfusion
cd /path/to/your/run_directory
source run_command.sh
```

## Batch Execution

Batch mode runs multiple samples in parallel using WDL's `scatter` block. Cromwell submits each sample as a separate SLURM job, and a gather task collects results into a clean output directory.

### 1. Prepare a CSV Sample Sheet

Create a CSV file with one row per sample. Required columns: `sample_id`, `left_fq`, `right_fq`.

```csv
sample_id,left_fq,right_fq
VCU-PC-124_9017,/lustre/home/harrell_lab/bulkRNASeq/raw/VCU-PC-124_9017_R1.fq.gz,/lustre/home/harrell_lab/bulkRNASeq/raw/VCU-PC-124_9017_R2.fq.gz
VCU-PC-125_9018,/lustre/home/harrell_lab/bulkRNASeq/raw/VCU-PC-125_9018_R1.fq.gz,/lustre/home/harrell_lab/bulkRNASeq/raw/VCU-PC-125_9018_R2.fq.gz
```

### 2. Edit `batch_config.json`

This file contains parameters shared across all samples:

```json
{
  "star_fusion_hg38_batch_hpc_wf.local_genome_dir": "/path/to/ctat_genome_lib_build_dir",
  "star_fusion_hg38_batch_hpc_wf.fusion_inspector": "validate",
  "star_fusion_hg38_batch_hpc_wf.examine_coding_effect": true,
  "star_fusion_hg38_batch_hpc_wf.memory": "100G",
  "star_fusion_hg38_batch_hpc_wf.docker": "trinityctat/starfusion:latest",
  "star_fusion_hg38_batch_hpc_wf.output_dir": "/path/to/output_directory",
  "star_fusion_hg38_batch_hpc_wf.keep_bam_and_junction": false
}
```

Set `output_dir` to where you want gathered results. The gather task creates a subdirectory per sample:

```
/path/to/output_directory/
  VCU-PC-124_9017/
    VCU-PC-124_9017.star-fusion.fusion_predictions.tsv.gz
    VCU-PC-124_9017.star-fusion.fusion_predictions.abridged.tsv.gz
    ...
  VCU-PC-125_9018/
    ...
```

Set `keep_bam_and_junction` to `true` if you want BAM, junction, and SJ files included in the gathered output. These are large and excluded by default.

### 3. Generate the Batch Inputs JSON

```bash
python /path/to/repo/example_hpc_run/csv_to_batch_inputs.py \
  sample_sheet.csv \
  --config batch_config.json \
  --output batch_inputs.json
```

### 4. Update `run_command.sh`

Make sure your run command points to the batch WDL and batch inputs:

```bash
java -Dconfig.file=/path/to/your/run_directory/cromwell.conf \
  -jar ~/.cromwell/lib/cromwell-91.jar \
  run /path/to/repo/star_fusion_hg38_batch_hpc_wf.wdl \
  --inputs batch_inputs.json 2>&1 | tee cromwell_run.log
```

### 5. Run

```bash
tmux new -s starfusion
cd /path/to/your/run_directory
source run_command.sh
```

## Monitoring

```bash
# Check SLURM job status (multiple jobs will appear for batch runs)
squeue -u $USER

# Check job history and exit codes
sacct --user $USER --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS

# Watch the Cromwell log
tail -f cromwell_run.log
```

## Troubleshooting

If a run fails, check these files in the Cromwell execution directory:

```bash
# Find error logs
find cromwell-executions/ -name "docker_stderr" | xargs cat
find cromwell-executions/ -name "stdout" | xargs cat

# Check return code
find cromwell-executions/ -name "rc" | xargs cat

# View the generated script
find cromwell-executions/ -name "script" | xargs cat
```

**Common issues:**

- **Exit code 127 (command not found):** Usually a bind mount issue — the container can't see the input files or reference genome. Verify your `YOUR_BASE_DATA_PATH` bind mount covers all paths in your inputs JSON. Each `--bind` flag needs its own prefix (e.g., `--bind /path1:/path1 --bind /path2:/path2`).
- **Exit code 137 (OOM):** Increase `memory` in `cromwell.conf` or use a higher-memory partition.
- **"No such file or directory" for `cromwell.conf`:** Use the full absolute path with `-Dconfig.file=`.
- **Genome not found inside container:** The `local_genome_dir` is passed as a String, not a File — Cromwell does not copy it. It must be accessible inside the container via the bind mount.
- **Large file copies / storage issues:** Ensure `cromwell.conf` includes the `filesystems { local { localization = ["soft-link", "copy"] } }` block so Cromwell symlinks input files instead of copying them.
- **Symlinked FASTQ files:** Symlinks are fine as long as the real files (check with `readlink -f`) are also under the bind-mounted path.

## Cleaning Up

Cromwell execution directories can be large. After verifying your gathered results in the output directory, clean up:

```bash
rm -rf cromwell-executions
```

## Cluster-Specific Notes

This template was developed and validated on the VCU Apollo HPC (SLURM, Lustre, Singularity-CE 4.0.1). Adaptations for other clusters may include:

- Different partition names (`sinfo -s`)
- Different Singularity/Apptainer module names (`module avail`)
- Different base data paths for bind mounts
- `sbatch --wrap` may work on some clusters — Apollo requires submit scripts instead (already configured in this template)
- Some clusters may support hard-link localization; Apollo requires soft-link