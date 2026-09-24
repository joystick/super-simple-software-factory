# SSSF fork recipes. Small on purpose -- everything here operates on
# docs/training/site-starlight/, an Astro Starlight site (the training
# course). Mirrors its own docs/training/justfile's recipes one-for-one,
# under a `training-` prefix so they're runnable from anywhere in this repo,
# not just from inside docs/training/.

# list every recipe
default:
    @just --list

# --- training (docs/training/site-starlight/, an Astro Starlight site) ---

# install site deps (run once)
training-install:
    cd docs/training/site-starlight && npm install

# serve the course locally with hot reload (http://localhost:4321)
training-serve PORT="4321":
    cd docs/training/site-starlight && npm run dev -- --port {{PORT}}

# alias for the everyday loop
training-dev PORT="4321": (training-serve PORT)

# production build into docs/training/site-starlight/dist
training-build:
    cd docs/training/site-starlight && npm run build

# preview the production build
training-preview:
    cd docs/training/site-starlight && npm run preview

# run the audio-module unit tests
training-test:
    cd docs/training/site-starlight && node --test scripts/audio/extract-sections.test.mjs scripts/audio/cue-map.test.mjs

# build the Piper TTS docker image once (bakes in the amy + ryan voices)
training-audio-image:
    cd docs/training/site-starlight && docker build -t piper-tts:local -f scripts/audio/piper.Dockerfile scripts/audio

# (re)generate narrated-lecture audio for all lessons -- Piper neural TTS via Docker.
# needs `just training-audio-image` (once). Depends on training-build so dist/
# always exists before build-audio.mjs reads it. Renders every lesson in both
# voices (amy, ryan). Limit with a route, e.g.
#   just training-audio /01-sssf-fundamentals/lessons/0001-a-gate-you-have-not-watched-fail/
# or one voice: `node scripts/audio/build-audio.mjs --voices amy`
training-audio ROUTE="": training-build
    cd docs/training/site-starlight && node scripts/audio/build-audio.mjs {{ if ROUTE != "" { "--only " + ROUTE } else { "" } }}

# verify docs/reference/'s concept-manifest links resolve and every real
# markdown link in docs/reference/ actually points somewhere real
docs-check:
    python3 scripts/docs-check/check_reference_manifest.py --root docs --fork-root .
    python3 scripts/docs-check/check_markdown_links.py --root docs --fork-root .
