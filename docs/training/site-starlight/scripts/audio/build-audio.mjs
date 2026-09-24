#!/usr/bin/env node
// Generate narrated audio + a cue-map manifest for each lesson, from the built
// site's HTML, using Piper (neural TTS) inside Docker. Each lesson gets one
// .m4a per voice plus a lecture.json manifest listing both voices' cue maps.
// Re-run after editing lessons.
//
//   node scripts/audio/build-audio.mjs [--only /route/] [--voices amy,ryan]
//
// Prereqs: `npm run build` (produces dist/), Docker running, and the image
// built once:  docker build -t piper-tts:local -f scripts/audio/piper.Dockerfile scripts/audio
import { execFileSync } from 'node:child_process'
import { readFileSync, writeFileSync, mkdirSync, readdirSync, mkdtempSync, rmSync } from 'node:fs'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { parse } from 'node-html-parser'
import { extractSections } from './extract-sections.mjs'
import { buildCueMap } from './cue-map.mjs'

const ROOT = join(import.meta.dirname, '..', '..')
const DIST = join(ROOT, 'dist')
const OUT = join(ROOT, 'public', 'audio')
const IMAGE = 'piper-tts:local'
const SENTENCE_SILENCE = 0.5 // seconds of silence between sentences (Piper native)

// Available voices (models baked into the Docker image). `default` is played first.
const VOICES = [
  { id: 'amy', model: 'en_US-amy-medium', label: 'Amy', gender: 'female' },
  { id: 'ryan', model: 'en_US-ryan-high', label: 'Ryan', gender: 'male' },
]
const DEFAULT_VOICE = 'amy'

function sh(cmd, args) {
  return execFileSync(cmd, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })
}

function ensureImage() {
  try {
    sh('docker', ['image', 'inspect', IMAGE])
  } catch {
    throw new Error(
      `Docker image ${IMAGE} not found. Build it:\n` +
        `  docker build -t ${IMAGE} -f scripts/audio/piper.Dockerfile scripts/audio`,
    )
  }
}

function lessonPages() {
  const pages = []
  const walk = (dir, route) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (e.isDirectory()) walk(join(dir, e.name), `${route}/${e.name}`)
      else if (e.name === 'index.html' && /\/lessons\//.test(`${route}/`))
        pages.push({ html: join(dir, e.name), route: `${route}/`.replace(/^\/+/, '/') })
    }
  }
  walk(DIST, '')
  return pages
}

function sectionsFor(htmlPath) {
  const root = parse(readFileSync(htmlPath, 'utf8'))
  const content = root.querySelector('.sl-markdown-content')
  if (!content) return []
  const h1 = root.querySelector('h1')
  const wrapped = `<main>${h1 ? h1.toString() : ''}${content.innerHTML}</main>`
  return extractSections(wrapped).filter((s) => `${s.title} ${s.text}`.trim().length > 0)
}

function durationOf(file) {
  const out = sh('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file])
  return Math.round(parseFloat(out.trim()) * 1000) / 1000
}

const pad = (n) => String(n).padStart(3, '0')

function build({ only, voices } = {}) {
  ensureImage()
  const selected = VOICES.filter((v) => !voices || voices.includes(v.id))
  console.log(`voices: ${selected.map((v) => v.id).join(', ')}`)
  const pages = lessonPages().filter((p) => !only || p.route === only)
  console.log(`${pages.length} page(s) to narrate`)

  for (const page of pages) {
    const sections = sectionsFor(page.html)
    if (!sections.length) {
      console.log(`  skip ${page.route} (no narratable text)`)
      continue
    }
    const tmp = mkdtempSync(join(tmpdir(), 'sssf-audio-'))
    try {
      // one text file per section (plain text; Piper adds sentence silence itself)
      mkdirSync(join(tmp, 'txt'))
      mkdirSync(join(tmp, 'wav'))
      sections.forEach((s, i) => writeFileSync(join(tmp, 'txt', `${pad(i)}.txt`), `${s.title}. ${s.text}`.trim()))

      const outDir = join(OUT, page.route)
      mkdirSync(outDir, { recursive: true })
      const voiceManifests = []

      for (const voice of selected) {
        // synthesize every section for this voice in one container pass
        const script =
          `set -e; mkdir -p /work/wav/${voice.id}; ` +
          `for f in $(ls /work/txt/*.txt | sort); do i=$(basename "$f" .txt); ` +
          `piper -m /models/${voice.model}.onnx --sentence-silence ${SENTENCE_SILENCE} ` +
          `-f /work/wav/${voice.id}/$i.wav < "$f"; done`
        sh('docker', ['run', '--rm', '-v', `${tmp}:/work`, IMAGE, 'sh', '-c', script])

        const clips = sections.map((_, i) => join(tmp, 'wav', voice.id, `${pad(i)}.wav`))
        const durs = sections.map((s, i) => ({ id: s.id, title: s.title, dur: durationOf(clips[i]) }))
        const listFile = join(tmp, `list-${voice.id}.txt`)
        writeFileSync(listFile, clips.map((c) => `file '${c}'`).join('\n'))
        const m4a = join(outDir, `lecture-${voice.id}.m4a`)
        sh('ffmpeg', ['-y', '-f', 'concat', '-safe', '0', '-i', listFile, '-c:a', 'aac', '-b:a', '96k', m4a])

        voiceManifests.push({
          id: voice.id,
          label: voice.label,
          gender: voice.gender,
          src: `/audio${page.route}lecture-${voice.id}.m4a`,
          duration: durationOf(m4a),
          cues: buildCueMap(durs),
        })
      }

      const manifest = { route: page.route, engine: 'piper', default: DEFAULT_VOICE, voices: voiceManifests }
      writeFileSync(join(outDir, 'lecture.json'), JSON.stringify(manifest, null, 2))
      console.log(
        `  ✓ ${page.route} — ${sections.length} sections × ${selected.length} voice(s) ` +
          `(${voiceManifests.map((v) => `${v.id} ${v.duration}s`).join(', ')})`,
      )
    } finally {
      rmSync(tmp, { recursive: true, force: true })
    }
  }
}

const arg = (name) => {
  const i = process.argv.indexOf(name)
  return i > -1 ? process.argv[i + 1] : undefined
}
build({ only: arg('--only'), voices: arg('--voices')?.split(',') })
