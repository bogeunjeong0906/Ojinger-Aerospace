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
    manager -->|Command to Execute Script| vessle
    vessle -->|Generate params.json| export.ks
    export.ks -->|Create| params.json
    params.json -->|Read| manager

    subgraph vessle [vessle]
        direction TB
        control.ks[control.ks - Real-time Control Script]
        export.ks[export.ks - Export Script: Save Rocket Parameters]
    end

    engine -->|Optimal Path Calculation| manager
```