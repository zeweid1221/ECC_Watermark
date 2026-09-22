# Released Vocabulary Partitions

`compact150-semantic-v1/` contains the exact model-specific vocabulary
partitions used for the paper's compact-150 main experiments. In the public
builder this algorithm is named `paper_main`. The appendix quality variant is
named `quality_variant_lsh`; its stricter global payload balancing does not reproduce
the main-protocol token assignments byte for byte.

Each model directory contains the complete token-to-bucket lookup, bucket ID
arrays, banned-token IDs, boundary-selection report, metadata, and the
partition checksum stored in `partition_config.json`.

To rebuild the main protocol, pass
`--target-boundary-size 150 --payload-split-strategy paper_main` to
`scripts/build_model_partition.py`. This regenerates the released algorithm;
the checked-in arrays and checksums remain the canonical byte-exact assignments
because tokenizer and numerical-library versions can affect a fresh build.

The artifacts correspond to these models:

- `qwen3-8b-semantic-v1`: `Qwen/Qwen3-8B`
- `mistral-7b-instruct-v0.3-semantic-v1`: `mistralai/Mistral-7B-Instruct-v0.3`
- `opt-125m-semantic-v1`: `facebook/opt-125m`

Load an artifact with `load_vocabulary_partition()` and validate it against
the active model with `validate_vocabulary_partition(...,
require_semantic_split=True)`. Loading also verifies the saved partition
checksum.
