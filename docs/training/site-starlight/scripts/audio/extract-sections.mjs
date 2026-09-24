import { parse } from 'node-html-parser'

// Turn a rendered lesson's HTML into ordered narration sections, one per
// "On this page" entry (an h2/h3 with an id), plus a leading "intro" for
// anything before the first such heading. Pure: HTML in, data out.
//
//   extractSections(html) -> [{ id, title, text }]
//
// Rules: read paragraphs, list items, and callout label+body; keep inline
// <code> text; drop block <pre> code, quizzes, and animated diagram figures;
// replace tables with a short spoken note rather than reading raw cells.

const HEADINGS = new Set(['h2', 'h3'])

function collapse(s) {
  return (s || '').replace(/\s+/g, ' ').trim()
}

function isSkippable(el) {
  const tag = el.rawTagName?.toLowerCase()
  if (tag === 'pre' || tag === 'script' || tag === 'style' || tag === 'svg') return true
  const cls = el.getAttribute?.('class') || ''
  const testid = el.getAttribute?.('data-testid') || ''
  // Code blocks: Starlight's Expressive Code wraps them in
  // <figure class="expressive-code">…<pre>…, so the bare <pre> check above is
  // not enough. Skip anything whose class marks a code block, or that contains
  // a <pre> at all — never narrate rendered code markup.
  if (/\bexpressive-code\b/.test(cls) || tag === 'figure') return true
  if (el.querySelector?.('pre')) return true
  if (/\bquiz\b/.test(cls) || testid === 'quiz') return true
  if (/\bdiagram\b/.test(cls) || testid.endsWith('-diagram') || testid === 'sdlc-cycle') return true
  if (testid === 'audio-lecture') return true
  return false
}

function narrate(el) {
  const tag = el.rawTagName?.toLowerCase()
  if (!tag || isSkippable(el)) return ''
  if (tag === 'table') return 'This section includes a table; see it on the page.'
  const cls = el.getAttribute?.('class') || ''
  if (/\bcallout\b/.test(cls)) {
    const label = collapse(el.querySelector('.callout-label')?.text || '')
    const body = collapse(el.querySelector('.callout-body')?.text || el.text)
    return collapse(`${label}. ${body}`)
  }
  // paragraphs, lists, blockquotes, plain text — inline <code> text is kept
  return collapse(el.text)
}

const LEAF = new Set(['p', 'ul', 'ol', 'blockquote', 'table', 'pre', 'figure', 'dl'])

// Is this element a self-contained block we narrate (or skip) as a unit,
// rather than a wrapper to descend into? Starlight nests headings and content
// inside wrapper <div>s, so we must recurse through plain containers but stop
// at callouts / quizzes / diagrams / tables / code.
function isLeaf(el, tag) {
  if (LEAF.has(tag)) return true
  const cls = el.getAttribute?.('class') || ''
  const testid = el.getAttribute?.('data-testid') || ''
  return (
    /\b(callout|quiz|diagram)\b/.test(cls) ||
    testid === 'quiz' ||
    testid === 'audio-lecture' ||
    testid.endsWith('-diagram') ||
    testid === 'sdlc-cycle'
  )
}

// Yield headings (with ids) and leaf blocks in document order, descending
// through wrapper containers.
function* blocks(el) {
  for (const node of el.childNodes) {
    const tag = node.rawTagName?.toLowerCase()
    if (!tag) continue
    if (tag === 'h1' || HEADINGS.has(tag)) {
      yield node
      continue
    }
    if (isLeaf(node, tag)) {
      yield node
      continue
    }
    yield* blocks(node)
  }
}

// The intro's id must match Starlight's page-title anchor ("Overview" in the
// TOC links to #_top), so the intro cue syncs and is seekable.
const INTRO_ID = '_top'

export function extractSections(html) {
  const root = parse(html || '')
  const main = root.querySelector('main') || root
  const sections = []
  let current = { id: INTRO_ID, title: 'Introduction', parts: [] }

  // Keep a heading's section even when its only content was skipped (a diagram-
  // or quiz-only section still gets a cue, so its "On this page" entry syncs);
  // drop only an empty intro.
  const flush = () => {
    if (current.id !== INTRO_ID || current.parts.length) sections.push(current)
  }

  for (const node of blocks(main)) {
    const tag = node.rawTagName.toLowerCase()
    if (tag === 'h1') {
      if (current.id === INTRO_ID) current.title = collapse(node.text) || current.title
      continue
    }
    if (HEADINGS.has(tag) && node.getAttribute('id')) {
      flush()
      current = { id: node.getAttribute('id'), title: collapse(node.text), parts: [] }
      continue
    }
    const spoken = narrate(node)
    if (spoken) current.parts.push(spoken)
  }
  flush()

  return sections.map(({ id, title, parts }) => ({ id, title, text: parts.join(' ') }))
}
