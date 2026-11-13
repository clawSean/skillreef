# Model Manager

![OpenClaw skill](https://img.shields.io/badge/OpenClaw-skill-red)
![Cloud and local](https://img.shields.io/badge/models-cloud%20%2B%20local-blue)

Discover, add, audit, and verify AI models in OpenClaw without silently changing defaults or fallbacks.

## Features

- Compare provider catalogs with configured models and aliases.
- Register picker entries and execution allowlists independently.
- Prove account access with exact-model, no-fallback canaries.
- Verify agent exposure while preserving local-only boundaries.
- Cover OpenAI, Anthropic/custom routers, OpenRouter, NVIDIA, Venice, xAI, Google, and local inference.

## Install

Clone this repository into your OpenClaw workspace's `skills/model-manager` directory, or copy the complete bundle into a configured skills directory. Avoid duplicate installation when Workshop already manages the skill.

## Use

> Use Model Manager to audit newly released models. Report missing routes without changing defaults.

> Add this exact model and prove it works. Keep existing fallbacks unchanged.

The agent follows [SKILL.md](SKILL.md) and the bundled [provider reference](references/provider-and-local-routing.md). Specialist skills are optional; official runtime docs and the provider reference supply the fallback.

## Boundaries

This is an instruction skill, not a plugin or daemon. It requires an existing OpenClaw installation and authorized provider access. It includes no credentials and grants no authority for unrequested upgrades, downloads, or restarts.

## Maintenance

The canonical skill is Workshop-managed. GitHub and SkillReef distributions are generated through one scrubbed publication pipeline, not independently edited.
