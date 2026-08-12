export const resultCards = [
  {
    key: "local",
    label: "Local detection",
    value: "TPR 0.997-0.998",
    detail: "At delta = 20, block FAR ranges from 0.002 to 0.075 across all three models.",
  },
  {
    key: "quality",
    label: "Adaptive generation",
    value: "18.0-23.4% lower PPL",
    detail: "At delta = 20, adaptive realization consistently reduces conditional PPL across model families.",
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
    value: "0.074 vs. 0.250 FAR",
    detail: "At delta = 20, ECC-IW retains 0.997 TPR while the matched AB CW reaches 0.922 TPR.",
  },
  {
    key: "llm",
    label: "LLM-guided edits",
    value: "0.905 TPR",
    detail: "Across 72 balanced delta = 20 Qwen3 edits; the full evaluation contains N = 144.",
  },
];

export const localDetection = [
  { model: "Qwen3-8B", delta: 2, tolerance: 2, feasible: 1.78, tpr: 0.2621, far: 0.0839, farReduction: 0.318, coverage: 0.5103, candidates: 4.70 },
  { model: "Qwen3-8B", delta: 5, tolerance: 1, feasible: 6.84, tpr: 0.5217, far: 0.2107, farReduction: 0.409, coverage: 0.6106, candidates: 3.99 },
  { model: "Qwen3-8B", delta: 20, tolerance: 0, feasible: 16.71, tpr: 0.9966, far: 0.0754, farReduction: null, coverage: 0.7811, candidates: 2.96 },
  { model: "Mistral-7B", delta: 2, tolerance: 2, feasible: 1.70, tpr: 0.2630, far: 0.0851, farReduction: 0.355, coverage: 0.5108, candidates: 4.73 },
  { model: "Mistral-7B", delta: 5, tolerance: 1, feasible: 5.34, tpr: 0.5443, far: 0.2119, farReduction: 0.489, coverage: 0.5874, candidates: 4.13 },
  { model: "Mistral-7B", delta: 20, tolerance: 0, feasible: 17.93, tpr: 0.9978, far: 0.0071, farReduction: null, coverage: 0.8009, candidates: 2.85 },
  { model: "OPT-125M", delta: 2, tolerance: 2, feasible: 6.56, tpr: 0.1843, far: 0.0115, farReduction: 0.786, coverage: 0.6134, candidates: 3.98 },
  { model: "OPT-125M", delta: 5, tolerance: 1, feasible: 15.26, tpr: 0.3366, far: 0.0162, farReduction: 0.797, coverage: 0.7576, candidates: 3.06 },
  { model: "OPT-125M", delta: 20, tolerance: 0, feasible: 18.00, tpr: 0.9980, far: 0.0025, farReduction: null, coverage: 0.8023, candidates: 2.85 },
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
  { model: "Qwen3-8B", delta: 2, reduction: 0.027949 },
  { model: "Qwen3-8B", delta: 5, reduction: 0.145258 },
  { model: "Qwen3-8B", delta: 20, reduction: 0.180207 },
  { model: "Mistral-7B", delta: 2, reduction: 0.012160 },
  { model: "Mistral-7B", delta: 5, reduction: 0.128352 },
  { model: "Mistral-7B", delta: 20, reduction: 0.190351 },
  { model: "OPT-125M", delta: 2, reduction: 0.158121 },
  { model: "OPT-125M", delta: 5, reduction: 0.226736 },
  { model: "OPT-125M", delta: 20, reduction: 0.234126 },
];

export const globalVerification = [
  { model: "Qwen3-8B", delta: 2, auc: 0.9954, tprAtZeroFpr: 0.9336, wm: 0.383, llm: 0.262, human: 0.244 },
  { model: "Qwen3-8B", delta: 5, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.483, llm: 0.262, human: 0.244 },
  { model: "Qwen3-8B", delta: 20, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.799, llm: 0.262, human: 0.244 },
  { model: "Mistral-7B", delta: 2, auc: 1.0000, tprAtZeroFpr: 0.9961, wm: 0.387, llm: 0.261, human: 0.245 },
  { model: "Mistral-7B", delta: 5, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.458, llm: 0.261, human: 0.245 },
  { model: "Mistral-7B", delta: 20, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.806, llm: 0.261, human: 0.244 },
  { model: "OPT-125M", delta: 2, auc: 0.9994, tprAtZeroFpr: 0.9844, wm: 0.487, llm: 0.284, human: 0.275 },
  { model: "OPT-125M", delta: 5, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.764, llm: 0.284, human: 0.275 },
  { model: "OPT-125M", delta: 20, auc: 1.0000, tprAtZeroFpr: 1.0000, wm: 0.922, llm: 0.284, human: 0.274 },
];

export const combinatorialComparison = [
  { pattern: "AB", delta: 2, eccTpr: 0.2812, eccFar: 0.1231, cwTpr: 0.0000, cwFar: 0.0000, adherence: 0.590 },
  { pattern: "AB", delta: 5, eccTpr: 0.5475, eccFar: 0.3565, cwTpr: 0.0000, cwFar: 0.0000, adherence: 0.704 },
  { pattern: "AB", delta: 20, eccTpr: 0.9973, eccFar: 0.0740, cwTpr: 0.9216, cwFar: 0.2502, adherence: 0.982 },
  { pattern: "ACADBCBD", delta: 2, eccTpr: 0.2812, eccFar: 0.1231, cwTpr: 0.0000, cwFar: 0.0000, adherence: 0.327 },
  { pattern: "ACADBCBD", delta: 5, eccTpr: 0.5475, eccFar: 0.3565, cwTpr: 0.0000, cwFar: 0.0000, adherence: 0.458 },
  { pattern: "ACADBCBD", delta: 20, eccTpr: 0.9973, eccFar: 0.0740, cwTpr: 0.9780, cwFar: 0.5438, adherence: 0.976 },
];

export const llmEditResults = [
  { delta: 5, intent: "Benign", n: 36, editedBlocks: 6.22, tpr: 0.8482, far: 0.3443, coverage: 0.4424 },
  { delta: 5, intent: "Malicious", n: 36, editedBlocks: 5.25, tpr: 0.8413, far: 0.3551, coverage: 0.4203 },
  { delta: 20, intent: "Benign", n: 36, editedBlocks: 5.78, tpr: 0.9038, far: 0.1182, coverage: 0.4967 },
  { delta: 20, intent: "Malicious", n: 36, editedBlocks: 5.36, tpr: 0.9067, far: 0.0769, coverage: 0.5019 },
];

export const archiveVersion = "paper_rerun_20260811 (Local + Quality); validated comparison archives (Global + CW + LLM edits)";
