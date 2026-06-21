# Local Integrity Checking for Watermarked LLM Outputs

This private repository contains the core implementation and companion website for the project:

**Local Integrity Checking for Watermarked LLM Outputs via Error-Correcting Codes**

The repository is intentionally curated for sharing and eventual release. It includes source code, scripts, and website assets, but excludes large experiment outputs, model caches, generated dependency folders, and temporary run artifacts.

## Contents

- `watermark_project/`: core ECC watermarking, detection, editing, partitioning, KGW baseline, and experiment logic.
- `scripts/`: standalone scripts for preview generation, LLM-guided editing, malicious-risk judging, plotting, and diagnostics.
- `run_main.py`: main experiment CLI.
- `website/`: Vite + React paper companion website with precomputed interactive walkthrough examples.

## Website Preview

From the repository root:

```bash
cd website
npm install
npm run dev
```

Then open the local URL printed by Vite, usually:

```text
http://127.0.0.1:5173/
```

## Notes

This repository is currently intended to stay private until the paper is ready for public release. The interactive website demo replays precomputed examples from saved experiment metadata; it does not run model inference or live detection in the browser.

