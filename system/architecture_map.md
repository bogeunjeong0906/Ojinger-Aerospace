# System Architecture Map

<!-- Note: To avoid rendering errors in Mermaid diagrams, avoid using parentheses in node labels. Use alternative delimiters like colons or dashes instead. -->

<!-- Philosophy: The architecture is based on a file/path structure. Every structural entity is represented as a file or a directory. -->

```mermaid
graph TD
    subgraph control_tower/ [control_tower/]
        direction TB
        ui[ui.py - Handles User Input] --> manager[manager.py - Hub]
        manager --> engine[engine.py - Optimization Engine]
    end

    User[User] -->|Input| ui
    manager -->|Command to Execute Script| vessel
    vessel -->|Generate params.json| export.ks
    export.ks -->|Create| params.json
    params.json -->|Read| manager

    subgraph vessel [vessel]
        direction TB
        control.ks[control.ks - Real-time Control Script]
        export.ks[export.ks - Export Script: Save Rocket Parameters]
    end

    engine -->|Optimal Path Calculation| manager
```

### export.ks 상세 아키텍처
아래 다이어그램은 `export.ks` 스크립트 내부 흐름을 나타냅니다.

```mermaid
graph TD
    subgraph export_ks [export.ks]
        direction TB
        shipAPI["SHIP & VESSEL APIs"] --> collect[Collect telemetry]
        collect --> build[Build JSON object]
        build --> fileWrite[Write JSON to file]
    end

    collect -->|iterate parts/engines| parts["PARTS/ENGINES lists"]
    build -->|use LEXICON/LIST| structures["kOS data structures"]
    fileWrite -->|WRITEJSON| filesystem["kOS filesystem (vessel/export.json)"]
```
