# Example HPC Execution Directory

This directory contains template configuration files for running the STAR-Fusion HPC pipeline using Cromwell on a SLURM-based cluster with Singularity.

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

Create a new directory for each analysis run. Copy the template files into it:

```bash
mkdir -p /path/to/your/run_directory
cp cromwell_TEMPLATE.conf /path/to/your/run_directory/cromwell.conf
cp inputs_TEMPLATE.json /path/to/your/run_directory/inputs.json
```

### 2. Edit `cromwell.conf`

Open `cromwell.conf` and replace the following placeholders:

| Placeholder | Replace With | How to Find It |
|-------------|-------------|----------------|
| `YOUR_PARTITION` | Your SLURM partition name | Run `sinfo -s` to list available partitions |
| `YOUR_SINGULARITY_MODULE` | The module name that provides `singularity` | Run `module avail singularity` or `module avail apptainer` |
| `YOUR_BASE_DATA_PATH` | The base filesystem path where your data, references, and run directories live | Must cover all paths referenced in `inputs.json` |

The `YOUR_BASE_DATA_PATH` bind mount appears twice on the same line (source:destination) so that paths inside the container match the host. For example, if all your data is under `/lustre/home/mylab/`, the bind would be `--bind /lustre/home/mylab:/lustre/home/mylab`.

**Additional settings you may want to adjust:**

- `memory = "100G"` — Default memory per task. STAR-Fusion typically needs 50-100 GB.
- `cpu = 12` — Default CPUs per task.
- `time_limit = "24:00:00"` — Maximum wall time. Adjust based on your partition limits and expected runtime.

### 3. Edit `inputs.json`

Open `inputs.json` and replace the placeholder values:

| Placeholder | Replace With |
|-------------|-------------|
| `YOUR_SAMPLE_ID` | A unique identifier for this sample |
| `/path/to/your/sample_R1.fq.gz` | Full path to the R1 FASTQ file |
| `/path/to/your/sample_R2.fq.gz` | Full path to the R2 FASTQ file |
| `/path/to/...ctat_genome_lib_build_dir` | Full path to the pre-extracted CTAT genome library |

**All paths must be absolute** and must be accessible from compute nodes via the bind mount configured in `cromwell.conf`.

**Alternative input modes:**

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

## Running the Pipeline

Always run Cromwell inside a `tmux` session to prevent losing the process if your SSH connection drops:

```bash
tmux new -s starfusion
cd /path/to/your/run_directory

java -Dconfig.file=/path/to/your/run_directory/cromwell.conf \
  -jar ~/.cromwell/lib/cromwell-91.jar \
  run /path/to/repo/star_fusion_hg38_hpc_wf.wdl \
  --inputs inputs.json 2>&1 | tee cromwell_run.log
```

Replace `/path/to/repo/` with the full path to your clone of this repository. Cromwell resolves WDL imports relative to the main WDL file, so it must point to the file inside the cloned repo.

Detach from tmux with `Ctrl+B`, then `D`. Reattach later with `tmux attach -t starfusion`.

## Monitoring

```bash
# Check SLURM job status
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

- **Exit code 127 (command not found):** Usually a bind mount issue — the container can't see the input files or reference genome. Verify your `YOUR_BASE_DATA_PATH` bind mount covers all paths in `inputs.json`.
- **Exit code 137 (OOM):** Increase `memory` in `cromwell.conf` or use a higher-memory partition.
- **"No such file or directory" for `cromwell.conf`:** Use the full absolute path with `-Dconfig.file=`.
- **Genome not found inside container:** The `local_genome_dir` is passed as a String, not a File — Cromwell does not copy it. It must be accessible inside the container via the bind mount.

## Cleaning Up

Cromwell execution directories can be large. After collecting your results, clean up:

```bash
rm -rf cromwell-executions
```

## Cluster-Specific Notes

This template was developed and validated on the VCU Apollo HPC (SLURM, Lustre, Singularity-CE 4.0.1). Adaptations for other clusters may include:

- Different partition names (`sinfo -s`)
- Different Singularity/Apptainer module names (`module avail`)
- Different base data paths for bind mounts
- `sbatch --wrap` may work on some clusters — Apollo requires submit scripts instead (already configured in this template)