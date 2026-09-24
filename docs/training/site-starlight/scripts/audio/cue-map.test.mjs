import { test } from 'node:test'
import assert from 'node:assert/strict'
import { buildCueMap } from './cue-map.mjs'

test('cumulative starts from per-section durations', () => {
  const cues = buildCueMap([
    { id: 'intro', title: 'Introduction', dur: 12.5 },
    { id: 'a', title: 'A', dur: 30 },
    { id: 'b', title: 'B', dur: 7.25 },
  ])
  assert.deepEqual(cues, [
    { id: 'intro', title: 'Introduction', start: 0, dur: 12.5 },
    { id: 'a', title: 'A', start: 12.5, dur: 30 },
    { id: 'b', title: 'B', start: 42.5, dur: 7.25 },
  ])
})

test('empty input yields empty map', () => {
  assert.deepEqual(buildCueMap([]), [])
})

test('single section starts at zero', () => {
  assert.deepEqual(buildCueMap([{ id: 'only', title: 'Only', dur: 9 }]), [
    { id: 'only', title: 'Only', start: 0, dur: 9 },
  ])
})
