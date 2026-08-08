import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { demoExamples } from "./demoExamples.js";
import { paperReferences } from "./referencesData.js";
import {
  adaptiveAblation,
  archiveVersion,
  combinatorialComparison,
  globalVerification,
  llmEditResults,
  localDetection,
  resultCards,
} from "./resultsData.js";

const PAPER_URL = "#citation";
const GITHUB_URL = "https://github.com/zeweid1221/ECC_Watermark";
const BIBTEX = `@misc{ecc_iw,
  title  = {ECC-IW: Local Integrity Checking for Watermarked LLM Outputs via Error-Correcting Codes},
  author = {Deng, Zewei and Xie, Liyan and Siddeek, Muhammad and Seif, Mohamed and Goldsmith, Andrea J. and Poor, H. Vincent and Wang, Mengdi},
  year   = {2026}
}`;

const authors = [
  { name: "Zewei Deng", affiliations: [1] },
  { name: "Liyan Xie", affiliations: [1] },
  { name: "Muhammad Siddeek", affiliations: [2] },
  { name: "Mohamed Seif", affiliations: [3] },
  { name: "Andrea J. Goldsmith", affiliations: [4] },
  { name: "H. Vincent Poor", affiliations: [5] },
  { name: "Mengdi Wang", affiliations: [5] },
];

const affiliations = [
  "Department of Industrial and Systems Engineering, University of Minnesota",
  "Google",
  "Department of Computer Science and Engineering, Oakland University",
  "Stony Brook University",
  "Princeton University",
];

const modelFamilies = [
  { name: "Qwen3-8B", organization: "Qwen", logo: "./assets/model-logos/qwen.png" },
  { name: "Mistral-7B", organization: "Mistral AI", logo: "./assets/model-logos/mistral.png" },
  { name: "OPT-125M", organization: "Meta AI", logo: "./assets/model-logos/meta.png" },
];

const methodSteps = [
  {
    title: "ECC-constrained watermarking",
    text:
      "Generated tokens are mapped into structural bits through a vocabulary partition. " +
      "Each local block is encouraged to satisfy a joint VT and Hamming feasible codeword constraint.",
  },
  {
    title: "Boundary-aware block recovery",
    text:
      "A separate boundary-anchor bucket closes structural blocks, allowing the detector to parse edited text back into local watermark blocks.",
  },
  {
    title: "Post-edit decoding",
    text:
      "The detector globally parses the observed structural sequence and measures each parsed block's edit distance to the feasible ECC set.",
  },
  {
    title: "Localization signal",
    text:
      "Blocks whose distance exceeds a tolerance threshold are flagged as suspicious, and the decoder returns candidate edit locations inside those blocks.",
  },
];

function App() {
  return (
    <main>
      <Nav />
      <Hero />
      <Motivation />
      <Method />
      <Results />
      <InteractiveDemo />
      <Citation />
    </main>
  );
}

function Nav() {
  return (
    <nav className="nav">
      <a className="brand" href="#top">ECC-IW</a>
      <div className="navLinks">
        <a href="#method">Method</a>
        <a href="#results">Results</a>
        <a href="#demo">Walkthrough</a>
        <a href={PAPER_URL} title="Replace PAPER_URL with the arXiv URL for the public release">Paper</a>
        <a href={GITHUB_URL} target="_blank" rel="noreferrer">GitHub</a>
        <a href="#citation">Citation</a>
      </div>
    </nav>
  );
}

