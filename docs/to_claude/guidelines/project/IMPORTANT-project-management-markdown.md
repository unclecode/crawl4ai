<!-- ---
!-- Timestamp: 2025-05-30 17:10:32
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/project/IMPORTANT-project-management-markdown.md
!-- --- -->

Project management is conducted under `./project_management` directory.

## Core Files and Locations
- Original plan: `./project_management/USER_PLAN.md` (DO NOT EDIT)
- Updated plans: `./project_management/CLAUDE_PLAN.md` (Use this as a persistent memory)
- Progress tracking (Markdown): `./project_management/progress-<title>-<timestamp>.md`
- Progress tracking (Mermaid) : `./project_management/progress-<title>-<timestamp>.mmd`
- Memory across sessions: `./project_management/next_steps-<timestamp>.md`

## Progress Format

``` markdown
# Title
| Type | Stat | Description   |
|------|------|---------------|
| 🚀   | [x]  | Project Title |

## Goals, Milestones, and Tasks
#### 🎯 Goal 1: Description
| Type | Stat | Description        |
|------|------|--------------------|
| 🎯   | [ ]  | Goal description   |
|      |      | 📌 Justication     |
|------|------|--------------------|
| 🏁   | [ ]  | Milestone details  |
|      | [J]  | Justication        |
|------|------|--------------------|
| 📋   | [x]  | Completed task     |
|      | [J]  | 📌 `/path/to/file` |

## Key Symbols
| Symbol | Meaning       | Status | Meaning |
|--------|---------------|--------|---------|
| 🎯     | Goal          | [ ]    | TODO    |
| 🏁     | Milestone     | [x]    | DONE    |
| 📋     | Task          |        |         |
| 💡     | Suggestion    |        |         |
| 📌     | Justification |        |         |
```

## Visual Progress Management using Mermaid Diagram
- `./project_management/progress-<title>-<timestamp>.mmd`
  - Mermaid diagram definition file reflecting `./project_management/progress-<title>-<timestamp>.md`
  - Use tags as well
  - Use TD layout
  - Understand the hierarchy and summarize into core elements
  - Summarize up to most-important 7 elements

- `./project_management/progress-<title>-<timestamp>.svg`
  - SVG file created from the mermaid file

- `./project_management/progress-<title>-<timestamp>.gif`
  - GIF image created from the SVG file

#### Rendering Tool
Use `.claude/bin/render_mermaid.sh /path/to/mermaid/file.mmd`

#### Example
``` mermaid
graph TD
    subgraph Legend
        Z1[Todo]:::todo
        Z2[In Progress]:::inProgress
        Z3[Done]:::done
        Z4[Directory]:::directory
    end
    subgraph Project Structure
    subgraph PD[Project Description]
        PJNAME[Project Name]:::done
        PJGOALS[Goals]:::done
    end
    subgraph PDIR[Project Directory]
        Root["\/workspace\/projects\/000-sample-project"]:::directory
        Config[config/]:::directory
        Data[data/]:::directory
        Scripts[scripts/]:::directory
        Results[results/]:::directory
        Resources[resources/]:::directory
        Env[.env/]:::directory
        Git[.git/]:::directory
        Requirements[requirements.txt/]:::directory
        Log[Log.txt/]:::directory
        PM[project_management.mmd]:::directory
    end
    end
    subgraph Execution Flow
    subgraph Step
        D[Compile Context]:::done
        E[Generate Elisp]:::inProgress
        F[Execute Elisp]:::todo
        G{Success?}:::todo
    end
    subgraph "Logging, Version Control, and State Update"
        H[Log Success]:::todo
        I[Log Error]:::todo
        J{Milestone?}:::todo
        K[Git Commit]:::todo
        L[Log Only]:::todo
        M{Goal Met?}:::todo
        N[Update Project_States]:::todo
    end
    end
    subgraph PMFLOW[Project Management Flow]
        MS1[Milestone 1]:::done
        MS2[Milestone 2]:::inProgress
    subgraph Tasks M1
        T1[task1]:::done
        T2[task2]:::done
    end
    subgraph Tasks M2
        T3[task1]:::done
        T4[task2]:::todo
    end
    end
    Start[Start]:::starttag --> PD
    PD --> PDIR
    PM --> PMFLOW
    PMFLOW --> PM
    PDIR --> D
    D --> E --> F --> G
    G -- Yes --> H
    G -- No --> I
    H --> J
    J -- Yes --> K
    J -- No --> L
    K --> M
    I --> L
    L --> M
    M -- No --> N
    N --> Root
    M -- Yes --> End[End]:::endtag
    PJGOALS --> PMFLOW
    MS1 --> T1
    MS1 --> T2
    MS2 --> T3
    MS2 --> T4
    classDef starttag fill:#cce5ff,stroke:#333,stroke-width:2px;
    classDef done fill:#9f9,stroke:#333,stroke-width:2px;
    classDef inProgress fill:#ff9,stroke:#333,stroke-width:2px;
    classDef todo fill:#fff,stroke:#333,stroke-width:2px;
    classDef directory fill:#efe,stroke:#333,stroke-width:1px;
    classDef endtag fill:#fcc,stroke:#333,stroke-width:2px;
    class Root,Config,Data,Scripts,Results,Resources directory;
```

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->