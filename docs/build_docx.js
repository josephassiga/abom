const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, TableOfContents, HeadingLevel,
  BorderStyle, WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak,
} = require("/opt/homebrew/lib/node_modules/docx");

// ---- palette ----
const NAVY = "1F3864";
const BLUE = "2E5496";
const LIGHT = "D9E2F3";
const GREY = "595959";
const BORDER = "BFBFBF";
const HEADERFILL = "1F3864";

const CONTENT_W = 9360; // US Letter, 1" margins

// ---- helpers ----
const border = { style: BorderStyle.SINGLE, size: 4, color: BORDER };
const cellBorders = { top: border, bottom: border, left: border, right: border };

function runs(text) {
  // Convert simple **bold** segments into TextRuns
  const parts = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return parts.map((p) =>
    p.startsWith("**") && p.endsWith("**")
      ? new TextRun({ text: p.slice(2, -2), bold: true })
      : new TextRun(p)
  );
}

function para(text, opts = {}) {
  return new Paragraph({
    children: runs(text),
    spacing: { after: 120, line: 276 },
    ...opts,
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 80, line: 264 },
    children: runs(text),
  });
}

function numbered(text, ref = "numbers") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 80, line: 264 },
    children: runs(text),
  });
}

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
}

function headerCell(text, w) {
  return new TableCell({
    borders: cellBorders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: BLUE, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: "FFFFFF" })] })],
  });
}

function bodyCell(text, w, fill) {
  return new TableCell({
    borders: cellBorders,
    width: { size: w, type: WidthType.DXA },
    ...(fill ? { shading: { fill, type: ShadingType.CLEAR } } : {}),
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ spacing: { after: 0 }, children: runs(text) })],
  });
}

function table(headers, rows, widths) {
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => headerCell(h, widths[i])),
  });
  const bodyRows = rows.map((r, ri) =>
    new TableRow({
      children: r.map((c, i) => bodyCell(c, widths[i], ri % 2 === 1 ? "F2F5FB" : undefined)),
    })
  );
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [headerRow, ...bodyRows],
  });
}

function spacer() {
  return new Paragraph({ spacing: { after: 60 }, children: [] });
}

// ---- document content ----
const children = [];

// Title block
children.push(
  new Paragraph({
    spacing: { before: 2200, after: 0 },
    alignment: AlignmentType.LEFT,
    children: [new TextRun({ text: "ABOM — The Agent", bold: true, size: 52, color: NAVY, font: "Arial" })],
  }),
  new Paragraph({
    spacing: { after: 200 },
    children: [new TextRun({ text: "Bill of Materials", bold: true, size: 52, color: NAVY, font: "Arial" })],
  }),
  new Paragraph({
    spacing: { after: 400 },
    children: [new TextRun({ text: "A signed, standard, tamper-evident record of what every AI agent is — and what it did.", italics: true, size: 26, color: BLUE })],
  }),
  new Paragraph({
    border: { top: { style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 8 } },
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text: "Founding strategy  ·  v3.0", bold: true, size: 24, color: GREY })],
  }),
  new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Company: ABOM · abom.ai", size: 22, color: GREY })] }),
  new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "CONFIDENTIAL — for internal use in company formation", size: 22, color: GREY, bold: true })] }),
  new Paragraph({ children: [new PageBreak()] }),
);

// TOC
children.push(
  new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "Contents", bold: true, size: 32, color: NAVY })] }),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),
);

// 0. What changed
children.push(h1("0. What changed (v2 → v3)"));
children.push(para("v2 framed the company as a **production control plane** for agentic AI — own the reliability runtime, govern agent fleets. Strong, but it competed in a crowded, capability-led race and made trust depend on a vendor's reputation. v3 makes a sharper, more defensible bet on the layer underneath every agent: **accountability.**"));
children.push(table(
  ["v2 — control plane", "v3 — Agent Bill of Materials"],
  [
    ["Make the agent better and more reliable", "Make the agent legible and attestable — a signed, standard record of what it is and did"],
    ["Trust rests on a vendor's reputation", "Trust is cryptographic, not reputational — tamper-evident and verifiable"],
    ["Compete in a crowded, capability-led race", "Define the standard for a layer no one owns; whoever defines it becomes infrastructure"],
    ["Reliability runtime as the product", "The same tamper-evident chain becomes the runtime substrate of an ABOM"],
    ["Win on engineering depth", "Win on neutrality + the standard + the Notary + completeness from runtime position"],
  ],
  [4680, 4680]
));
children.push(spacer());
children.push(para("The reliability/audit machinery from v2 isn't discarded: the tamper-evident chain we already built **is** the runtime substrate of an ABOM. We re-center on the artifact, the standard, and the neutral notary around it. The single most important shift: **stop trying to make the agent better — make it answerable.**"));

