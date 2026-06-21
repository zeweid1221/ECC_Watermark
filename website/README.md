# ECC Local Integrity Website

Paper companion website for **Local Integrity Checking for Watermarked LLM Outputs via Error-Correcting Codes**.

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

This first version includes the paper overview, method summary, main result figures, LLM-guided sparse edit table, walkthrough placeholder, and citation/reference section. The interactive demo is intentionally a precomputed replay placeholder; it does not run model inference or live detection in the browser.
