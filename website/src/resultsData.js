export const resultCards = [
  {
    key: "local",
    label: "Local detection",
    value: "TPR ~ 0.998",
    detail: "At delta = 50, block FAR remains at or below 0.003 across all three models.",
  },
  {
    key: "quality",
    label: "Adaptive generation",
    value: "10.3–18.3% lower PPL",
    detail: "At delta = 50, adaptive realization improves conditional PPL with essentially unchanged TPR.",
  },
  {
    key: "global",
    label: "Global verification",
    value: "AUC 0.995–1.000",
    detail: "Final-text-only verification against matched unwatermarked outputs and human LFQA answers.",
  },
  {
    key: "cw",
    label: "ECC vs. CW",
    value: "0.003 vs. 0.141 FAR",
    detail: "At delta = 50, ECC-IW also raises Qwen3 block TPR from 0.918 to 0.998 over the AB prototype.",
  },
  {
    key: "llm",
    label: "LLM-guided edits",
    value: "0.905 TPR",
    detail: "Across 72 balanced delta = 20 Qwen3 edits; the full evaluation contains N = 144.",
  },
];

export const localDetection = [
  { model: "Qwen3-8B", delta: 2, feasible: 1.84, tpr: 0.2812, far: 0.1231, coverage: 0.4946, candidates: 4.74 },
  { model: "Qwen3-8B", delta: 5, feasible: 6.99, tpr: 0.5475, far: 0.3565, coverage: 0.5883, candidates: 4.06 },
  { model: "Qwen3-8B", delta: 20, feasible: 16.74, tpr: 0.9973, far: 0.0740, coverage: 0.7759, candidates: 2.96 },
  { model: "Qwen3-8B", delta: 50, feasible: 18.00, tpr: 0.9977, far: 0.0030, coverage: 0.8004, candidates: 2.83 },
  { model: "Mistral-7B", delta: 2, feasible: 1.66, tpr: 0.2875, far: 0.1319, coverage: 0.4929, candidates: 4.77 },
  { model: "Mistral-7B", delta: 5, feasible: 5.08, tpr: 0.5815, far: 0.4144, coverage: 0.5528, candidates: 4.22 },
  { model: "Mistral-7B", delta: 20, feasible: 17.93, tpr: 0.9974, far: 0.0060, coverage: 0.7984, candidates: 2.84 },
  { model: "Mistral-7B", delta: 50, feasible: 18.00, tpr: 0.9983, far: 0.0024, coverage: 0.8012, candidates: 2.84 },
  { model: "OPT-125M", delta: 2, feasible: 6.28, tpr: 0.2170, far: 0.0541, coverage: 0.5779, candidates: 4.09 },
  { model: "OPT-125M", delta: 5, feasible: 14.87, tpr: 0.3535, far: 0.0800, coverage: 0.7406, candidates: 3.13 },
  { model: "OPT-125M", delta: 20, feasible: 18.00, tpr: 0.9978, far: 0.0023, coverage: 0.7980, candidates: 2.85 },
  { model: "OPT-125M", delta: 50, feasible: 18.00, tpr: 0.9981, far: 0.0025, coverage: 0.7980, candidates: 2.84 },
].map((row) => ({
  ...row,
  candidateFraction: row.candidates / 16,
  searchReduction: 1 - row.candidates / 16,
}));

export const generationQuality = [
  { model: "Qwen3-8B", setting: "Unwatermarked", feasible: null, conditionalPpl: 1.96, unconditionalPpl: 4.58 },
  { model: "Qwen3-8B", setting: "delta = 2", feasible: 1.84, conditionalPpl: 23.36, unconditionalPpl: 28.44 },
  { model: "Qwen3-8B", setting: "delta = 5", feasible: 6.99, conditionalPpl: 33.38, unconditionalPpl: 39.66 },
  { model: "Qwen3-8B", setting: "delta = 20", feasible: 16.74, conditionalPpl: 80.74, unconditionalPpl: 91.67 },
  { model: "Mistral-7B", setting: "Unwatermarked", feasible: null, conditionalPpl: 2.07, unconditionalPpl: 4.49 },
  { model: "Mistral-7B", setting: "delta = 2", feasible: 1.66, conditionalPpl: 11.28, unconditionalPpl: 18.23 },
  { model: "Mistral-7B", setting: "delta = 5", feasible: 5.08, conditionalPpl: 15.59, unconditionalPpl: 23.62 },
  { model: "Mistral-7B", setting: "delta = 20", feasible: 17.93, conditionalPpl: 60.73, unconditionalPpl: 77.80 },
  { model: "OPT-125M", setting: "Unwatermarked", feasible: null, conditionalPpl: 3.21, unconditionalPpl: 15.32 },
  { model: "OPT-125M", setting: "delta = 2", feasible: 6.28, conditionalPpl: 20.93, unconditionalPpl: 43.50 },
  { model: "OPT-125M", setting: "delta = 5", feasible: 14.87, conditionalPpl: 33.52, unconditionalPpl: 59.68 },
  { model: "OPT-125M", setting: "delta = 20", feasible: 18.00, conditionalPpl: 72.18, unconditionalPpl: 113.57 },
];