// 1. Executive summary
children.push(h1("1. Executive summary"));
children.push(para("Agentic AI is moving into production inside regulated institutions, and a question no one can answer well today is about to become a compliance requirement: **\"What is this agent made of, and what exactly did it do?\"** Risk officers, auditors, and regulators need a verifiable account of every model, tool, prompt, data source, and policy an agent used — and of every consequential decision it took. They have logs they must trust; they do not have a **signed, standard, tamper-evident bill of materials.**"));
children.push(para("**ABOM is the Agent Bill of Materials**: a standard format plus the tooling to generate, verify, and notarize it. Two artifacts:"));
children.push(bullet("**Composition Manifest** — the ingredients label: every model (with weight hashes), tool, prompt, data source, framework, and policy that makes up an agent. Signed at deploy time."));
children.push(bullet("**Action Provenance Record** — the flight recorder: for each consequential action, the inputs, model calls, tools invoked, data classification, policy decisions, and approvals — hash-chained and tamper-evident, linked back to the composition."));
children.push(para("Around that standard sit three products: **abom-gen** (open-source generator/SDK that auto-emits ABOMs), **abom-verify** (checks an ABOM against policy — the part risk teams pay for), and **the Notary** (a signed, queryable registry — the neutral system of record auditors and regulators query). We open-source the format and the generator to win the standard, and monetize verification and the notary."));
children.push(para("We extend the emerging **CycloneDX ML-BOM** standard to full agents and runtime provenance rather than forking it. We land in **European regulated financial services**, ~12–18 months ahead of a mandate the SBOM precedent makes nearly inevitable. Underneath the software, this is a trust company — and the trust is **cryptographic, not reputational.**"));

// 2. Problem
children.push(h1("2. The problem"));
children.push(para("Agents are becoming autonomous black boxes inside institutions that are legally accountable for what software does. Three gaps:"));
children.push(para("**1 — Composition is opaque.** No one can say, in one signed document, which models/tools/prompts/data/policies an agent is actually built from — or prove the deployed agent matches what was approved."));
children.push(para("**2 — Actions are unaccountable.** When an agent makes a consequential decision, the evidence is scattered application logs the institution must **trust** — not a tamper-evident, portable record it can **verify** and hand to a regulator."));
children.push(para("**3 — The mandate is coming and no one is ready.** AI Act Art. 12 (record-keeping), DORA (evidence of ICT control), and NIST AI RMF all point at \"account for what your AI is and did.\" SBOM went from optional to mandated in three years; agent accountability is on the same trajectory, and the tooling doesn't exist."));
children.push(para("The market is racing to make agents **do more.** Almost no one is building the layer that makes an agent **answerable.** That is the gap."));

// 3. The product
children.push(h1("3. The product"));
children.push(h2("3.1 The two artifacts"));
children.push(para("**Composition Manifest** (static — what the agent **is**): every model with weight hashes, every tool with its scope and allowed endpoints, every system prompt by hash, every data source with its classification, and the policy engine — wrapped with deploy-time controls (egress deny-by-default, human-in-the-loop for consequential actions, EU residency) and an ed25519 signature from the notary."));
children.push(para("**Action Provenance Record** (runtime — what the agent **did**, per consequential action): the agent reference and composition hash, the run and sequence id, the decision, the retrieved inputs, the model calls (with token counts and output hashes), the tools invoked, the data touched and its classification, the policy decisions, and the human approval — each record carrying the previous record's hash so the chain is tamper-evident."));
children.push(para("The Action Provenance Record is the tamper-evident chain we already shipped, upgraded to a standard schema and linked to the composition by hash."));
children.push(h2("3.2 Three pieces around an open standard"));
children.push(table(
  ["Piece", "What it is", "Role"],
  [
    ["abom-gen", "SDK / agent-runtime hook that auto-emits both artifacts", "Open-source → drives adoption of the standard"],
    ["abom-verify", "Scanner that checks an ABOM against policy — no unapproved models, no PII to egress, every consequential action approved, deployed composition matches the signed manifest", "The product risk / compliance teams pay for"],
    ["The Notary", "Signed, queryable, tamper-evident registry of every ABOM across the org; exports to SIEM and regulators", "The neutral system of record — the can't-self-host moat"],
  ],
  [1900, 4260, 3200]
));

