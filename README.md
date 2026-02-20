# Guided Component Architect - Pythrust Assignment

## Overview
This project implements an **Agentic Code-Generation Workflow** that transforms natural language descriptions into valid, styled Angular components while adhering to a predefined Design System.

## Architecture: The Agentic Loop
The system follows a `Generate -> Validate -> Self-Correct` feedback loop:

1.  **The Generator (`generator.py`)**: Uses prompt engineering to inject `design-system.json` tokens into the LLM context. It instructs the LLM to output a structured JSON containing HTML, CSS, and TypeScript.
2.  **The Validator (`validator.py`)**: A "Linter-Agent" that inspects the generated code for:
    *   **Syntax Validity**: Matching brackets and valid JSON structure.
    *   **Design Compliance**: Ensuring mandatory tokens (like `primary-color`) are present in the code.
3.  **Self-Correction Loop (`main.py`)**: If the validator detects errors, the system automatically re-prompts the LLM with the specific error logs. The LLM then "fixes" the component based on this feedback.

## Frontend Checklist (Complete)
- [x] Implement LLM Fallback (OS -> OpenAI)
    - [x] Update `generator.py` with fallback logic
    - [x] Update `requirements.txt` and `.env`
- [x] Implement Interactive UI (Streamlit)
    - [x] Create `app.py`
    - [x] Refactor `main.py` for status yielding
- [x] Documentation and Finalization

## How to Run
1.  **Install Dependencies**:
    ```bash
    pip install openai groq python-dotenv streamlit
    ```
2.  **Set Up API Keys**: Create a `.env` file and add your keys.
3.  **Run the Interactive UI**:
    ```bash
    streamlit run app.py
    ```
4.  **Run via Terminal (Original)**:
    ```bash
    python main.py
    ```

## Multi-Provider Fallback Logic
The system is designed for high availability and cost-efficiency:
1.  **Primary**: Calls an Open Source model (Llama 3 via Groq).
2.  **Secondary (Fallback)**: If Groq fails or the key is missing, it automatically falls back to OpenAI (GPT-4o).
3.  **Failsafe**: If both providers are unavailable, a local mock generator provides a sample response to keep the agentic loop running for demonstration.

## Prompt Injection Prevention & Scaling
### Prompt Injection Prevention
To prevent malicious prompts from hijacking the generator:
*   **Strict System Prompts**: We define the LLM's role and output format strictly.
*   **Input Sanitization**: User descriptions can be sanitized to remove common injection keywords (e.g., "ignore all previous instructions").
*   **Separation of Concerns**: The LLM has no access to system commands or sensitive files. Its output is treated as data (JSON), not executable script on the host.

### Scaling to Full-Page Applications
To scale this to full-page apps:
1.  **Hierarchical Generation**: Break the page into sub-components. Generate layout first, then fill in components.
2.  **State Management**: Use a "Global State Definition" token in the design system to sync data across components.
3.  **AST-Based Merging**: Instead of raw strings, use an AST parser to merge generated components into a main page structure safely.
4.  **Persistent Feedback**: Maintain the context of previously generated components so the LLM knows how new parts relate to old ones.

---
*Developed for Gen AI Engineer Intern Evaluation - Pythrust Technologies*
