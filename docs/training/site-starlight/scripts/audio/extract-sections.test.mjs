import { test } from 'node:test'
import assert from 'node:assert/strict'
import { extractSections } from './extract-sections.mjs'

// A stand-in for a rendered Starlight lesson's <main>: an intro before the
// first heading, two h2 sections with ids, a callout, a code block, a table,
// and a quiz that must be skipped.
const HTML = `
<main>
  <h1 id="_top">Lesson Title</h1>
  <p>Intro paragraph before any section.</p>
  <div class="callout callout-win"><span class="callout-label">The win</span>
    <div class="callout-body"><p>You will learn the thing.</p></div></div>

  <h2 id="what-a-gate-is">What a gate is</h2>
  <p>A gate is a <code>deterministic</code> check.</p>
  <ul><li>Code runs it.</li><li>It judges the result.</li></ul>
  <pre><code>echo "PLACEHOLDER"   exit 0</code></pre>

  <h2 id="the-problem">The problem</h2>
  <p>Two states, identical from the outside.</p>
  <table><tr><th>Probe</th><th>pytest</th></tr><tr><td>x</td><td>PASS</td></tr></table>
  <div class="quiz" data-testid="quiz"><p class="quiz-question">Ignore me?</p>
    <button data-testid="quiz-choice">nope</button></div>
</main>`

test('returns one section per heading with id, in order', () => {
  const secs = extractSections(HTML)
  // the intro carries the page-title anchor id (_top), matching the TOC's "Overview"
  assert.deepEqual(secs.map((s) => s.id), ['_top', 'what-a-gate-is', 'the-problem'])
  assert.deepEqual(
    secs.map((s) => s.title),
    ['Lesson Title', 'What a gate is', 'The problem'],
  )
})

test('intro captures pre-heading prose and the win callout', () => {
  const [intro] = extractSections(HTML)
  assert.match(intro.text, /Intro paragraph before any section/)
  assert.match(intro.text, /The win/)
  assert.match(intro.text, /You will learn the thing/)
})

test('code blocks are stripped but inline code text is kept', () => {
  const secs = extractSections(HTML)
  const gate = secs.find((s) => s.id === 'what-a-gate-is')
  assert.match(gate.text, /deterministic check/) // inline <code> kept
  assert.doesNotMatch(gate.text, /PLACEHOLDER/) // <pre> dropped
  assert.match(gate.text, /Code runs it/) // list items kept
})

test('tables become a short spoken note, not raw cells', () => {
  const secs = extractSections(HTML)
  const problem = secs.find((s) => s.id === 'the-problem')
  assert.match(problem.text, /table/i)
  assert.doesNotMatch(problem.text, /PASS/) // cell contents not read verbatim
})

test('quizzes are skipped entirely', () => {
  const secs = extractSections(HTML)
  const problem = secs.find((s) => s.id === 'the-problem')
  assert.doesNotMatch(problem.text, /Ignore me/)
})

test('Expressive Code blocks are never read as literal markup', () => {
  // Starlight renders code fences into <figure class="expressive-code">…<pre>…,
  // whose rendered DOM must never leak into narration.
  const ec = `<main>
    <h2 id="build-it">Build it</h2>
    <p>Run the command below.</p>
    <figure class="expressive-code"><figcaption>bash</figcaption>
      <pre data-language="bash"><code><div class="ec-line"><div class="code">
        <span style="--0:#d6deeb">deno</span> <span>test</span></div></div></code></pre>
    </figure>
    <p>Then read the output.</p>
  </main>`
  const [sec] = extractSections(ec)
  assert.match(sec.text, /Run the command below/)
  assert.match(sec.text, /Then read the output/)
  assert.doesNotMatch(sec.text, /ec-line|<div|<span|class=|style=|--0/)
})

test('empty / heading-less input yields no sections', () => {
  assert.deepEqual(extractSections('<main></main>'), [])
  assert.deepEqual(extractSections(''), [])
})
