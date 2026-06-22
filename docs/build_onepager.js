const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, BorderStyle, WidthType, ShadingType, VerticalAlign,
} = require("/opt/homebrew/lib/node_modules/docx");

const NAVY = "1F3864", BLUE = "2E5496", LIGHT = "EAF0FA", GREY = "595959", BORDER = "BFBFBF";
const CONTENT_W = 9360;
const noBorder = { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } };

function t(text, opts = {}) { return new TextRun({ text, font: "Arial", ...opts }); }

function bul(text, color) {
  return new Paragraph({
    numbering: { reference: "b", level: 0 },
    spacing: { after: 40, line: 240 },
    children: [t(text, { size: 18, color: color || "262626" })],
  });
}
function lead(text, runsExtra) {
  return new Paragraph({ spacing: { after: 100, line: 252 }, children: [t(text, { size: 19, color: "262626" }), ...(runsExtra || [])] });
}
function sect(text) {
  return new Paragraph({
    spacing: { before: 120, after: 60 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: LIGHT, space: 2 } },
    children: [t(text.toUpperCase(), { size: 18, bold: true, color: BLUE, characterSpacing: 20 })],
  });
}

function panelCell(title, items, fill, w) {
  const kids = [new Paragraph({ spacing: { after: 60 }, children: [t(title, { size: 18, bold: true, color: NAVY })] })];
  items.forEach((it) => kids.push(new Paragraph({
    numbering: { reference: "b", level: 0 }, spacing: { after: 30, line: 234 },
    children: [t(it, { size: 17, color: "262626" })],
  })));
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: { fill, type: ShadingType.CLEAR },
    margins: { top: 120, bottom: 120, left: 160, right: 160 },
    verticalAlign: VerticalAlign.TOP,
    borders: noBorder,
    children: kids,
  });
}

const children = [];

// Header band
children.push(new Table({
  width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W],
  borders: noBorder,
  rows: [new TableRow({ children: [new TableCell({
    width: { size: CONTENT_W, type: WidthType.DXA },
    shading: { fill: NAVY, type: ShadingType.CLEAR },
    margins: { top: 160, bottom: 160, left: 200, right: 200 }, borders: noBorder,
    children: [
      new Paragraph({ spacing: { after: 20 }, children: [t("ABOM", { size: 30, bold: true, color: "FFFFFF", characterSpacing: 40 }), t("   ·   Lighthouse Design Partner Brief", { size: 18, color: "C9D6EC" })] }),
      new Paragraph({ children: [t("Know what your agents are made of — and what they did. Signed, standard, tamper-evident.", { size: 19, italics: true, color: "EAF0FA" })] }),
    ],
  })] })],
}));
children.push(new Paragraph({ spacing: { after: 80 }, children: [] }));

// The problem
children.push(sect("The question you can't answer today"));
children.push(lead("Agents are moving into production inside your institution, and a question your auditors and regulators will soon require is one no one can answer well: what is each agent made of, and what exactly did it do? You have scattered application logs you must trust — not a signed, standard, tamper-evident record you can verify and hand to a regulator. AI Act Art. 12, DORA, and NIST AI RMF all point at it; SBOM went from optional to mandated in three years, and agent accountability is on the same path."));

// The offer
children.push(sect("What we're offering a lighthouse partner"));
children.push(lead("A founding partnership to stand up ABOM — the Agent Bill of Materials — inside your environment, producing a signed, standard, tamper-evident record of one high-stakes agent: every model, tool, prompt, data source, and policy it is built from, and every consequential thing it did. You shape the standard; we earn your reference."));

// two-column: what you get / what we ask
children.push(new Table({
  width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [4680, 4680], borders: noBorder,
  rows: [new TableRow({ children: [
    panelCell("What you get", [
      "A verified ABOM for one high-stakes agent: a signed Composition Manifest (what it is) plus a hash-chained Action Provenance Record (what it did).",
      "abom-verify run against your policy — catching a real violation (e.g. an unapproved model, or confidential data heading to egress) in the first weeks.",
      "A tamper-evident system of record, exportable to your SIEM and your regulator, mapped to DORA and EU AI Act Art. 12 expectations.",
      "Direct influence over the open ABOM standard, and founder-level support throughout.",
      "Preferential founding-partner commercial terms, locked for the term.",
    ], LIGHT, 4680),
    panelCell("What we ask", [
      "One real, high-stakes agent already running (or about to) inside your boundary.",
      "Access to a small group of platform, risk, and compliance stakeholders.",
      "A joint success definition and a short pilot timeline.",
      "Reference rights — a named logo and a quote — once the first verified ABOM is produced.",
    ], "F4F6FB", 4680),
  ] })],
}));
children.push(new Paragraph({ spacing: { after: 60 }, children: [] }));

// The first artifact
children.push(sect("The first artifact — a verified ABOM for one high-stakes agent"));
children.push(lead("We start narrow and concrete: instrument one consequential agent with abom-gen so it emits a signed Composition Manifest at deploy time and a hash-chained Action Provenance Record for each consequential action. Then abom-verify checks it against your policy. Success is measurable in weeks, not quarters — one signed, verifiable document that answers the question — and it becomes the reference that unlocks the rest of the institution."));

// Why ABOM
children.push(sect("Why ABOM"));
children.push(bul("Standard — extends the emerging CycloneDX ML-BOM to full agents and runtime provenance; we ride the rail, we don't fork it."));
children.push(bul("Signed — tamper-evident and regulator-grade; trust that is cryptographic, not reputational, and exportable to your SIEM and regulator."));
children.push(bul("Neutral and yours — we sell no model and no agent, so the bill of materials is impartial; it runs inside your boundary and nothing leaves."));

// Call to action band
children.push(new Paragraph({ spacing: { before: 60, after: 0 }, children: [] }));
children.push(new Table({
  width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W], borders: noBorder,
  rows: [new TableRow({ children: [new TableCell({
    width: { size: CONTENT_W, type: WidthType.DXA },
    shading: { fill: BLUE, type: ShadingType.CLEAR },
    margins: { top: 140, bottom: 140, left: 200, right: 200 }, borders: noBorder,
    children: [
      new Paragraph({ spacing: { after: 20 }, children: [t("Request a workshop", { size: 19, bold: true, color: "FFFFFF" })] }),
      new Paragraph({ children: [t("A 60-minute scoping session: we pick one candidate agent, sketch its Composition Manifest, and agree what its first verified ABOM must prove. No commitment beyond the conversation.", { size: 18, color: "EAF0FA" })] }),
    ],
  })] })],
}));

// footer contact
children.push(new Paragraph({
  spacing: { before: 120 },
  border: { top: { style: BorderStyle.SINGLE, size: 4, color: BORDER, space: 6 } },
  children: [t("ABOM · abom.ai · Confidential · Founding design-partner program · contact: hello@abom.ai", { size: 15, color: GREY, italics: true })],
}));

const doc = new Document({
  creator: "ABOM founding team",
  title: "ABOM — Lighthouse Design Partner Brief",
  styles: { default: { document: { run: { font: "Arial", size: 18, color: "262626" } } } },
  numbering: { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "▪", alignment: AlignmentType.LEFT, style: { run: { color: BLUE }, paragraph: { indent: { left: 320, hanging: 200 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, right: 1440, bottom: 900, left: 1440 } } },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("/Users/josephassiga/Desktop/aegis/ABOM_Lighthouse_Onepager.docx", buf);
  console.log("WROTE ABOM_Lighthouse_Onepager.docx", buf.length, "bytes");
});