export const adaptiveAblation = [
  { model: "Qwen3-8B", fixedPpl: 114.91, adaptivePpl: 96.29, reduction: 0.162, fixedTpr: 0.9983, adaptiveTpr: 0.9977 },
  { model: "Mistral-7B", fixedPpl: 81.12, adaptivePpl: 66.30, reduction: 0.183, fixedTpr: 0.9980, adaptiveTpr: 0.9983 },
  { model: "OPT-125M", fixedPpl: 97.10, adaptivePpl: 87.14, reduction: 0.103, fixedTpr: 0.9979, adaptiveTpr: 0.9981 },
];

export const globalVerification = [
  { model: "Qwen3-8B", delta: 2, auc: 0.9954, tprAtZeroFpr: 0.9336, wm: 0.383, llm: 0.262, human: 0.244 },
  { model: "Qwen3-8B", delta: 5, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.483, llm: 0.262, human: 0.244 },
  { model: "Qwen3-8B", delta: 20, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.799, llm: 0.262, human: 0.244 },
  { model: "Qwen3-8B", delta: 50, auc: 1.0000, tprAtZeroFpr: 0.9961, wm: 0.815, llm: 0.262, human: 0.244 },
  { model: "Mistral-7B", delta: 2, auc: 1.0000, tprAtZeroFpr: 0.9961, wm: 0.387, llm: 0.261, human: 0.245 },
  { model: "Mistral-7B", delta: 5, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.458, llm: 0.261, human: 0.245 },
  { model: "Mistral-7B", delta: 20, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.806, llm: 0.261, human: 0.244 },
  { model: "Mistral-7B", delta: 50, auc: 1.0000, tprAtZeroFpr: 0.9961, wm: 0.791, llm: 0.261, human: 0.244 },
  { model: "OPT-125M", delta: 2, auc: 0.9994, tprAtZeroFpr: 0.9844, wm: 0.487, llm: 0.284, human: 0.275 },
  { model: "OPT-125M", delta: 5, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.764, llm: 0.284, human: 0.275 },
  { model: "OPT-125M", delta: 20, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.922, llm: 0.284, human: 0.274 },
  { model: "OPT-125M", delta: 50, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.903, llm: 0.284, human: 0.275 },
];

export const combinatorialComparison = [
  { pattern: "AB", delta: 2, eccTpr: 0.2812, eccFar: 0.1231, cwTpr: 0.0000, cwFar: 0.0000, adherence: 0.590 },
  { pattern: "AB", delta: 5, eccTpr: 0.5475, eccFar: 0.3565, cwTpr: 0.0000, cwFar: 0.0000, adherence: 0.704 },
  { pattern: "AB", delta: 20, eccTpr: 0.9973, eccFar: 0.0740, cwTpr: 0.9216, cwFar: 0.2502, adherence: 0.982 },
  { pattern: "AB", delta: 50, eccTpr: 0.9977, eccFar: 0.0030, cwTpr: 0.9181, cwFar: 0.1411, adherence: 1.000 },
  { pattern: "ACADBCBD", delta: 2, eccTpr: 0.2812, eccFar: 0.1231, cwTpr: 0.0000, cwFar: 0.0000, adherence: 0.327 },
  { pattern: "ACADBCBD", delta: 5, eccTpr: 0.5475, eccFar: 0.3565, cwTpr: 0.0000, cwFar: 0.0000, adherence: 0.458 },
  { pattern: "ACADBCBD", delta: 20, eccTpr: 0.9973, eccFar: 0.0740, cwTpr: 0.9780, cwFar: 0.5438, adherence: 0.976 },
  { pattern: "ACADBCBD", delta: 50, eccTpr: 0.9977, eccFar: 0.0030, cwTpr: 0.9921, cwFar: 0.6330, adherence: 1.000 },
];

export const llmEditResults = [
  { delta: 5, intent: "Benign", n: 36, editedBlocks: 6.22, tpr: 0.8482, far: 0.3443, coverage: 0.4424 },
  { delta: 5, intent: "Malicious", n: 36, editedBlocks: 5.25, tpr: 0.8413, far: 0.3551, coverage: 0.4203 },
  { delta: 20, intent: "Benign", n: 36, editedBlocks: 5.78, tpr: 0.9038, far: 0.1182, coverage: 0.4967 },
  { delta: 20, intent: "Malicious", n: 36, editedBlocks: 5.36, tpr: 0.9067, far: 0.0769, coverage: 0.5019 },
];

export const archiveVersion = "paper_results_archive_v3_corrected_20260806";
