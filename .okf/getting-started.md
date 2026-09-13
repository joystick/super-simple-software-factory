---
type: Guide
title: Getting started
description: How to use this bundle and what it covers.
tags: [guide, pocock, sssf]
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
---

# Getting started

This bundle documents the **Matt Pocock "Skills For Real Engineers"
collection** as it relates to this repository (SSSF — a headless multi-agent
ADW pipeline shipped as a Claude Code skill).

Read in this order:

1. [/pocock-skills/catalog.md](/pocock-skills/catalog.md) — what the
   collection is, the two install philosophies, and the two on-disk snapshots
   this bundle compares.
2. [/pocock-skills/skill-matrix.md](/pocock-skills/skill-matrix.md) — the
   full GoF-style comparison table of every skill in both snapshots.
3. [/pocock-skills/naming-drift.md](/pocock-skills/naming-drift.md) — the
   verified rename chains (`write-a-prd → to-prd → to-spec`, etc.) and why
   they matter to SSSF's vendored `skill_engineering/` files.
4. [/pocock-skills/skills/](/pocock-skills/skills/index.md) — deeper entries
   for the skills that are load-bearing for SSSF's bootstrap/AFK mechanism.

The integration analysis that consumes this bundle lives outside it, at
`plans/pocock-protocol-sssf-integration.md` in this repo.