function Hero() {
  return (
    <section id="top" className="hero">
      <div className="heroText">
        <p className="eyebrow">ECC integrity watermark</p>
        <h1>ECC-IW: Local Integrity Checking for Watermarked LLM Outputs via Error-Correcting Codes</h1>
        <div className="authorBlock" aria-label="Authors and affiliations">
          <div className="authorList">
            {authors.map((author) => (
              <span key={author.name}>
                {author.name}
                <sup>{author.affiliations.join(",")}</sup>
              </span>
            ))}
          </div>
          <div className="affiliationList">
            {affiliations.map((affiliation, index) => (
              <span key={affiliation}>
                <b>{index + 1}</b>
                {affiliation}
              </span>
            ))}
          </div>
          <p className="affiliationNote">
            Mohamed Seif and Andrea J. Goldsmith contributed to this work while at Princeton University.
          </p>
        </div>
        <p className="lead">
          We study how to detect and localize sparse post-generation edits in watermarked LLM
          outputs. Instead of only asking whether a text is watermarked, our detector asks where
          suspicious local modifications may have occurred.
        </p>
        <div className="heroActions">
          <a className="button primary" href="#results">View results</a>
          <a className="button secondary" href="#demo">Preview walkthrough</a>
        </div>
      </div>
      <div className="heroPanel" aria-label="Pipeline summary">
        <div className="pipelineNode">Watermarked generation</div>
        <div className="pipelineArrow">{"->"}</div>
        <div className="pipelineNode warning">Sparse edit</div>
        <div className="pipelineArrow">{"->"}</div>
        <div className="pipelineNode">ECC detector</div>
        <div className="pipelineArrow">{"->"}</div>
        <div className="pipelineNode accent">Suspicious blocks</div>
      </div>
    </section>
  );
}

function Motivation() {
  return (
    <section className="section split">
      <div>
        <p className="eyebrow">Motivation</p>
        <h2>Watermark detection is not enough when edits are local.</h2>
      </div>
      <div className="bodyText">
        <p>
          Existing watermark detectors largely focus on document- or segment-level attribution:
          deciding whether a text was generated by an LLM. In practice, however, a watermarked
          response may be locally edited after generation while the overall watermark signal remains
          detectable.
        </p>
        <p>
          Small edits can change factuality, certainty, stance, or source attribution. Our goal is
          local integrity checking: given only the observed edited text and the watermark key, identify
          suspicious watermark blocks and provide candidate edit locations for downstream review.
        </p>
      </div>
    </section>
  );
}

