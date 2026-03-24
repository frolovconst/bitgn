# First Legitimate Score Runbook

## Goal

Get one valid end-to-end benchmark run scored by the BitGN server.

## Minimum scoring path

1. Configure a model provider through config (`local` or `api`).
2. Execute a single benchmark run command.
3. Submit to the server and confirm receipt of a legitimate score.
4. Save run artifacts for reproducibility.

## Required run artifacts

For each scored run, capture:

- timestamp (UTC)
- commit SHA
- model provider (`local` or `api`)
- model name
- relevant runtime config
- server score response
- log path or output file path

## Recommended first-run strategy

- start with the most reliable currently available provider setup
- prioritize successful server scoring over optimization
- once first score is obtained, iterate in small controlled changes

## Notes

This runbook is intentionally focused on the nearest milestone for a time-constrained contest workflow.
