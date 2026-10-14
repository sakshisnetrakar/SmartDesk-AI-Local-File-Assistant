# SmartDesk AI – Local File Assistant

A local Windows desktop app built with Python, Tkinter, PyPDF, and Ollama. Document content is sent only to the locally running Ollama server on your computer; no cloud API key is needed.

## Setup

1. Install Ollama for Windows.
2. In a terminal, download and start the local model:

```cmd
ollama pull llama3.2
ollama serve
```

3. In a second terminal, run the app:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python smartdesk_ai.py
```

## How to use

1. Click **Select document** and choose a TXT or PDF file.
2. Ask a question, or click **Summarize document**.
3. Select **Save conversation** to save the local chat as a text file.

The application performs Ollama calls in a background thread so the Tkinter window remains responsive. It displays a helpful message when Ollama is not running.

## Scope

This is a local learning prototype, not a production document-management system. For very large files, it sends only the first 24,000 characters to the model.
