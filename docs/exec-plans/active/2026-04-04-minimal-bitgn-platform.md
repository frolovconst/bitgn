# Minimal BitGN Platform

## Goal

Build the minimum platform layer needed to interact with the BitGN API and support full-task execution.

## Scope

In scope:

- minimum benchmark API integration
- task fetch and result submission flow
- thin support layer for end-to-end runs

Out of scope:

- sophisticated agent behavior
- production hardening beyond what is needed for first end-to-end runs

## Steps

1. Define the minimum repository interface for benchmark interaction.
2. Implement the API plumbing needed to fetch tasks and submit results.
3. Make the platform usable as the base for a full benchmark-facing agent.

## Status

Not started

## Notes

- Keep the platform thin and easy to replace.
- Prefer the smallest correct interface that unblocks the first agent.
