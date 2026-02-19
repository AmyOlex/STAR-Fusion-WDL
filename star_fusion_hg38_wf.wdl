version 1.0

import "star_fusion_workflow.wdl" as sf

workflow star_fusion_hg38_wf {
  input {
    String sample_id

    File genome_plug_n_play_tar_gz

    # ---- FASTQ inputs (original mode) ----
    File? left_fq
    File? right_fq
    File? fastq_pair_tar_gz

    # ---- Junction file input (re-run mode) ----
    # Provide Chimeric.out.junction(.gz) from a prior STAR run to skip re-alignment
    File? input_chimeric_junction

    # ---- STAR-Fusion parameters ----
    String?  fusion_inspector         # "inspect" or "validate"
    Boolean  examine_coding_effect = false
    Boolean  coord_sort_bam        = false
    Float    min_FFPM              = 0.1

    # ---- Runtime parameters ----
    String  docker                       = "trinityctat/starfusion:latest"
    Int     num_cpu                      = 12
    Float   fastq_disk_space_multiplier  = 3.25
    String  memory                       = "50G"
    Float   genome_disk_space_multiplier = 2.5
    Int     preemptible                  = 2
    Float   extra_disk_space             = 10
    Boolean use_ssd                      = true
  }

  call sf.star_fusion_workflow {
    input:
      sample_id                    = sample_id,
      genome_plug_n_play_tar_gz    = genome_plug_n_play_tar_gz,
      left_fq                      = left_fq,
      right_fq                     = right_fq,
      fastq_pair_tar_gz            = fastq_pair_tar_gz,
      input_chimeric_junction      = input_chimeric_junction,
      fusion_inspector             = fusion_inspector,
      examine_coding_effect        = examine_coding_effect,
      coord_sort_bam               = coord_sort_bam,
      min_FFPM                     = min_FFPM,
      docker                       = docker,
      num_cpu                      = num_cpu,
      fastq_disk_space_multiplier  = fastq_disk_space_multiplier,
      memory                       = memory,
      genome_disk_space_multiplier = genome_disk_space_multiplier,
      preemptible                  = preemptible,
      extra_disk_space             = extra_disk_space,
      use_ssd                      = use_ssd
  }

  output {
    File  fusion_predictions          = sf.star_fusion_workflow.fusion_predictions
    File  fusion_predictions_abridged = sf.star_fusion_workflow.fusion_predictions_abridged
    File? junction                    = sf.star_fusion_workflow.junction
    File? bam                         = sf.star_fusion_workflow.bam
    File? bai                         = sf.star_fusion_workflow.bai
    File? sj                          = sf.star_fusion_workflow.sj
    File? coding_effect               = sf.star_fusion_workflow.coding_effect
    Array[File]? extract_fusion_reads = sf.star_fusion_workflow.extract_fusion_reads
    File? star_log_final              = sf.star_fusion_workflow.star_log_final

    File? fusion_inspector_validate_fusions_abridged = sf.star_fusion_workflow.fusion_inspector_validate_fusions_abridged
    File? fusion_inspector_validate_web              = sf.star_fusion_workflow.fusion_inspector_validate_web
    File? fusion_inspector_inspect_fusions_abridged  = sf.star_fusion_workflow.fusion_inspector_inspect_fusions_abridged
    File? fusion_inspector_inspect_web               = sf.star_fusion_workflow.fusion_inspector_inspect_web
  }
}
