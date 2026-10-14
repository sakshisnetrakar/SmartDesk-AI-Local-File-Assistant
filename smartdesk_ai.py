"""SmartDesk AI: a local Tkinter document assistant powered by Ollama."""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, X, Button, Label, Text, Tk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import requests
from pypdf import PdfReader

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"
MAX_CONTEXT_CHARS = 24_000


class SmartDeskApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("SmartDesk AI – Local File Assistant")
        self.root.geometry("900x680")
        self.document_text = ""
        self.document_name = "No document selected"
        self.conversation: list[tuple[str, str]] = []

        Label(root, text="SmartDesk AI – Local File Assistant", font=("Segoe UI", 16, "bold")).pack(pady=(12, 3))
        self.status = Label(root, text="Select a TXT or PDF file to begin.", anchor="w")
        self.status.pack(fill=X, padx=14, pady=(0, 8))

        buttons = root
        Button(buttons, text="Select document", command=self.select_document).pack(side=LEFT, padx=(14, 6))
        self.summarize_button = Button(buttons, text="Summarize document", command=self.summarize, state="disabled")
        self.summarize_button.pack(side=LEFT, padx=6)
        Button(buttons, text="Save conversation", command=self.save_conversation).pack(side=RIGHT, padx=(6, 14))
        Button(buttons, text="Clear chat", command=self.clear_chat).pack(side=RIGHT, padx=6)

        Label(root, text="Conversation").pack(anchor="w", padx=14, pady=(12, 2))
        self.chat = ScrolledText(root, wrap="word", height=22, state="disabled", font=("Segoe UI", 10))
        self.chat.pack(fill=BOTH, expand=True, padx=14)

        Label(root, text="Ask a question about the selected document").pack(anchor="w", padx=14, pady=(10, 2))
        self.question = Text(root, height=3, wrap="word", font=("Segoe UI", 10))
        self.question.pack(fill=X, padx=14)
        self.ask_button = Button(root, text="Ask SmartDesk AI", command=self.ask_question, state="disabled")
        self.ask_button.pack(pady=10)

    def select_document(self) -> None:
        file_path = filedialog.askopenfilename(title="Select a document", filetypes=[("Supported documents", "*.txt *.pdf"), ("Text files", "*.txt"), ("PDF files", "*.pdf")])
        if not file_path:
            return
        try:
            path = Path(file_path)
            if path.suffix.lower() == ".txt":
                text = path.read_text(encoding="utf-8", errors="replace")
            elif path.suffix.lower() == ".pdf":
                reader = PdfReader(path)
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            else:
                raise ValueError("Choose a TXT or PDF document.")
            if not text.strip():
                raise ValueError("No readable text was found in this document.")
            self.document_text, self.document_name = text, path.name
            self.status.config(text=f"Selected: {path.name} ({len(text):,} characters)")
            self.ask_button.config(state="normal")
            self.summarize_button.config(state="normal")
            self.append_chat("System", f"Loaded {path.name}. Ask a question or select Summarize document.")
        except Exception as error:
            messagebox.showerror("Cannot read document", str(error))

    def ask_question(self) -> None:
        question = self.question.get("1.0", END).strip()
        if not question:
            messagebox.showinfo("Question needed", "Type a question first.")
            return
        self.question.delete("1.0", END)
        self.append_chat("You", question)
        self.run_generation(f"Answer the question using only the document text. If the answer is not present, say so.\n\nQuestion: {question}")

    def summarize(self) -> None:
        self.append_chat("You", "Please summarize this document.")
        self.run_generation("Give a concise bullet-point summary of the document. Include only information supported by the document text.")

    def run_generation(self, instruction: str) -> None:
        self.ask_button.config(state="disabled")
        self.summarize_button.config(state="disabled")
        self.status.config(text="Ollama is generating a local response...")
        context = self.document_text[:MAX_CONTEXT_CHARS]
        prompt = f"You are SmartDesk AI, a local document assistant.\n\nDOCUMENT ({self.document_name}):\n{context}\n\n{instruction}"
        threading.Thread(target=self._generate_worker, args=(prompt,), daemon=True).start()

    def _generate_worker(self, prompt: str) -> None:
        try:
            response = requests.post(OLLAMA_URL, json={"model": MODEL, "prompt": prompt, "stream": False}, timeout=180)
            response.raise_for_status()
            answer = response.json().get("response", "No response was returned by Ollama.").strip()
            self.root.after(0, lambda: self.finish_generation(answer))
        except requests.ConnectionError:
            self.root.after(0, lambda: self.finish_generation("Ollama is not running. Start it with 'ollama serve' and make sure the llama3.2 model is installed using 'ollama pull llama3.2'."))
        except Exception as error:
            self.root.after(0, lambda: self.finish_generation(f"Unable to generate a response: {error}"))

    def finish_generation(self, answer: str) -> None:
        self.append_chat("SmartDesk AI", answer)
        self.status.config(text=f"Ready — {self.document_name}")
        self.ask_button.config(state="normal")
        self.summarize_button.config(state="normal")

    def append_chat(self, speaker: str, text: str) -> None:
        self.conversation.append((speaker, text))
        self.chat.config(state="normal")
        self.chat.insert(END, f"{speaker}:\n{text}\n\n")
        self.chat.config(state="disabled")
        self.chat.see(END)

    def clear_chat(self) -> None:
        self.conversation.clear()
        self.chat.config(state="normal")
        self.chat.delete("1.0", END)
        self.chat.config(state="disabled")

    def save_conversation(self) -> None:
        if not self.conversation:
            messagebox.showinfo("Nothing to save", "Start a conversation first.")
            return
        target = filedialog.asksaveasfilename(title="Save conversation", defaultextension=".txt", initialfile="smartdesk_conversation.txt", filetypes=[("Text files", "*.txt")])
        if target:
            content = f"SmartDesk AI conversation\nDocument: {self.document_name}\n\n" + "\n\n".join(f"{speaker}:\n{text}" for speaker, text in self.conversation)
            Path(target).write_text(content, encoding="utf-8")
            self.status.config(text=f"Conversation saved to {Path(target).name}")


if __name__ == "__main__":
    window = Tk()
    SmartDeskApp(window)
    window.mainloop()
