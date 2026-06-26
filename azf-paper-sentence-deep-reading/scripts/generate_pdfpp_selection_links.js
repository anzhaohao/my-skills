#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { createRequire } = require("module");

function parseArgs(argv) {
  const args = { sentence: [] };
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (!arg.startsWith("--")) {
      throw new Error(`Unexpected argument: ${arg}`);
    }
    const key = arg.slice(2);
    if (key === "sentence") {
      args.sentence.push(argv[++i]);
    } else {
      args[key] = argv[++i];
    }
  }
  return args;
}

function usage() {
  return [
    "Usage:",
    "  node generate_pdfpp_selection_links.js --pdf paper.pdf --page 1 --sentence \"Sentence.\" [--sentence \"Next.\"] [--sentences file.txt] [--pdfjs-root .codex-tmp/pdfjs-probe] [--link-target Paper.pdf] [--display \"Paper, p.1\"]",
    "",
    "Install compatible PDF.js if needed:",
    "  npm install pdfjs-dist@3.11.174 --prefix .codex-tmp/pdfjs-probe",
  ].join("\n");
}

function loadPdfjs(pdfjsRoot) {
  const roots = [];
  if (pdfjsRoot) roots.push(path.resolve(pdfjsRoot));
  roots.push(process.cwd());
  roots.push(__dirname);

  const errors = [];
  for (const root of roots) {
    const originalWarn = console.warn;
    const originalLog = console.log;
    try {
      if (!process.env.PDFPP_LINKS_DEBUG) {
        console.warn = () => {};
        console.log = (...parts) => {
          const text = parts.join(" ");
          if (text.startsWith("Warning: Cannot polyfill")) return;
          originalLog(...parts);
        };
      }
      const req = createRequire(path.join(root, "probe.js"));
      return req("pdfjs-dist/legacy/build/pdf.js");
    } catch (error) {
      errors.push(`${root}: ${error.message}`);
    } finally {
      console.warn = originalWarn;
      console.log = originalLog;
    }
  }

  throw new Error(
    "Could not load pdfjs-dist/legacy/build/pdf.js.\n" +
      "Install with: npm install pdfjs-dist@3.11.174 --prefix .codex-tmp/pdfjs-probe\n" +
      "Then pass: --pdfjs-root .codex-tmp/pdfjs-probe\n\n" +
      errors.join("\n")
  );
}

function readSentences(args) {
  const sentences = [];
  if (args.sentences) {
    const raw = fs.readFileSync(args.sentences, "utf8").trim();
    if (raw.startsWith("[")) {
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) throw new Error("--sentences JSON must be an array");
      sentences.push(...parsed);
    } else {
      sentences.push(...raw.split(/\r?\n/).map((line) => line.trim()).filter(Boolean));
    }
  }
  sentences.push(...args.sentence);
  if (!sentences.length) throw new Error("Provide at least one --sentence or --sentences file.");
  return sentences;
}

function expandLigature(ch) {
  return {
    "\uFB00": "ff",
    "\uFB01": "fi",
    "\uFB02": "fl",
    "\uFB03": "ffi",
    "\uFB04": "ffl",
    "\uFB05": "ft",
    "\uFB06": "st",
  }[ch] || ch;
}

function normalizeTarget(text) {
  return Array.from(text)
    .flatMap((ch) => Array.from(expandLigature(ch)))
    .map((ch) => (ch === "'" || ch === "\u2018" ? "\u2019" : ch))
    .join("")
    .replace(/\s+/g, " ")
    .trim();
}

function buildCharEntries(items) {
  const entries = [];
  for (const item of items) {
    for (let off = 0; off < item.str.length; off++) {
      const expanded = expandLigature(item.str[off]);
      for (const ch of expanded) {
        entries.push({ ch, ref: { idx: item.idx, off } });
      }
    }
    entries.push({ ch: "\n", ref: { idx: item.idx, off: item.str.length, sep: true } });
  }
  return entries;
}

function nextNonSpace(entries, start) {
  for (let i = start; i < entries.length; i++) {
    if (!/\s/.test(entries[i].ch)) return entries[i].ch;
  }
  return "";
}

function buildReadableNormalizedText(text) {
  return Array.from(text)
    .flatMap((ch) => Array.from(expandLigature(ch)))
    .map((ch) => (ch === "'" || ch === "\u2018" ? "\u2019" : ch))
    .join("")
    .replace(/-\s+([a-z])/g, "$1")
    .replace(/([a-z])\s+(fi|fl)\s*([a-z])/g, "$1$2$3")
    .replace(/\s+\u2019\s*/g, "\u2019")
    .replace(/\s+/g, " ")
    .trim();
}

