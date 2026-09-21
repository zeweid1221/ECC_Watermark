# Released Vocabulary Partitions

`compact150-semantic-v1/` contains the exact model-specific vocabulary
partitions used for the paper's compact-150 main experiments. These artifacts
are included because later versions of the partition builder use a stricter
global payload-balancing rule and therefore do not reproduce the original
token assignments byte for byte.

Each model directory contains the complete token-to-bucket lookup, bucket ID
arrays, banned-token IDs, boundary-selection report, metadata, and the
partition checksum stored in `partition_config.json`.

The artifacts correspond to these models:

- `qwen3-8b-semantic-v1`: `Qwen/Qwen3-8B`
- `mistral-7b-instruct-v0.3-semantic-v1`: `mistralai/Mistral-7B-Instruct-v0.3`
- `opt-125m-semantic-v1`: `facebook/opt-125m`

Load an artifact with `load_vocabulary_partition()` and validate it against
the active model with `validate_vocabulary_partition(...,
require_semantic_split=True)`. Loading also verifies the saved partition
checksum.
