version 1.0

import "star_fusion_hg38_hpc_wf.wdl" as hpc

# ==============================================================================
# BATCH HPC WRAPPER: Run STAR-Fusion on multiple samples via scatter
# ==============================================================================
# This wrapper takes arrays of sample-specific inputs, scatters over them
# to run each sample through the HPC single-sample wrapper in parallel,
# and gathers key output files into a clean per-sample directory structure.
#
# Input:  Arrays of sample_id, left_fq, right_fq (one entry per sample)
#         Shared parameters (genome, fusion_inspector, memory, etc.)
# Output: Gathered results in output_dir/<sample_id>/ per sample

workflow star_fusion_hg38_batch_hpc_wf {
  input {
    # ---- Per-sample inputs (arrays, one entry per sample) ----
    Array[String] sample_ids
    Array[File] left_fqs
    Array[File] right_fqs

    # ---- Shared inputs (same for all samples) ----
    String local_genome_dir

    String? fusion_inspector
    Boolean examine_coding_effect = false
    Boolean coord_sort_bam = false
    Float min_FFPM = 0.1

    String docker = "trinityctat/starfusion:latest"
    Int num_cpu = 12
    String memory = "50G"

    # ---- Gather options ----
    String output_dir
    Boolean keep_bam_and_junction = false
  }

  # Scatter over samples
  scatter (idx in range(length(sample_ids))) {
    call hpc.star_fusion_hg38_wf as per_sample {
      input:
        sample_id             = sample_ids[idx],
        left_fq               = left_fqs[idx],
        right_fq              = right_fqs[idx],
        local_genome_dir      = local_genome_dir,
        fusion_inspector      = fusion_inspector,
        examine_coding_effect = examine_coding_effect,
        coord_sort_bam        = coord_sort_bam,
        min_FFPM              = min_FFPM,
        docker                = docker,
        num_cpu               = num_cpu,
        memory                = memory
    }

    call gather_results {
      input:
        sample_id                = sample_ids[idx],
        output_dir               = output_dir,
        keep_bam_and_junction    = keep_bam_and_junction,
        fusion_predictions       = per_sample.fusion_predictions,
        fusion_predictions_abridged = per_sample.fusion_predictions_abridged,
        coding_effect            = per_sample.coding_effect,
        star_log_final           = per_sample.star_log_final,
        junction                 = per_sample.junction,
        bam                      = per_sample.bam,
        sj                       = per_sample.sj,
        fusion_inspector_validate_fusions_abridged = per_sample.fusion_inspector_validate_fusions_abridged,
        fusion_inspector_validate_web              = per_sample.fusion_inspector_validate_web,
        fusion_inspector_inspect_fusions_abridged  = per_sample.fusion_inspector_inspect_fusions_abridged,
        fusion_inspector_inspect_web               = per_sample.fusion_inspector_inspect_web
    }
  }

  output {
    Array[String] completed_samples = sample_ids
    Array[String] output_directories = gather_results.sample_output_dir
  }
}


task gather_results {
  input {
    String sample_id
    String output_dir
    Boolean keep_bam_and_junction

    # Required outputs
    File fusion_predictions
    File fusion_predictions_abridged

    # Optional outputs
    File? coding_effect
    File? star_log_final
    File? junction
    File? bam
    File? sj
    File? fusion_inspector_validate_fusions_abridged
    File? fusion_inspector_validate_web
    File? fusion_inspector_inspect_fusions_abridged
    File? fusion_inspector_inspect_web
  }

  String sample_dir = "~{output_dir}/~{sample_id}"

  command <<<
    set -e

    mkdir -p ~{sample_dir}

    # --- Always copy core fusion results ---
    cp ~{fusion_predictions} ~{sample_dir}/
    cp ~{fusion_predictions_abridged} ~{sample_dir}/

    # --- Coding effect (if produced) ---
    if [ -f "~{coding_effect}" ]; then
      cp ~{coding_effect} ~{sample_dir}/
    fi

    # --- STAR log (if produced) ---
    if [ -f "~{star_log_final}" ]; then
      cp ~{star_log_final} ~{sample_dir}/
    fi

    # --- FusionInspector validate results (if produced) ---
    if [ -f "~{fusion_inspector_validate_fusions_abridged}" ]; then
      cp ~{fusion_inspector_validate_fusions_abridged} ~{sample_dir}/
    fi
    if [ -f "~{fusion_inspector_validate_web}" ]; then
      cp ~{fusion_inspector_validate_web} ~{sample_dir}/
    fi

    # --- FusionInspector inspect results (if produced) ---
    if [ -f "~{fusion_inspector_inspect_fusions_abridged}" ]; then
      cp ~{fusion_inspector_inspect_fusions_abridged} ~{sample_dir}/
    fi
    if [ -f "~{fusion_inspector_inspect_web}" ]; then
      cp ~{fusion_inspector_inspect_web} ~{sample_dir}/
    fi

    # --- BAM, junction, SJ (only if keep_bam_and_junction is true) ---
    if [ "~{keep_bam_and_junction}" == "true" ]; then
      if [ -f "~{junction}" ]; then
        cp ~{junction} ~{sample_dir}/
      fi
      if [ -f "~{bam}" ]; then
        cp ~{bam} ~{sample_dir}/
      fi
      if [ -f "~{sj}" ]; then
        cp ~{sj} ~{sample_dir}/
      fi
    fi

    echo "~{sample_dir}"
  >>>

  output {
    String sample_output_dir = read_string(stdout())
  }

  runtime {
    docker: "ubuntu:latest"
    memory: "2G"
    cpu: 1
  }
}
