---
name: mermaid
description: Create workflow diagrams, flowcharts, sequence diagrams, state diagrams, Gantt charts, and process visualizations using Mermaid.js. Use when you need to visually demonstrate processes, information flow, system architecture, state transitions, or any diagram showing relationships and progression. Renders to PNG/SVG via mermaid-cli (mmdc).
---

# Mermaid Diagram Generation

Generate professional diagrams as code using Mermaid.js syntax, then render to images.

## When to Use

- Workflow diagrams showing process flow
- Information transfer/progression diagrams
- System architecture visualizations
- State machines and transitions
- Sequence diagrams (API calls, interactions)
- Gantt charts for project timelines
- Entity relationship diagrams

## Quick Start

1. Write Mermaid syntax to a `.mmd` file
2. Render with `mmdc` CLI
3. Output is ready to share

## Rendering Command

```bash
mmdc -i input.mmd -o output.png -b transparent -p ~/.openclaw/workspace/skills/mermaid/references/puppeteer-config.json
```

**Required flags:**
- `-p` with puppeteer config (fixes `--no-sandbox` for root execution)
- `-b transparent` for clean backgrounds

## Diagram Types

### Flowchart (most common)

```mermaid
flowchart TD
    Start([Beginning]) --> Process[Do Something]
    Process --> Decision{Check?}
    Decision -->|Yes| Action1[Path A]
    Decision -->|No| Action2[Path B]
    Action1 --> End([Done])
    Action2 --> End
```

**Layout directions:**
- `TD` / `TB` = Top to bottom
- `LR` = Left to right
- `RL` = Right to left
- `BT` = Bottom to top

**Node shapes:**
- `[Rectangle]` = Standard process
- `([Rounded])` = Start/End/Terminator
- `{Diamond}` = Decision
- `[[Subroutine]]` = Subprocess
- `[(Database)]` = Data store
- `((Circle))` = Connector

**Styling:**
```mermaid
style NodeId fill:#e1f5ff,stroke:#333
```

### Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant API
    participant DB
    
    User->>API: Request data
    API->>DB: Query
    DB-->>API: Results
    API-->>User: Response
```

### State Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing: Start
    Processing --> Complete: Success
    Processing --> Error: Failure
    Error --> Idle: Retry
    Complete --> [*]
```

### Gantt Chart

```mermaid
gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    
    section Phase 1
    Task 1: 2024-01-01, 7d
    Task 2: 2024-01-08, 5d
    
    section Phase 2
    Task 3: 2024-01-13, 10d
```

## Helper Script

Use `scripts/render_mermaid.sh` for simplified rendering:

```bash
./scripts/render_mermaid.sh input.mmd output.png
```

The script handles paths and config automatically.

## Examples

See `references/examples.md` for complete diagram examples across all types.

## Best Practices

**Clarity over complexity:**
- Keep diagrams focused on one concept
- Use 5-15 nodes (not 50)
- Color code for meaning, not decoration

**Consistent naming:**
- Use descriptive node IDs (not `A`, `B`, `C`)
- Match business/technical terminology

**Progressive disclosure:**
- High-level diagram first
- Link to detailed sub-diagrams if needed
- Don't cram everything into one graphic

## Common Patterns

**Decision tree with colors:**
```mermaid
flowchart TD
    Start([Input]) --> Parse
    Parse --> Valid{Valid?}
    Valid -->|Yes| Process
    Valid -->|No| Error[Reject]
    
    style Start fill:#e1f5ff
    style Process fill:#d4edda
    style Error fill:#f8d7da
```

**Multi-path convergence:**
```mermaid
flowchart LR
    A[Source 1] --> Merge[Combine]
    B[Source 2] --> Merge
    C[Source 3] --> Merge
    Merge --> Output[Result]
```

**Parallel processing:**
```mermaid
flowchart TD
    Start --> Split{Fork}
    Split --> Path1[Process A]
    Split --> Path2[Process B]
    Split --> Path3[Process C]
    Path1 --> Join[Merge]
    Path2 --> Join
    Path3 --> Join
    Join --> End([Done])
```

## Troubleshooting

**Rendering fails:**
- Check for syntax errors in `.mmd` file
- Ensure puppeteer config path is correct
- Run `mmdc --version` to verify installation

**Diagrams too large:**
- Use `LR` layout instead of `TD` for wide diagrams
- Split into multiple focused diagrams
- Adjust canvas size with `%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#fff'}}}%%` in mmd file

## Output Storage

Store diagrams in organized locations:
- `~/.openclaw/workspace/diagrams/YYYY-MM-DD/` for dated work
- Project-specific folders for documentation

Keep `.mmd` source files alongside `.png` output for future editing.