function Method() {
  return (
    <section id="method" className="section sectionDivider">
      <div className="sectionHeader">
        <p className="eyebrow">Method overview</p>
        <h2>Embedding local ECC structure into generated text</h2>
        <p>
          The watermark maps tokens into structural bits and boundary anchors. Local blocks are
          constrained by a feasible codeword set C = V_a(n) intersect H, combining VT sensitivity to
          insertion/deletion edits with Hamming parity sensitivity to substitutions.
        </p>
      </div>

      <div className="figureGrid">
        <figure>
          <img src="./assets/watermark_pipeline.png" alt="Watermark embedding pipeline" />
          <figcaption>Watermark embedding pipeline.</figcaption>
        </figure>
        <figure>
          <img src="./assets/decode_pipeline.png" alt="ECC decoding and localization pipeline" />
          <figcaption>Decoding and edit-localization pipeline.</figcaption>
        </figure>
      </div>

      <div className="methodGrid">
        {methodSteps.map((step) => (
          <article className="methodCard" key={step.title}>
            <h3>{step.title}</h3>
            <p>{step.text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function Results() {
  const [activeResult, setActiveResult] = useState("local");

  return (
    <section id="results" className="section results">
      <div className="sectionHeader">
        <p className="eyebrow">Expanded evaluation</p>
        <h2>How ECC-IW performs across five evaluation settings</h2>
        <p>
          The current archive evaluates 18 closed ECC blocks per sequence across three model
          families and four soft-bias settings. Local detection, text quality, global verification,
          the Combinatorial Watermark (CW) comparison, and Qwen3-guided edits are reported separately.
        </p>
      </div>

      <div className="modelFamilyStrip" aria-label="Evaluated model families">
        {modelFamilies.map((model) => (
          <div className="modelFamilyBadge" key={model.name}>
            <img src={model.logo} alt={`${model.organization} logo`} />
            <span>
              <strong>{model.name}</strong>
              <small>{model.organization}</small>
            </span>
          </div>
        ))}
      </div>

      <div className="resultCards" role="tablist" aria-label="Evaluation result views">
        {resultCards.map((card) => (
          <button
            className={activeResult === card.key ? "resultCard active" : "resultCard"}
            key={card.key}
            onClick={() => setActiveResult(card.key)}
            role="tab"
            aria-selected={activeResult === card.key}
            aria-controls="result-workbench"
          >
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.detail}</p>
          </button>
        ))}
      </div>

      <div id="result-workbench" className="resultWorkbench" role="tabpanel">
        {activeResult === "local" && <LocalDetectionResult />}
        {activeResult === "quality" && <QualityResult />}
        {activeResult === "global" && <GlobalVerificationResult />}
        {activeResult === "cw" && <CombinatorialResult />}
        {activeResult === "llm" && <LlmEditResult />}
      </div>

      <p className="archiveNote">Displayed values: {archiveVersion}</p>
    </section>
  );
}

function LocalDetectionResult() {
  return (
    <ResultPanel
      eyebrow="Synthetic mixed edits"
      title="Cross-model block detection and candidate localization"
      note="Macro averages over 12 attack settings. Candidate reduction is measured relative to 16 admissible within-block edit locations: 7 payload positions, 8 insertion gaps, and 1 boundary position."
    >
      <DataTable
        label="Cross-model local detection"
        columns={[
          ["Model", (r) => r.model], ["δ", (r) => r.delta],
          ["Clean feasible", (r) => `${r.feasible.toFixed(2)}/18`],
          ["Block TPR", (r) => fmt(r.tpr)], ["Block FAR", (r) => fmt(r.far)],
          ["Event cov.", (r) => fmt(r.coverage)],
          ["Cand. fraction", (r) => fmt(r.candidateFraction, 3)],
          ["Reduction", (r) => fmt(r.searchReduction, 3)],
        ]}
        rows={localDetection}
      />
    </ResultPanel>
  );
}

function QualityResult() {
  return (
    <ResultPanel
      eyebrow="Adaptive generation"
      title="Adaptive codeword realization reduces PPL across all three models"
      note="Relative reduction in conditional PPL at δ = 50, comparing adaptive generation with the same watermarked setting without adaptation. Lower PPL is better."
    >
      <DataTable
        label="Adaptive generation PPL improvement"
        columns={[
          ["Model", (r) => r.model],
          ["Conditional PPL reduction", (r) => `${(r.reduction * 100).toFixed(1)}%`, "methodColumn"],
        ]}
        rows={adaptiveAblation}
      />
    </ResultPanel>
  );
}

function GlobalVerificationResult() {
  return (
    <ResultPanel
      eyebrow="Final-text-only verification"
      title="A global ECC score separates watermarked text from two negative sources"
      note="Higher scores indicate stronger ECC-IW watermark evidence. The verifier receives only final text, tokenizer, model partition, and ECC configuration. Evaluation uses 256 watermarked outputs, 256 matched unwatermarked outputs, and 251 human LFQA answers."
    >
      <div className="scoreDefinition">
        <code>S(s) = 1 / (1 + C(s) / max(1, B_estimated))</code>
        <p>C(s) combines nearest-codeword payload distance, boundary mismatches, unmatched symbols, and the parsed-versus-estimated block-count penalty.</p>
      </div>
      <DataTable
        label="Global verification"
        columns={[
          ["Model", (r) => r.model], ["δ", (r) => r.delta], ["AUC", (r) => fmt(r.auc)],
          ["TPR at empirical FPR = 0", (r) => fmt(r.tprAtZeroFpr)],
          ["Mean score: watermarked", (r) => fmt(r.wm, 3), "methodColumn"],
          ["Mean score: unwatermarked LLM", (r) => fmt(r.llm, 3)],
          ["Mean score: human", (r) => fmt(r.human, 3)],
        ]}
        rows={globalVerification}
      />
    </ResultPanel>
  );
}

function CombinatorialResult() {
  return (
    <ResultPanel
      eyebrow="Closest-prior comparison"
      title="ECC versus Combinatorial Watermark (CW) on Qwen3"
      note="Both methods use the same prompts, generation settings, attacks, and block-level TPR/FAR protocol. CW retains its original clean-watermark threshold calibration."
    >
      <DataTable
        label="ECC versus Combinatorial Watermark"
        columns={[
          ["CW pattern", (r) => r.pattern], ["δ", (r) => r.delta],
          ["ECC-IW TPR", (r) => fmt(r.eccTpr), "methodColumn"],
          ["ECC-IW FAR", (r) => fmt(r.eccFar), "methodColumn"],
          ["CW TPR", (r) => fmt(r.cwTpr)], ["CW FAR", (r) => fmt(r.cwFar)],
          ["Pattern adherence", (r) => fmt(r.adherence, 3)],
        ]}
        rows={combinatorialComparison}
      />
    </ResultPanel>
  );
}

function LlmEditResult() {
  return (
    <ResultPanel
      eyebrow="Natural-language edits"
      title="Balanced Qwen3/LFQA edit evaluation"
      note="N = 144: 72 examples per bias and 72 per intent, with 12 examples for each bias × motivation stratum. The detector localizes structural change rather than classifying intent."
    >
      <DataTable
        label="Balanced Qwen3 LLM edit results"
        columns={[
          ["δ", (r) => r.delta], ["Intent", (r) => r.intent], ["N", (r) => r.n],
          ["Edited blocks", (r) => r.editedBlocks.toFixed(2)], ["Block TPR", (r) => fmt(r.tpr)],
          ["Block FAR", (r) => fmt(r.far)], ["Event cov.", (r) => fmt(r.coverage)],
        ]}
        rows={llmEditResults}
      />
    </ResultPanel>
  );
}

function ResultPanel({ eyebrow, title, note, children }) {
  return (
    <article className="resultPanel">
      <div className="resultPanelHeader"><span>{eyebrow}</span><h3>{title}</h3></div>
      {children}
      <p className="resultNote">{note}</p>
    </article>
  );
}

function DataTable({ label, columns, rows }) {
  return (
    <div className="dataTableWrap">
      <table className="dataTable" aria-label={label}>
        <thead>
          <tr>
            {columns.map(([heading, , className]) => (
              <th className={className} key={heading}>{heading}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`${label}-${rowIndex}`}>
              {columns.map(([heading, render, className]) => (
                <td className={className} key={heading}>{render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function fmt(value, digits = 4) {
  return Number(value).toFixed(digits);
}

const demoSteps = [
  "Source answer",
  "Sparse edit",
  "Bucket view",
  "ECC decoding",
  "Localized alarm",
];

function InteractiveDemo() {
  const [exampleIndex, setExampleIndex] = useState(0);
  const [stepIndex, setStepIndex] = useState(0);
  const [stepHeight, setStepHeight] = useState(null);
  const [activeIntent, setActiveIntent] = useState(demoExamples[0]?.intentLabel ?? "benign");
  const panelRefs = useRef([]);
  const example = demoExamples[exampleIndex];
  const groupedExamples = useMemo(() => {
    return demoExamples.reduce((groups, item, idx) => {
      const intent = item.intentLabel;
      const motivation = item.motivation;
      groups[intent] ??= {};
      groups[intent][motivation] ??= [];
      groups[intent][motivation].push({ ...item, originalIndex: idx });
      return groups;
    }, {});
  }, []);
  const primaryFlag = useMemo(
    () => example.flaggedBlocks.find((block) => block.isGroundTruthEdited) ?? example.flaggedBlocks[0],
    [example],
  );

  useLayoutEffect(() => {
    const panel = panelRefs.current[stepIndex];
    if (!panel) return undefined;

    const updateHeight = () => setStepHeight(panel.getBoundingClientRect().height);
    updateHeight();

    const observer = new ResizeObserver(updateHeight);
    observer.observe(panel);
    return () => observer.disconnect();
  }, [exampleIndex, stepIndex]);

  return (
    <section id="demo" className="section demo">
      <div className="sectionHeader">
        <p className="eyebrow">Interactive walkthrough</p>
        <h2>Precomputed edit-localization replay</h2>
        <p>
          This walkthrough replays real examples from the latest LLM-guided sparse-edit run. It does
          not run a live model in the browser; instead, it shows representative examples from each
          edit intent, along with saved token buckets, structural symbols, detector parse, and
          localized block alarms produced by the evaluation pipeline.
        </p>
      </div>

      <div className="demoSelector" aria-label="Choose a precomputed example">
        <div className="intentTabs">
          {Object.keys(groupedExamples).map((intent) => (
            <button
              className={intent === activeIntent ? "intentTab active" : "intentTab"}
              key={intent}
              onClick={() => {
                setActiveIntent(intent);
                const firstGroup = Object.values(groupedExamples[intent])[0] ?? [];
                if (firstGroup[0]) {
                  setExampleIndex(firstGroup[0].originalIndex);
                  setStepIndex(0);
                }
              }}
            >
              <span>{intent}</span>
              {Object.values(groupedExamples[intent]).flat().length} examples
            </button>
          ))}
        </div>

        <div className="motivationGroups">
          {Object.entries(groupedExamples[activeIntent] ?? {}).map(([motivation, items]) => (
            <div className="motivationGroup" key={motivation}>
              <div className="motivationHeader">
                <span>{motivation.replace("_", " ")}</span>
                <small>{items.length} cases</small>
              </div>
              <div className="caseButtons">
                {items.map((item, localIdx) => (
                  <button
                    className={item.originalIndex === exampleIndex ? "caseButton active" : "caseButton"}
                    key={item.id}
                    onClick={() => {
                      setExampleIndex(item.originalIndex);
                      setStepIndex(0);
                    }}
                  >
                    <strong>Case {localIdx + 1}</strong>
                    <span>seq {item.sequenceIndex}</span>
                    <small>
                      δ {item.logitBias} · TPR {item.metrics.blockTpr?.toFixed(2) ?? "n/a"} · FAR{" "}
                      {item.metrics.blockFar?.toFixed(2) ?? "n/a"}
                    </small>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="demoStage">
        <aside className="demoRail">
          {demoSteps.map((step, idx) => (
            <button
              className={idx === stepIndex ? "railStep active" : idx < stepIndex ? "railStep done" : "railStep"}
              key={step}
              onClick={() => setStepIndex(idx)}
            >
              <span>{idx + 1}</span>
              {step}
            </button>
          ))}
        </aside>

        <div className="demoCanvas">
          <div className="demoMeta">
            <span>Sequence {example.sequenceIndex}</span>
            <span>δ = {example.logitBias}</span>
            <span>{example.motivation.replace("_", " ")}</span>
            <span>{example.intentLabel}</span>
          </div>

          <div className="questionCard">
            <strong>Question</strong>
            <p>{example.question}</p>
          </div>

          <div
            className="stepViewport"
            style={stepHeight == null ? undefined : { height: `${stepHeight}px` }}
          >
              <div className="stepPanels" style={{ transform: `translateX(-${stepIndex * 100}%)` }}>
                <SourcePanel example={example} panelRef={(node) => { panelRefs.current[0] = node; }} />
                <EditPanel example={example} panelRef={(node) => { panelRefs.current[1] = node; }} />
                <BucketPanel example={example} panelRef={(node) => { panelRefs.current[2] = node; }} />
                <DecodePanel block={primaryFlag} panelRef={(node) => { panelRefs.current[3] = node; }} />
                <AlarmPanel example={example} panelRef={(node) => { panelRefs.current[4] = node; }} />
              </div>
          </div>

          <div className="demoControls">
            <button onClick={() => setStepIndex(Math.max(0, stepIndex - 1))} disabled={stepIndex === 0}>
              Previous
            </button>
            <div className="progressDots">
              {demoSteps.map((step, idx) => (
                <button
                  aria-label={step}
                  className={idx === stepIndex ? "dot active" : "dot"}
                  key={step}
                  onClick={() => setStepIndex(idx)}
                />
              ))}
            </div>
            <button
              onClick={() => setStepIndex(Math.min(demoSteps.length - 1, stepIndex + 1))}
              disabled={stepIndex === demoSteps.length - 1}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

function SourcePanel({ example, panelRef }) {
  return (
    <article className="stepPanel" ref={panelRef}>
      <PanelHeader label="Step 1" title="Start from a watermarked LFQA answer" />
      <TextCompare
        leftTitle="Watermarked source answer"
        leftText={example.sourceAnswer}
        rightTitle="Edited answer preview"
        rightText={example.editedAnswer}
        mutedRight
      />
      <MetricStrip example={example} />
    </article>
  );
}

function EditPanel({ example, panelRef }) {
  return (
    <article className="stepPanel" ref={panelRef}>
      <PanelHeader label="Step 2" title="Show the edited sequence and the local edit motives" />
      <HighlightedAnswer text={example.editedAnswer} edits={example.edits} />
      <div className="editTraceGrid">
        {example.edits.map((edit, idx) => (
          <div className="editTraceCard" key={`${edit.op}-${edit.anchor}-${idx}`}>
            <span className="editOp">{edit.op}</span>
            <h3>
              {edit.originalText || "(gap)"} {"->"} {edit.newContent}
            </h3>
            <p>{edit.reason}</p>
            <div className="traceLine">
              <span>token/gap {edit.anchor}</span>
              <span>source block {edit.anchorBlock ?? "?"}</span>
              <span>detector block {edit.detectorBlock ?? "?"}</span>
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

function BucketPanel({ example, panelRef }) {
  return (
    <article className="stepPanel" ref={panelRef}>
      <PanelHeader label="Step 3" title="Trace each edit into the watermark structure" />
      <p className="panelText">
        Each edited token is first mapped to a vocabulary bucket. Bucket 0 and 1 become payload bits
        inside an ECC block; bucket 2 is a boundary anchor that closes a block. The detector later
        parses this structural sequence and checks whether each block still looks like a feasible
        VT+Hamming codeword.
      </p>
      <div className="bucketLegend">
        <span className="bucketMini bucket0">B0 = payload bit 0</span>
        <span className="bucketMini bucket1">B1 = payload bit 1</span>
        <span className="bucketMini bucket2">B2 = boundary anchor</span>
      </div>
      <div className="structureTraceList">
        {example.edits.map((edit, idx) => (
          <div className="structureTraceCard" key={`${edit.op}-${edit.anchor}-${idx}`}>
            <div className="traceSource">
              <span className="traceLabel">Edited token</span>
              <strong>{edit.newContent || edit.originalText || "(inserted text)"}</strong>
              <small>
                token/gap {edit.anchor}; source surface "{edit.anchorToken?.surface ?? "n/a"}"
              </small>
            </div>
            <div className="traceArrow">{"->"}</div>
            <TraceNode
              label="Edited bucket sequence"
              value={(edit.bucketIds ?? [edit.anchorToken?.bucketId]).map((value) => `B${value ?? "?"}`).join(" · ")}
              detail={edit.bucketMeaning}
              tone="bucketSequenceNode"
            />
            <div className="traceArrow">{"->"}</div>
            <TraceNode
              label="ECC block"
              value={`block ${edit.anchorBlock ?? "?"}`}
              detail={`structural index ${edit.anchorToken?.structuralIndex ?? "?"}`}
            />
            <div className="traceArrow">{"->"}</div>
            <TraceNode
              label="Detector alarm"
              value={`block ${edit.detectorBlock ?? "?"}`}
              detail={`payload distance ${edit.payloadDistance ?? "n/a"}`}
              tone="alarmNode"
            />
            <p className="traceReason">{edit.reason}</p>
            <p className="traceSnippet">
              Detector snippet: <mark>{edit.detectorSnippet || "n/a"}</mark>
            </p>
          </div>
        ))}
      </div>
    </article>
  );
}

function TraceNode({ label, value, detail, tone = "" }) {
  return (
    <div className={`traceNode ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function HighlightedAnswer({ text, edits }) {
  const pieces = buildHighlightedPieces(text, edits);
  return (
    <div className="highlightedAnswer">
      <strong>Edited answer with local modifications highlighted</strong>
      <p>
        {pieces.map((piece, idx) =>
          piece.edit ? (
            <mark className={`editMark mark${piece.editIndex % 3}`} key={`${piece.text}-${idx}`}>
              {piece.text}
            </mark>
          ) : (
            <span key={`${piece.text}-${idx}`}>{piece.text}</span>
          ),
        )}
      </p>
    </div>
  );
}

function buildHighlightedPieces(text, edits) {
  const ranges = [];
  for (const [editIndex, edit] of edits.entries()) {
    if (
      Number.isInteger(edit.highlightStart) &&
      Number.isInteger(edit.highlightEnd) &&
      edit.highlightStart >= 0 &&
      edit.highlightEnd > edit.highlightStart &&
      edit.highlightEnd <= text.length
    ) {
      ranges.push({ start: edit.highlightStart, end: edit.highlightEnd, editIndex });
      continue;
    }
    const needle = (edit.newContent || edit.originalText || "").trim();
    if (!needle) continue;
    let start = text.indexOf(needle);
    while (start >= 0 && ranges.some((range) => start < range.end && start + needle.length > range.start)) {
      start = text.indexOf(needle, start + needle.length);
    }
    if (start >= 0) {
      ranges.push({ start, end: start + needle.length, editIndex });
    }
  }
  ranges.sort((a, b) => a.start - b.start);
  const pieces = [];
  let cursor = 0;
  for (const range of ranges) {
    if (range.start > cursor) pieces.push({ text: text.slice(cursor, range.start) });
    pieces.push({ text: text.slice(range.start, range.end), edit: true, editIndex: range.editIndex });
    cursor = range.end;
  }
  if (cursor < text.length) pieces.push({ text: text.slice(cursor) });
  return pieces;
}

function DecodePanel({ block, panelRef }) {
  return (
    <article className="stepPanel" ref={panelRef}>
      <PanelHeader label="Step 4" title={`Decode parsed block ${block.blockId}`} />
      <p className="panelText">
        The detector parses the observed structural sequence into ECC blocks, then compares each
        observed payload segment to the nearest feasible VT+Hamming codeword. This block exceeds
        the tolerance threshold and is raised as an alarm.
      </p>
      <div className="decodeGrid">
        <CodeVector title="Observed structural segment" values={block.observedSegment} tone="observed" />
        <CodeVector title="Nearest decoded codeword" values={block.decodedCodeword} tone="decoded" />
        <div className="distanceCard">
          <span>Payload distance</span>
          <strong>{block.payloadDistance ?? "n/a"}</strong>
          <p>Boundary: {block.boundaryState ?? "unknown"}</p>
        </div>
      </div>
      <CandidateList locations={block.candidateLocations} />
    </article>
  );
}

function AlarmPanel({ example, panelRef }) {
  return (
    <article className="stepPanel" ref={panelRef}>
      <PanelHeader label="Step 5" title="Localize suspicious blocks in natural language" />
      <div className="blockMap">
        {Array.from({ length: example.numBlocks ?? 18 }, (_, blockId) => {
          const predicted = example.predictedBlocks.includes(blockId);
          const edited = example.gtBlocks.includes(blockId);
          return (
            <div
              className={predicted ? (edited ? "blockCell hit" : "blockCell alarm") : edited ? "blockCell missed" : "blockCell"}
              key={blockId}
            >
              {blockId}
            </div>
          );
        })}
      </div>
      <div className="snippetGrid">
        {example.flaggedBlocks.map((block) => (
          <div className={block.isGroundTruthEdited ? "snippetCard hit" : "snippetCard"} key={`${block.blockId}-${block.parsedBlockIndex}`}>
            <span>Block {block.blockId}</span>
            <p>{block.snippet}</p>
          </div>
        ))}
      </div>
      <p className="legendText">
        Green blocks are detector alarms that overlap true edited blocks; orange blocks are detector
        alarms outside the edited locations; red outline marks a true edited block missed by this example.
      </p>
    </article>
  );
}

function PanelHeader({ label, title }) {
  return (
    <div className="panelHeader">
      <span>{label}</span>
      <h3>{title}</h3>
    </div>
  );
}

function TextCompare({ leftTitle, leftText, rightTitle, rightText, mutedRight = false }) {
  return (
    <div className="textCompare">
      <div>
        <strong>{leftTitle}</strong>
        <p>{leftText}</p>
      </div>
      <div className={mutedRight ? "mutedPreview" : ""}>
        <strong>{rightTitle}</strong>
        <p>{rightText}</p>
      </div>
    </div>
  );
}

function MetricStrip({ example }) {
  return (
    <div className="metricStrip">
      <span>GT edited blocks: {example.gtBlocks.join(", ")}</span>
      <span>Predicted alarms: {example.predictedBlocks.join(", ")}</span>
      <span>TPR {example.metrics.blockTpr.toFixed(2)}</span>
      <span>FAR {example.metrics.blockFar.toFixed(2)}</span>
    </div>
  );
}

function CodeVector({ title, values, tone }) {
  return (
    <div className="codeVector">
      <strong>{title}</strong>
      <div>
        {(values ?? []).map((value, idx) => (
          <span className={`bit ${tone}`} key={`${title}-${idx}`}>
            {value}
          </span>
        ))}
      </div>
    </div>
  );
}

function CandidateList({ locations }) {
  return (
    <div className="candidateList">
      <strong>Candidate edit-location set</strong>
      <div>
        {(locations ?? []).map((loc, idx) => (
          <span key={`${loc[0]}-${loc[1]}-${idx}`}>
            {loc[0]} {loc[1]}
          </span>
        ))}
      </div>
    </div>
  );
}

function Citation() {
  const [referencesExpanded, setReferencesExpanded] = useState(false);
  const [copyStatus, setCopyStatus] = useState("Copy BibTeX");

  async function copyBibtex() {
    try {
      await navigator.clipboard.writeText(BIBTEX);
      setCopyStatus("Copied");
      window.setTimeout(() => setCopyStatus("Copy BibTeX"), 1800);
    } catch {
      setCopyStatus("Copy failed");
      window.setTimeout(() => setCopyStatus("Copy BibTeX"), 1800);
    }
  }

  return (
    <section id="citation" className="section citation">
      <div className="sectionHeader">
        <p className="eyebrow">Paper and references</p>
        <h2>Citation</h2>
      </div>
      <div className="citationCode">
        <button onClick={copyBibtex} type="button" aria-live="polite">
          {copyStatus}
        </button>
        <pre>{BIBTEX}</pre>
      </div>
      <div className="referencesToolbar">
        <h3>
          References <span>{paperReferences.length} cited works</span>
        </h3>
        <button
          aria-controls="paper-references"
          aria-expanded={referencesExpanded}
          onClick={() => setReferencesExpanded((expanded) => !expanded)}
        >
          {referencesExpanded ? "Collapse references" : "View all references"}
        </button>
      </div>
      <div className="referencesFrame">
        <div
          className={referencesExpanded ? "referenceGrid expanded" : "referenceGrid"}
          id="paper-references"
        >
          {paperReferences.map((reference, index) => (
            <article className="referenceItem" key={reference.key}>
              <span className="referenceNumber">[{index + 1}]</span>
              <div>
                <strong>{reference.title}</strong>
                <p>
                  {reference.authors} · {reference.venue ? `${reference.venue}, ` : ""}
                  {reference.year}
                </p>
              </div>
            </article>
          ))}
        </div>
        {!referencesExpanded && <div className="referenceFade" aria-hidden="true" />}
      </div>
    </section>
  );
}

export default App;