// 4. Why now
children.push(h1("4. Why now"));
children.push(bullet("**The precedent is proven.** SBOM went from nice-to-have to mandated (US EO 14028, EU Cyber Resilience Act). The institutional muscle memory exists."));
children.push(bullet("**The rail already exists.** CycloneDX shipped **ML-BOM** for models. ABOM is the obvious extension to full agents + runtime provenance. Extend the winner; don't fork the ecosystem."));
children.push(bullet("**The mandate is coming.** AI Act Art. 12, DORA, NIST AI RMF all converge on agent accountability. We arrive 12–18 months early."));
children.push(bullet("**Buildable now.** No formal-methods research required (unlike the proof-carrying endgame in §9). Step 0 — the tamper-evident chain — already runs."));

// 5. Moat
children.push(h1("5. Moat & defensibility"));
children.push(numbered("**Neutrality.** A bill of materials is inherently vendor-neutral — a position only an independent can hold. We sell no model and no agent."));
children.push(numbered("**The standard.** Formats are natural monopolies. If \"every regulated agent must emit an ABOM\" becomes true, there is one reference implementation."));
children.push(numbered("**The Notary.** Third-party independence cannot be self-hosted; the neutral, signed registry is the durable, monetizable asset."));
children.push(numbered("**Completeness from position.** A trustworthy runtime ABOM requires capturing **every** action — which means sitting in the agent runtime / control plane, where we already are. A bolt-on logger can't match that coverage."));

// 6. Competitive
children.push(h1("6. Competitive landscape"));
children.push(table(
  ["Player", "Position", "Why they don't own this"],
  [
    ["LLM observability (Langfuse, Arize, Helicone)", "Dashboards & traces for developers", "Built for debugging, not signed, regulator-grade, tamper-evident attestation. Wrong buyer, wrong assurances."],
    ["SBOM vendors (Anchore, etc.)", "Software supply-chain BOMs", "Don't model agents (models / tools / prompts / runtime decisions). Could extend in — so move fast on the agent layer."],
    ["Hyperscaler agent platforms", "Managed agent ops", "Cloud-locked and not neutral; can't be the sovereign, in-boundary, vendor-neutral attestor regulated buyers need."],
    ["Model vendors", "Sell a model", "Cannot credibly be the neutral bill-of-materials layer over all models. Natural partners."],
    ["GRC / audit tooling", "Compliance workflows", "Operate at the policy / paperwork layer, not at machine-checkable agent provenance. Integration targets."],
  ],
  [2500, 2700, 4160]
));
children.push(spacer());
children.push(para("**White space:** signed, standard, tamper-evident **runtime** provenance for agentic systems, generated where coverage is complete. No one owns it."));

// 7. Go-to-market
children.push(h1("7. Go-to-market"));
children.push(para("**Wedge: European regulated financial services.** Risk, compliance, and platform leaders facing AI Act / DORA evidence obligations, who cannot today answer the question below."));
children.push(new Paragraph({
  spacing: { before: 80, after: 160 },
  border: { left: { style: BorderStyle.SINGLE, size: 24, color: BLUE, space: 12 } },
  indent: { left: 240 },
  children: [new TextRun({ text: "\"Show me, in one signed document, exactly what every AI agent in our bank is made of — and every consequential thing it did — verifiable, and exportable to our SIEM and our regulator.\"", italics: true, size: 24, color: NAVY })],
}));
children.push(para("**Motion:** land a lighthouse via abom-gen on one high-stakes agent → produce a verified ABOM and catch a real policy violation in abom-verify → become the system of record (Notary) for that team → expand across agents and into adjacent regulated verticals. Open-source adoption of the format seeds the top of funnel beyond the wedge."));

// 8. Business model
children.push(h1("8. Business model"));
children.push(bullet("**Open-source:** the ABOM format and **abom-gen** — adoption is the strategy."));
children.push(bullet("**Paid:** **abom-verify** (certified policy verification, per agent / per workload) and **the Notary** (registry subscription, priced per deployment + capacity), with on-prem / air-gapped deployment and integration services into regulated estates."));
children.push(bullet("**Shape:** predictable, on-prem-friendly enterprise pricing; high retention once it is the system of record in compliance workflows."));

