# BitGN Platform Reference

## Purpose

This note captures the external assumptions about BitGN that currently shape the project.

## Verified on

- Date checked: 2026-03-24
- Source: <https://bitgn.com/>

## Current understanding

BitGN presents itself as a benchmark and challenge platform for autonomous agents and the teams building them.

Based on the public site as checked above:

- agents connect to a simulated challenge environment through an API
- the platform provides deterministic scoring
- teams receive immediate evaluation feedback
- results are tracked on a global leaderboard
- the benchmark is meant to compare agent approaches under shared constraints

## Why this matters for Columbarium

These assumptions support the core project strategy:

- optimize for measurable benchmark outcomes
- build fast iteration loops
- treat score, failure modes, and reliability as primary engineering feedback

## Caution

This document is not a substitute for official challenge rules or API docs for a specific BitGN round.
When round-specific details matter, record them separately and date them.
