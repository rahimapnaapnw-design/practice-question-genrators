# 📚 Imtihan Saathi (امتحان ساتھی)

**Your exam companion for Matric and Intermediate.**

Imtihan Saathi helps students in Pakistan prepare for board exams using their *own* textbook. Upload a chapter and the app creates practice questions, checks your answers against the chapter, and runs quizzes. Every explanation is available in **English, Urdu (اردو) and Roman Urdu**.

## Features

| Feature | What it does |
|---|---|
| 📝 **Practice Questions** | Generates MCQs, short questions and long questions from your chapter, at Easy, Medium or Hard difficulty |
| ✅ **Check My Answer** | Scores your answer out of 10 against the chapter, shows what was missing, and gives a model answer |
| 🎯 **Quiz Mode** | Builds a 3 to 20 question MCQ quiz, scores it, and explains every answer |
| 🌐 **Three languages** | English, Urdu script and Roman Urdu, selectable from the sidebar |
| 📂 **Your own textbook** | Accepts PDF, DOCX and TXT chapters |

All questions and feedback are based only on the chapter you upload.

## Tech stack

- [Streamlit](https://streamlit.io) for the web interface
- [Anthropic Claude API](https://docs.claude.com) for question generation and answer checking
- `pypdf` and `python-docx` for reading chapters

## Run locally

```bash
git clone https://github.com/<your-username>/imtihan-saathi.git
cd imtihan-saathi
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:

```toml
ANTHROPIC_API_KEY = "your-api-key-here"
```

Then start the app:

```bash
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select your repo, with `app.py` as the main file.
4. Open **Settings → Secrets** and add:
   ```toml
   ANTHROPIC_API_KEY = "your-api-key-here"
   ```
5. Deploy.

> ⚠️ Never commit your API key. Add `.streamlit/secrets.toml` to `.gitignore`.

## How to use

1. Choose your level (Matric or Intermediate) and optionally enter the subject.
2. Upload a chapter and click **Load chapter**.
3. Choose your explanation languages.
4. Use the three tabs: Practice Questions, Check My Answer, and Quiz.

## Limitations

- Scanned (image-only) PDFs are not supported. Use text-based PDFs.
- Only the first 60,000 characters of a chapter are used (`MAX_CHARS` in `app.py`).
- AI-generated questions and feedback can contain mistakes. Always confirm important points with your textbook and teacher.
- Each action uses the Claude API, which has a cost.

## Project structure

```
├── app.py            # Streamlit app
├── requirements.txt  # Python dependencies
└── README.md
```

## Roadmap

- Save quiz scores and track progress
- OCR for scanned textbooks
- Past-paper style question formats per board
- Download questions as PDF
- Voice reading of Urdu explanations

## License

MIT. Free to use and adapt for education.