// 9. Roadmap arc
children.push(h1("9. Roadmap arc"));
children.push(para("**ABOM (now): accountability.** Record what the agent is and did. Buildable today."));
children.push(para("**→ Proof-Carrying Actions (later): prevention.** Escalate from **recording** an action to **gating** it on a machine-checkable proof that it satisfies policy before it runs — a proof is simply a stronger ABOM claim. The accountability record is the on-ramp to the verification endgame."));

// 10. Risks
children.push(h1("10. Risks & mitigations"));
children.push(table(
  ["Risk", "Why it matters", "Mitigation"],
  [
    ["Standard adoption is a coordination problem", "A format no one emits is worthless", "Extend CycloneDX (don't fork); win on best generator; anchor a regulated lighthouse who needs it for the deadline"],
    ["\"Isn't this just audit logging?\"", "Looks like observability, commoditises", "Lead with the signed standard schema + composition↔runtime linkage + policy verification + neutral notary — not logs"],
    ["Completeness of runtime capture", "A partial record isn't trustworthy", "Generate from inside the agent runtime / control plane, where we see every action"],
    ["Observability or SBOM vendors extend in", "Well-funded adjacents", "Regulated-grade signing, tamper-evidence, neutrality and in-boundary posture they aren't built for; move first on the standard"],
  ],
  [2700, 2700, 3960]
));

// 11. Immediate next steps
children.push(h1("11. Immediate next steps"));
children.push(numbered("Publish **ABOM v0.1** as a public schema that extends CycloneDX ML-BOM."));
children.push(numbered("Ship **abom-gen v0** — instrument one agent runtime to emit a signed Composition Manifest + Action Provenance chain (the MVP)."));
children.push(numbered("Ship **abom-verify v0** — one decidable policy check that catches a real violation (e.g. **unapproved model used** or **confidential data to egress**)."));
children.push(numbered("Sign a regulated financial-services lighthouse; produce their first verified ABOM."));
children.push(numbered("Stand up the Notary as the system of record and convert the lighthouse into a named reference."));

// 12. Messaging
children.push(h1("12. Website & messaging starter (abom.ai)"));
children.push(para("**Hero:** Know what your agents are made of — and what they did."));
children.push(para("**Subhead:** ABOM is the Agent Bill of Materials: a signed, standard, tamper-evident record of every model, tool, prompt, data source, and decision behind your AI agents. Built for regulated teams under the EU AI Act and DORA."));
children.push(para("**Value pillars**"));
children.push(bullet("**Standard.** Extends CycloneDX ML-BOM, open — the format adoption is built on."));
children.push(bullet("**Signed.** Tamper-evident and regulator-grade — trust that is cryptographic, not reputational."));
children.push(bullet("**Neutral.** Any model, any framework — we sell neither, so the bill of materials is impartial."));
children.push(bullet("**Yours.** Runs in your boundary; nothing leaves."));

// Disclaimer
children.push(new Paragraph({
  spacing: { before: 320, after: 0 },
  border: { top: { style: BorderStyle.SINGLE, size: 4, color: BORDER, space: 8 } },
  children: [new TextRun({ text: "ABOM is the company name and abom.ai the domain. This document is a strategic frame for company formation, not investment or legal advice; regulatory positioning should be validated with qualified counsel.", italics: true, size: 18, color: GREY })],
}));

// ---- assemble ----
const doc = new Document({
  creator: "ABOM founding team",
  title: "ABOM — The Agent Bill of Materials · Founding strategy v3.0",
  styles: {
    default: { document: { run: { font: "Arial", size: 21, color: "262626" } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Arial", color: NAVY },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: LIGHT, space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: BLUE },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 540, hanging: 280 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 540, hanging: 280 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        spacing: { after: 0 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BORDER, space: 6 } },
        tabStops: [{ type: "right", position: CONTENT_W }],
        children: [
          new TextRun({ text: "ABOM · The Agent Bill of Materials · abom.ai", size: 16, color: GREY }),
          new TextRun({ text: "\tConfidential", size: 16, color: GREY }),
        ],
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        spacing: { before: 0 },
        tabStops: [{ type: "right", position: CONTENT_W }],
        children: [
          new TextRun({ text: "Founding strategy · v3.0 · abom.ai", size: 16, color: GREY }),
          new TextRun({ text: "\tPage ", size: 16, color: GREY }),
          new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY }),
        ],
      })] }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("/Users/josephassiga/Desktop/aegis/ABOM_Strategy.docx", buffer);
  console.log("WROTE ABOM_Strategy.docx", buffer.length, "bytes");
});
