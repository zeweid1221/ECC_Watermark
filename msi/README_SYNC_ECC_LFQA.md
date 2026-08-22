# Synchronization-ECC LFQA Baseline

This pipeline reproduces the synchronization-string plus VT construction from
the accepted Findings of EMNLP 2026 paper under the current ECC-IW LFQA
protocol. In this repository, `sync-ECC` refers to that accepted construction;
`ECC-IW` refers to the current joint VT-Hamming method with explicit boundary
anchors and global block decomposition.

## Scope

The baseline is isolated from `watermark_project/` and implemented in readable
source at `baselines/sync_ecc.py`. It does not import historical experiment
scripts, serialized Python bytecode, or cached `.pt` objects.

The default Qwen3 run uses:

- the same 256 LFQA prompts and QA/chat formatting as ECC-IW;
- 18 blocks of 7 tokens;
- soft logit biases 2, 5, and 20;
- temperature 0.75, top-k 40, top-p 0.9, and repetition penalty 1.2;
- insertion, deletion, and substitution attacks at rates 0.2/0.4/0.6/0.8;
- per-block edit budgets 1/2/3 with uniform sampling from 1 through the budget.
- insertion gaps sampled inside their source block, matching the accepted
  camera-ready ground-truth convention.

Insertion and deletion are the accepted method's native threat model.
Substitution is reported as an out-of-scope stress test and is sampled to alter
the induced step bucket.

Block TPR/FAR use the accepted evaluator's restored-block rule: a block is
flagged when its recovered token count differs from seven. Alignment
insertions are assigned to the previous matched block, or to the next matched
block when no previous match exists. VT nearest-codeword decoding is kept as a
separate candidate-location refinement and reports coverage and candidate-set
size; it is not folded into the block alarm.

## Run on MSI

From the repository root:

```bash
mkdir -p logs
JOBID=$(sbatch --parsable msi/run_qwen3_sync_ecc_lfqa.slurm)
echo "$JOBID"
```

Use a unique output tag when rerunning:

```bash
JOBID=$(sbatch --parsable \
  --export=ALL,RUN_TAG=qwen3_sync_ecc_lfqa_256_v2 \
  msi/run_qwen3_sync_ecc_lfqa.slurm)
```

The launcher runs protocol unit tests before generation and validates the full
result grid afterward. A successful default run contains 108 summary rows,
27,648 detail rows, 768 saved generations, and `validation_report.json` with
`"status": "passed"`.

## Outputs

The default result directory is:

```text
outputs/sync_ecc_lfqa_baseline/qwen3_sync_ecc_lfqa_256_v1/
```

Important files are `summary.csv`, `details.csv`, `generated.json`,
`config.json`, `prompts.txt`, and `validation_report.json`. Conditional PPL is
computed from the exact saved continuation token IDs under the frozen source
model, matching the current ECC-IW evaluator.

## Deterministic Metric Replay

Saved generations can be reevaluated with the current detector without loading
the source model weights:

```bash
python scripts/recompute_sync_ecc_lfqa_results.py \
  --result-dir outputs/sync_ecc_lfqa_baseline/qwen3_sync_ecc_lfqa_256_v1 \
  --output-dir outputs/sync_ecc_lfqa_baseline/qwen3_sync_ecc_lfqa_256_v1_corrected \
  --local-files-only
```

The replay reconstructs the attack vocabulary with the source tokenizer,
reuses every saved random seed, and requires the realized edit count,
ground-truth blocks, and alignment distance to match every original detail
row. It records input hashes and the implementation commit in
`recompute_report.json`. `numba` is optional and only accelerates alignment;
the reference implementation is used when it is unavailable.
