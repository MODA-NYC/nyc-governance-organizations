# NYCGO Edit-Publish Pipeline

> **Interactive BPMN Viewer**: [View full diagram with zoom/pan controls](https://moda-nyc.github.io/nyc-governance-organizations/docs/nycgo-edit-publish-pipeline-standalone.html)
>
> **Source files**: [BPMN XML](./nycgo-edit-publish-pipeline.bpmn) (importable to Camunda, Bizagi, etc.)

```mermaid
flowchart TB
    subgraph AdminUI["NYCGO Admin UI"]
        direction LR
        A1([User Opens Admin UI]) --> A2[Load Golden Dataset from GitHub]
        A2 --> A3[Search/Select Organization]
        A3 --> A4[Fill Edit Form]
        A4 --> A5{Schedule for later?}
        A5 -->|Yes| A6[Set Scheduled Date/Time]
        A6 --> A7[Commit to scheduled-edits/]
        A5 -->|No| A8[Commit CSV to pending-edits/]
        A7 --> A9([Edit Submitted])
        A8 --> A9
    end

    subgraph ProcessEdit["Process Edit Workflow"]
        direction LR
        B1([Edit CSV Pushed / Scheduled Trigger]) --> B2[Check and Promote Scheduled Edits]
        B2 --> B3{Has pending edits?}
        B3 -->|No| B4([No Edits to Process])
        B3 -->|Yes| B5[Determine Mode]
        B5 --> B6[Checkout Pipeline Repo]
        B6 --> B7[Find Latest Golden Dataset]
        B7 --> B8[Combine Pending Edits into QA File]
        B8 --> B9[[Run Pipeline]]
        B9 --> B10[Commit Audit Artifacts to Target Branch]
        B10 --> B11{Trigger Publish?}
        B11 -->|Test Only| B14[Archive Processed Edits]
        B11 -->|Demo or Production| B12[Determine Version Bump]
        B12 --> B13[Trigger publish-release Workflow]
        B13 --> B14
        B14 --> B15([Edit Processing Complete])
    end

    subgraph PublishRelease["Publish Release Workflow"]
        direction LR
        C1([Publish Workflow Triggered]) --> C2[Determine Mode]
        C2 --> C3[Find Run ID from Audit Runs]
        C3 --> C4[Calculate Next Version]
        C4 --> C5[Run publish_run.py]
        C5 --> C6[Create _latest.csv Copies]
        C6 --> C7[[Validate Release Assets]]
        C7 --> C8[Generate Socrata-Compatible JSON]
        C8 --> C9{Production Mode?}
        C9 -->|Yes| C10[Commit Published Files to Main]
        C10 --> C11[Prepare Release Notes]
        C9 -->|No| C11
        C11 --> C12[Create GitHub Release]
        C12 --> C13{Triggered by User?}
        C13 -->|Yes| C14[Notify User of Completion]
        C14 --> C15([Release Published])
        C13 -->|No| C15
    end

    subgraph PipelineSubprocess["Run Pipeline (run_pipeline.py)"]
        direction LR
        P1([Start]) --> P2[Load Golden + QA Inputs]
        P2 --> P3[Apply QA Edits to Dataset]
        P3 --> P4[Apply Directory Rules]
        P4 --> P5[Generate Outputs]
        P5 --> P6[Write run_summary.json]
        P6 --> P7([Complete])
    end

    subgraph ValidationSubprocess["Validate Release Assets"]
        direction LR
        V1([Start]) --> V2[Validate Golden Dataset Schema]
        V2 --> V3[Validate Published Dataset Schema]
        V3 --> V4([Complete])
        V2 -.->|Validation Failed| V5([Release Blocked])
    end

    %% Cross-pool message flows
    A8 -.->|CSV to pending-edits/| B1
    B13 -.->|workflow_dispatch| C1

    %% Styling
    classDef pool fill:#f5f5f5,stroke:#1a365d,stroke-width:2px
    classDef subprocess fill:#fff3cd,stroke:#856404
    classDef startEnd fill:#d4edda,stroke:#155724
    classDef decision fill:#cce5ff,stroke:#004085

    class AdminUI,ProcessEdit,PublishRelease pool
    class PipelineSubprocess,ValidationSubprocess subprocess
```

## Pipeline Subprocess Detail

```mermaid
flowchart LR
    P1([Start Pipeline]) --> P2[Load Golden + QA Inputs]
    P2 --> P3[Apply QA Edits to Dataset]
    P3 --> P4[Apply Directory Rules]
    P4 --> P5[Generate golden_pre-release.csv<br/>and published_pre-release.csv]
    P5 --> P6[Write run_summary.json]
    P6 --> P7([Pipeline Complete])
```

## Validation Subprocess Detail

```mermaid
flowchart LR
    V1([Start Validation]) --> V2[Validate Golden Dataset Schema]
    V2 --> V3[Validate Published Dataset Schema]
    V3 --> V4([Validation Complete])
    V2 -.->|Error| V5([Release Blocked])
    V3 -.->|Error| V5
```

## Legend

| Symbol | Meaning |
|--------|---------|
| `([text])` | Start/End event |
| `[text]` | Task |
| `{text}` | Gateway (decision) |
| `[[text]]` | Subprocess (collapsed) |
| `-.->` | Message flow (cross-pool) |
| `-->` | Sequence flow |
