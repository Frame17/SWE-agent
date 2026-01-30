python -m sweagent.run.run_batch \
  --config config/gradle_test_generation.yaml \
  --instances.type file \
  --instances.path gradle_prs_swe_bench_trimmed.json \
  --agent.model.name claude-sonnet-4-5