function buildCompactStream(items) {
  const entries = buildCharEntries(items);
  const chars = [];
  const refs = [];

  function push(ch, ref) {
    chars.push(ch);
    refs.push(ref);
  }

  for (let i = 0; i < entries.length; i++) {
    let { ch, ref } = entries[i];
    if (ch === "'" || ch === "\u2018") ch = "\u2019";

    const next = nextNonSpace(entries, i + 1);

    if (ch === "-" && /\s/.test(entries[i + 1]?.ch || "") && /[a-z]/.test(next)) {
      continue;
    }

    if (/\s/.test(ch)) {
      continue;
    }

    push(ch, ref);
  }

  return { text: chars.join(""), refs };
}

function compactTarget(text) {
  return Array.from(text)
    .flatMap((ch) => Array.from(expandLigature(ch)))
    .map((ch) => (ch === "'" || ch === "\u2018" ? "\u2019" : ch))
    .join("")
    .replace(/\s+/g, "");
}

function selectedText(items, selection) {
  const [startIdx, startOffset, endIdx, endOffset] = selection;
  if (startIdx === endIdx) {
    return items[startIdx].str.slice(startOffset, endOffset).replace(/\s+/g, " ").trim();
  }
  const pieces = [items[startIdx].str.slice(startOffset)];
  for (let idx = startIdx + 1; idx < endIdx; idx++) pieces.push(items[idx].str);
  pieces.push(items[endIdx].str.slice(0, endOffset));
  return pieces.join("\n").replace(/\s+/g, " ").trim();
}

function selectedCompactText(items, selection) {
  const [startIdx, startOffset, endIdx, endOffset] = selection;
  const clipped = items.map((item) => ({ ...item }));
  clipped[startIdx] = { ...clipped[startIdx], str: clipped[startIdx].str.slice(startOffset) };
  clipped[endIdx] = { ...clipped[endIdx], str: clipped[endIdx].str.slice(0, endOffset) };
  return buildCompactStream(clipped.slice(startIdx, endIdx + 1)).text;
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.pdf || !args.page) {
    console.error(usage());
    process.exit(1);
  }

  const pdfjs = loadPdfjs(args["pdfjs-root"]);
  const sentences = readSentences(args);
  const pageNumber = Number(args.page);
  if (!Number.isInteger(pageNumber) || pageNumber < 1) throw new Error("--page must be a 1-based positive integer.");

  const data = new Uint8Array(fs.readFileSync(args.pdf));
  const doc = await pdfjs.getDocument({
    data,
    disableWorker: true,
    verbosity: pdfjs.VerbosityLevel?.ERRORS,
  }).promise;
  const page = await doc.getPage(pageNumber);
  const textContent = await page.getTextContent({ includeMarkedContent: false });
  const items = textContent.items.map((item, idx) => ({ idx, str: item.str, hasEOL: Boolean(item.hasEOL) }));
  const stream = buildCompactStream(items);

  let searchStart = 0;
  const rows = [];
  for (let i = 0; i < sentences.length; i++) {
    const target = compactTarget(sentences[i]);
    const pos = stream.text.indexOf(target, searchStart);
    if (pos === -1) {
      rows.push({
        sentence: i + 1,
        ok: false,
        error: "Sentence not found in normalized PDF.js text stream.",
        sentenceText: sentences[i],
      });
      continue;
    }

    const startRef = stream.refs[pos];
    const endRef = stream.refs[pos + target.length - 1];
    const selection = [startRef.idx, startRef.off, endRef.idx, endRef.off + 1];
    const selected = selectedText(items, selection);
    const linkTarget = args["link-target"] || path.basename(args.pdf);
    const display = args.display || `${path.basename(args.pdf, path.extname(args.pdf))}, p.${pageNumber}`;
    const link = `[[${linkTarget}#page=${pageNumber}&selection=${selection.join(",")}|${display}]]`;
    const selectedNormalized = buildReadableNormalizedText(selected);
    const selectedCompact = selectedCompactText(items, selection);

    rows.push({
      sentence: i + 1,
      ok: true,
      matches: selectedCompact === target,
      selection,
      link,
      sentenceText: sentences[i],
      selectedText: selected,
      selectedNormalizedText: selectedNormalized,
      selectedCompactText: selectedCompact,
    });

    searchStart = pos + target.length;
  }

  const result = {
    pdfjsVersion: pdfjs.version,
    pdf: args.pdf,
    page: pageNumber,
    itemsCount: items.length,
    rows,
  };

  const output = JSON.stringify(result, null, 2);
  if (args.out) fs.writeFileSync(args.out, output, "utf8");
  else console.log(output);

  if (rows.some((row) => !row.ok || !row.matches)) process.exitCode = 2;
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
