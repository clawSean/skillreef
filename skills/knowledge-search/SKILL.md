---
name: knowledge-search
description: Knowledge base backed by ChromaDB vector search. Use when you need to look up topics, procedures, research, or other markdown/text content in a configurable knowledge directory, especially when exact keyword search is not enough. Files are indexed recursively and searched semantically via Ollama embeddings. Separate from OpenClaw's built-in memory_search, which covers MEMORY.md and memory/ files.
---

# Knowledge Base Search

Semantic search over a configurable knowledge directory using ChromaDB + Ollama local embeddings.

## Quick Start

**Ingest the knowledge directory into ChromaDB:**
```bash
bash ~/.openclaw/workspace/skills/knowledge-search/scripts/ingest.sh
```

**Query the knowledge base:**
```bash
bash ~/.openclaw/workspace/skills/knowledge-search/scripts/query.sh "how does the Telegram API work"
```

## What Lives Where

This mapping is system-specific to this workspace.

- `knowledge/topics/` — facts, concepts, entities, and reference material
- `knowledge/procedures/` — how-tos, workflows, and operational steps
- `knowledge/research/` — deeper investigations, comparisons, and findings
- `knowledge/notes/` — staging or lighter-weight knowledge notes
- `memory/` and `MEMORY.md` — personal and episodic memory, not this skill's scope

Use this skill for the knowledge base. Use `memory_search` / memory files for memory.

## Content Scope

- Indexes all `.md` and `.txt` files under the configured source directory and all child folders
- Default source directory is `workspace/knowledge/`
- You can point it at a differently named knowledge folder or any other document tree by setting `SOURCE_DIR=/path/to/folder`
- Re-running ingest is safe

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SOURCE_DIR` | `~/.openclaw/workspace/knowledge` if present, otherwise `skill/data` | Root directory to index recursively |
| `CHROMA_PERSIST_DIR` | `~/.openclaw/chroma/knowledge-search` | Where ChromaDB stores its data |
| `CHROMA_COLLECTION` | `knowledge` | Collection name |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Ollama model used for embeddings |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server base URL |
| `CHUNK_SIZE` | `1500` | Max characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `FORCE_REINGEST` | `0` | Set to `1` to bypass manifest caching and reprocess all files |

## Commands

### Ingest documents

```bash
bash ~/.openclaw/workspace/skills/knowledge-search/scripts/ingest.sh
```

Override the source path when needed:

```bash
SOURCE_DIR=/path/to/knowledge-folder bash ~/.openclaw/workspace/skills/knowledge-search/scripts/ingest.sh
```

The ingest runner:
- walks the source directory recursively
- chunks files at paragraph boundaries with overlap
- skips unchanged files using a manifest cache
- removes orphaned chunks when files were deleted
- upserts safely into the configured Chroma collection

### Query

```bash
bash ~/.openclaw/workspace/skills/knowledge-search/scripts/query.sh "your question here" [n_results]
```

Returns JSON with title, source, distance, and excerpt.

## OpenClaw-Compatible Re-Ingest Guidance

Prefer an OpenClaw cron job over system crontab when you want the agent to own recurring maintenance.

Recommended pattern:
- schedule an isolated recurring agent turn
- have it run `bash ~/.openclaw/workspace/skills/knowledge-search/scripts/ingest.sh`
- capture and report the final summary line when useful
- keep delivery off unless you actually want notifications

Example agent-turn payload concept:

```text
Run bash ~/.openclaw/workspace/skills/knowledge-search/scripts/ingest.sh for the knowledge base and report the final summary line.
```

Use system crontab only when you explicitly want a host-level job independent of OpenClaw.

## Resources

### data/

Optional fallback source material when `workspace/knowledge/` is absent. This is mainly for standalone or packaged use.

### scripts/

**`ingest.sh`**
- resolves the source directory
- applies environment defaults
- calls `ingest_runner.py`

**`ingest_runner.py`**
- performs recursive file discovery
- chunks content and embeds it with Ollama
- caches file state for incremental re-ingest
- removes orphaned chunks from deleted files

**`query.sh`**
- performs semantic search against the index
- returns a friendly JSON error if the collection does not exist yet
