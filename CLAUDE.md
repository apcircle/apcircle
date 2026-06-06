# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current State

This repository is essentially empty. It contains a single file, `Readme.txt`
(placeholder text: "This is my new rep"), and one commit. There is no source
code, build system, test suite, dependency manifest, or CI configuration yet.

As a result, there are no project-specific build, lint, test, or run commands to
document. The sections below should be filled in as the project takes shape.

## When Adding Code to This Repository

Because no conventions exist yet, the first substantive changes will set them.
When scaffolding the project, update this file with:

- **Stack & entry point** — language, framework, and where execution begins.
- **Commands** — how to install dependencies, build, lint, run, and test
  (including how to run a single test), once a toolchain is chosen.
- **Architecture** — the big-picture structure once there are multiple modules
  whose relationships aren't obvious from reading a single file.

## Git Conventions

- The default branch is `master`.
- Development for AI-assisted work happens on dedicated `claude/*` branches;
  push with `git push -u origin <branch-name>` and do not push to `master`
  without explicit permission.
