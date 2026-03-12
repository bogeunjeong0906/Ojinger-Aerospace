# GitHub Copilot Instructions for Rocket Mission Project

This project governs the automated space mission system, including trajectory optimization and real-time rocket control. All interactions with the user must strictly follow these instructions.

---

## 1. Response Language Standards
- **Explanations**: Always provide descriptions and explanations in **Korean** for the user's convenience.
- **Artifacts**: All generated technical content, including **Code, Comments, Architecture Diagrams, and Documentation**, must be written entirely in **English**.
- **Tone**: Maintain a professional and technical tone.

## 2. Architecture Diagram Standards
- **Format**: Use **UML** or **Mermaid (mmd)** for any architecture generation or modification requests.
- **Visualization**: Ensure diagrams are wrapped in `mermaid` code blocks for proper rendering.
- **Consistency**: Reflect the separation between 'Control Tower' (Optimization/UI) and 'Vessel' (Real-time control).

## 3. Domain Knowledge & Tooling (Strict Enforcement)
The `.github/domain_knowledge` directory contains the "Source of Truth" for specialized tools.
- **Target Tools**: 
    - **kOS (Kerbal Operating System)**: `.ks` scripting language.
    - **kRPC**: Python package for KSP interaction.
- **Instruction**: **DO NOT** use your pre-trained internal knowledge for these tools. You must strictly reference the syntax, functions, and tokens provided in the `.github/domain_knowledge` path. Quote and use them "exactly" as defined in the reference files.

## 4. Standard Toolset
The following packages are the established standards for this project. Use them as the primary solution:
- **UI Framework**: `dearpygui`
- **Numerical Analysis & Optimization**: `casadi`
- **Constraint**: If you need to suggest an external package not listed here, you **must ask for the user's permission** and request to add it to the Standard Toolset list first.

## 5. Implementation Strategy
- When providing Python code for optimization, prioritize `casadi` symbolic modeling.
- When creating UI components, use `dearpygui`'s specific item-callback structure.
- All code comments and variable names must be in **English**.

## 6. Python Script Execution Guidelines
- Before running any Python script, ensure that the virtual environment `.venv` (miniconda) is activated by executing the command:
  ```bash
  conda activate ./.venv
  ```
- Alternatively, verify that the `.venv` virtual environment is currently active before proceeding.

## 7. Agent Workflow Prerequisites
The multi-agent system has specific requirements to function effectively on the free model tier. Experiments show the strongest performance and highest potential with the **raptor-mini(preview)** model due to its larger context window.

However, agents will not operate correctly if the **gem-orchestrator** agent attempts to invoke them immediately after the agent files are added. Before the orchestrator can delegate any work, you must:

1. Attach the agent definition files and accompanying instruction documents to the conversation.
2. Explicitly instruct Copilot to **read and internalize** those files so they are loaded into the context window.

If this preload step is skipped or if context is lost and the **gem-orchestrator** (or any subagent it activates) fails to grasp the agent files, instructions, or workflow, **the invoking agent must halt execution**. That agent should then prompt the user to reattach the agent files and request that they be read thoroughly.

This ensures the orchestration layer always has full awareness of the agent specifications and avoids silent misbehavior or misinterpretation.

