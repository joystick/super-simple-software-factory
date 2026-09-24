// Turn per-section durations into a cue map with cumulative start times.
//   buildCueMap([{id, title, dur}]) -> [{id, title, start, dur}]
// Pure. `start` is the seconds offset of each section within the concatenated
// per-lesson audio file; the player uses it to sync the "On this page" panel.
export function buildCueMap(sections) {
  let start = 0
  return sections.map(({ id, title, dur }) => {
    const cue = { id, title, start, dur }
    start += dur
    return cue
  })
}
