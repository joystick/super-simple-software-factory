---
title: "Can WanGP generate training videos on a 2019 16-inch MacBook Pro?"
version: 1.0
updated: 2026-08-25
status: active
verdict: "No — three independent blockers, each verified on the machine."
---

# WanGP on a MacBookPro16,1 — research findings

**Question.** Can [WanGP](https://wangp.ai/) (Wan2GP) be used locally to create the SSSF
training videos on an Intel i9 / 32 GB / Radeon Pro 5500M 8 GB machine?

**Answer: no.** Three blockers, any one of which is fatal. All were verified on the
machine rather than inferred from documentation.

---

## The machine

```
MacBookPro16,1 · macOS 15.7.4
Intel Core i9-9980HK · 32 GB RAM
AMD Radeon Pro 5500M · 8 GB VRAM (Navi 14, RDNA 1)
```

## Blocker 1 — the GPU is the wrong AMD generation

WanGP's [AMD guide](https://github.com/deepbeepmeep/Wan2GP/blob/main/docs/AMD-INSTALLATION.md)
is titled *"AMD Installation Guide for **Windows** (TheRock)"* and supports:

| Family | Architecture | Examples |
|---|---|---|
| `gfx103X-dgpu` | RDNA 2 | RX 6000 series |
| `gfx110X-all` | RDNA 3 | RX 7900 XTX, 7800 XT, 780M |
| `gfx1150/1151` | RDNA 3.5 APU | Radeon 890M, Strix Halo |
| `gfx120X-all` | RDNA 4 | RX 9070 XT, 9060 |

The Radeon Pro 5500M is **RDNA 1**. It appears in none of these families. The site's own
FAQ says AMD support covers "RDNA 2, RDNA 3, RDNA 3.5 and RDNA 4".

## Blocker 2 — that AMD path is Windows-only anyway

AMD acceleration goes through **TheRock's ROCm PyTorch wheels, on Windows 10/11**. There is
no ROCm for macOS, and Apple removed the AMD-on-macOS compute story years ago. Even a
supported GPU would not help on this OS.

## Blocker 3 — PyTorch itself has left this platform behind

This is the deepest one, and it rules out most local generative AI, not just WanGP.

```
platform tag              macosx-15.0-x86_64
newest torch for x86 Mac  2.2.2      (also: 2.1.2, 2.2.0, 2.2.1)
current torch release     2.13.0
WanGP requires            2.7.1 (GTX 10xx) or 2.10 (RTX 30–50xx)
```

PyTorch stopped publishing macOS x86_64 wheels after **2.2.2**. The versions WanGP asks for
have never existed for this architecture and never will. Torch 2.2.2 also predates Python
3.12, so it needs a Python 3.11 environment on top.

## The surprise: the GPU *is* reachable — and it does not matter

I expected `torch.backends.mps` to be unavailable on an Intel Mac. **It is available, and
it computes correctly.** Measured with torch 2.2.2 on Python 3.11:

```
2048×2048 matmul ×20    GPU (mps) 0.60s    CPU 0.61s    speedup 1.0×
effective throughput    ~571 GFLOP/s fp32
correctness             True
```

So the Radeon Pro 5500M works — and delivers **no speedup over the CPU** on dense matmul,
which is the operation video diffusion is made of. For scale, the RTX-class hardware WanGP
targets is two orders of magnitude faster on the tensor paths these models use, and has
dedicated fp16/fp8 acceleration this GPU lacks entirely.

Even if every software blocker vanished, a Wan 2.2-class model at ~571 GFLOP/s fp32 would
take hours per few seconds of footage.

---

## What to do instead

### If you want AI-generated video: rent a GPU

WanGP is built for this and runs unmodified on a rented Linux box with an NVIDIA card.
Cloud GPU hosts (RunPod, Vast.ai, Lambda) rent 4090/A100-class hardware by the hour.

> **Not verified:** I did not check current pricing. Confirm before budgeting — rates move,
> and per-second billing versus per-hour changes the maths for short jobs.

Workflow: rent → install WanGP per the Linux guide → generate → download → shut it down.
Nothing about your local machine changes.

### For *these* training videos: generative video is the wrong tool

Worth saying plainly, because it is the more useful finding.

The SSSF series teaches a terminal workflow. What it needs on screen is **a real terminal
running real commands** — not synthesised footage. A generative model cannot show
`just sdlc` producing a real diff, and if it "showed" one it would be fabricating output,
which is precisely what the series spends ten episodes warning against.

Everything needed is already on this machine, and free:

| Need | Tool | Notes |
|---|---|---|
| Screen recording | **Cmd-Shift-5** (built in) | records screen + mic, no install |
| Terminal recording | **asciinema** (installed) | tiny, text-based, perfectly crisp |
| Cast → video/GIF | `agg`, or play a cast and screen-record it | `brew install agg` |
| Narration | your voice, or macOS `say` | `say -v Daniel -o out.aiff -f script.txt` |
| Editing | iMovie (free) / DaVinci Resolve (free) | both fine on this hardware |
| Slides | the lesson HTML already written | screen-share and scroll |

The eight casts in `training/casts/` were recorded from real commands and are ready to
narrate. `training/*.md` carries the scripts, with `[CAST: ...]` markers naming the extra
recordings still needed.

**This machine is entirely capable of producing the series.** It is just not capable of
generating video with a diffusion model, and the series does not want that.

---

## Method

Every claim above was checked on the machine:

- hardware via `system_profiler` / `sysctl`
- WanGP support matrix from the project's own AMD and installation docs
- available torch wheels queried live from the PyPI JSON API
- MPS availability and throughput measured in a throwaway Python 3.11 venv

The one thing I did not verify is cloud GPU pricing, flagged inline.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-25 | Initial research. Verdict: not viable locally; three verified blockers; screen recording recommended instead. |
