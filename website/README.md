# ECC-IW Website

Paper companion website for **ECC-IW: Local Integrity Checking for Watermarked LLM Outputs via Error-Correcting Codes**.

## Local Preview

Install Node.js first if `node` / `npm` are not available on the machine.

```bash
npm install
npm run dev
```

Then open the local URL printed by Vite, usually `http://localhost:5173/`.

## Static Build

```bash
npm run build
npm run preview
```

The static site is emitted to `dist/` and can be deployed to GitHub Pages.

## Current Scope

The site includes the paper overview, method summary, corrected cross-model results, generation-quality analysis, final-text-only global verification, a matched Combinatorial Watermark comparison, and balanced Qwen3-guided edit results. The interactive walkthrough replays 18 real examples from the corrected experiment archive; it does not run model inference or live detection in the browser.

The displayed metrics are centralized in `src/resultsData.js`. The walkthrough records and compact bibliography in `src/demoExamples.js` and `src/referencesData.js` are generated from the corrected experiment archive and current paper draft before each public release.

The current source archive is `paper_results_archive_v3_corrected_20260806`. Update the generated data before publishing a new paper result version.

For the public release, replace `PAPER_URL` near the top of `src/App.jsx` with the final arXiv URL. `GITHUB_URL` already points to the project repository.
