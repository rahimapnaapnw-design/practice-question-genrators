"""
Exam Prep Buddy - Matric & Intermediate
Upload a textbook chapter -> practice questions, answer checking, and quizzes.
Explanations in English, Urdu and Roman Urdu.

Run:  streamlit run app.py
Secret: set ANTHROPIC_API_KEY in Streamlit secrets (.streamlit/secrets.toml) or as an env var.
"""

import io
import json
import os

import streamlit as st
from anthropic import Anthropic
from pypdf import PdfReader

MODEL = "claude-sonnet-5-5"
MAX_CHARS = 60000  # chapter text sent to the model

st.set_page_config(page_title="Exam Prep Buddy", page_icon="📚", layout="wide")

# ---------- Styling (Urdu needs RTL + a Nastaliq-friendly font) ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap');
    .urdu { direction: rtl; text-align: right; font-family: 'Noto Nastaliq Urdu', serif;
            line-height: 2.2; font-size: 1.1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Helpers ----------
@st.cache_resource
def get_client():
    key = None
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        pass
    key = key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    return Anthropic(api_key=key)


def ask_llm(system: str, prompt: str, max_tokens: int = 4000) -> str:
    client = get_client()
    if client is None:
        st.error("ANTHROPIC_API_KEY is not set. Add it in Streamlit secrets.")
        st.stop()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def extract_json(text: str):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON found in model reply")
    return json.loads(text[start : end + 1])


def read_chapter(uploaded) -> str:
    name = uploaded.name.lower()
    data = uploaded.read()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if name.endswith(".docx"):
        from docx import Document

        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    return data.decode("utf-8", errors="ignore")


def base_system(level: str, subject: str) -> str:
    return (
        f"You are a patient, expert teacher for Pakistani {level} students"
        f"{' studying ' + subject if subject else ''}. "
        "You ONLY use the chapter text provided by the student as the source of truth. "
        "If something is not in the chapter, say so. Keep language simple and exam-oriented "
        "(board exam style). Urdu must be written in proper Urdu script; Roman Urdu is Urdu "
        "written in Latin letters (e.g. 'Yeh jawab sahi hai kyunke...')."
    )


def show_multilang(en: str, ur: str, ro: str, langs):
    if "English" in langs and en:
        st.markdown("**English**")
        st.write(en)
    if "اردو (Urdu)" in langs and ur:
        st.markdown("**اردو**")
        st.markdown(f"<div class='urdu'>{ur}</div>", unsafe_allow_html=True)
    if "Roman Urdu" in langs and ro:
        st.markdown("**Roman Urdu**")
        st.write(ro)


# ---------- Sidebar: chapter upload ----------
with st.sidebar:
    st.title("📚 Exam Prep Buddy")
    level = st.selectbox("Level", ["Matric (9th/10th)", "Intermediate (FSc/FA, 11th/12th)"])
    subject = st.text_input("Subject (optional)", placeholder="e.g. Physics, Biology, Urdu, English")
    uploaded = st.file_uploader("Upload chapter (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"])
    langs = st.multiselect(
        "Explanation languages",
        ["English", "اردو (Urdu)", "Roman Urdu"],
        default=["English", "اردو (Urdu)", "Roman Urdu"],
    )

    if uploaded and st.button("Load chapter", use_container_width=True):
        text = read_chapter(uploaded).strip()
        if len(text) < 200:
            st.error("Could not read enough text. If it's a scanned PDF, use a text-based PDF.")
        else:
            st.session_state["chapter"] = text[:MAX_CHARS]
            st.session_state["chapter_name"] = uploaded.name
            for k in ("questions", "quiz", "quiz_answers", "quiz_submitted"):
                st.session_state.pop(k, None)
            st.success(f"Loaded {len(text):,} characters.")
            if len(text) > MAX_CHARS:
                st.warning(f"Chapter is long; only the first {MAX_CHARS:,} characters are used.")

    if "chapter" in st.session_state:
        st.caption(f"Current chapter: {st.session_state['chapter_name']}")

st.title("Prepare for your exam from your own textbook")

if "chapter" not in st.session_state:
    st.info("👈 Upload a chapter in the sidebar and click **Load chapter** to begin.")
    st.stop()

chapter = st.session_state["chapter"]
SYSTEM = base_system(level, subject)

tab1, tab2, tab3 = st.tabs(["📝 Practice Questions", "✅ Check My Answer", "🎯 Quiz"])

# ---------- Tab 1: Practice questions ----------
with tab1:
    st.subheader("Generate practice questions")
    c1, c2, c3 = st.columns(3)
    n_mcq = c1.number_input("MCQs", 0, 20, 5)
    n_short = c2.number_input("Short questions", 0, 15, 5)
    n_long = c3.number_input("Long questions", 0, 10, 2)
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")

    if st.button("Generate questions", type="primary"):
        prompt = f"""CHAPTER:
\"\"\"{chapter}\"\"\"

Create exam practice questions from this chapter only, difficulty: {difficulty}.
- {n_mcq} MCQs (4 options each, mark the correct one)
- {n_short} short-answer questions
- {n_long} long-answer questions

Return ONLY JSON:
{{"mcq":[{{"q":"","options":["","","",""],"answer":"A/B/C/D"}}],
 "short":["..."], "long":["..."]}}"""
        with st.spinner("Creating questions..."):
            try:
                st.session_state["questions"] = extract_json(ask_llm(SYSTEM, prompt, 4000))
            except Exception as e:
                st.error(f"Could not generate questions, please try again. ({e})")

    qs = st.session_state.get("questions")
    if qs:
        if qs.get("mcq"):
            st.markdown("### MCQs")
            for i, m in enumerate(qs["mcq"], 1):
                st.markdown(f"**Q{i}. {m['q']}**")
                for lbl, opt in zip("ABCD", m["options"]):
                    st.write(f"{lbl}) {opt}")
                with st.expander("Show answer"):
                    st.write(f"Correct: **{m['answer']}**")
        if qs.get("short"):
            st.markdown("### Short questions")
            for i, q in enumerate(qs["short"], 1):
                st.markdown(f"**{i}.** {q}")
        if qs.get("long"):
            st.markdown("### Long questions")
            for i, q in enumerate(qs["long"], 1):
                st.markdown(f"**{i}.** {q}")
        st.caption("Copy a question into the 'Check My Answer' tab to get feedback.")

# ---------- Tab 2: Check answer ----------
with tab2:
    st.subheader("Check your answer against the chapter")
    question = st.text_area("Question", height=80)
    answer = st.text_area("Your answer", height=160)

    if st.button("Check answer", type="primary"):
        if not question.strip() or not answer.strip():
            st.warning("Please enter both the question and your answer.")
        else:
            prompt = f"""CHAPTER:
\"\"\"{chapter}\"\"\"

QUESTION: {question}
STUDENT ANSWER: {answer}

Check the student's answer strictly against the chapter. Return ONLY JSON:
{{"score": <0-10 integer>,
 "verdict": "Correct" | "Partially correct" | "Incorrect",
 "correct_answer_en": "model answer based on the chapter",
 "feedback_en": "what was right, what was missing/wrong, how to improve",
 "correct_answer_ur": "same in Urdu script",
 "feedback_ur": "same in Urdu script",
 "correct_answer_ro": "same in Roman Urdu",
 "feedback_ro": "same in Roman Urdu"}}"""
            with st.spinner("Checking..."):
                try:
                    r = extract_json(ask_llm(SYSTEM, prompt, 3000))
                    st.metric("Score", f"{r['score']}/10", r["verdict"])
                    st.markdown("#### Feedback")
                    show_multilang(r.get("feedback_en", ""), r.get("feedback_ur", ""),
                                   r.get("feedback_ro", ""), langs)
                    st.markdown("#### Model answer")
                    show_multilang(r.get("correct_answer_en", ""), r.get("correct_answer_ur", ""),
                                   r.get("correct_answer_ro", ""), langs)
                except Exception as e:
                    st.error(f"Could not check the answer, please try again. ({e})")

# ---------- Tab 3: Quiz ----------
with tab3:
    st.subheader("Practice quiz")
    n = st.slider("Number of questions", 3, 20, 10)

    if st.button("Start new quiz", type="primary"):
        prompt = f"""CHAPTER:
\"\"\"{chapter}\"\"\"

Create a {n}-question MCQ quiz from this chapter only, in board-exam style.
Return ONLY JSON:
{{"questions":[{{"q":"","options":["","","",""],"correct":0,
 "explanation_en":"why it is correct, based on the chapter",
 "explanation_ur":"same in Urdu script",
 "explanation_ro":"same in Roman Urdu"}}]}}
"correct" is the 0-based index of the right option."""
        with st.spinner("Building quiz..."):
            try:
                st.session_state["quiz"] = extract_json(ask_llm(SYSTEM, prompt, 6000))["questions"]
                st.session_state["quiz_submitted"] = False
                st.session_state["quiz_answers"] = {}
            except Exception as e:
                st.error(f"Could not build the quiz, please try again. ({e})")

    quiz = st.session_state.get("quiz")
    if quiz:
        submitted = st.session_state.get("quiz_submitted", False)
        for i, q in enumerate(quiz):
            st.markdown(f"**Q{i + 1}. {q['q']}**")
            choice = st.radio(
                "Choose one",
                options=list(range(len(q["options"]))),
                format_func=lambda j, q=q: f"{'ABCD'[j]}) {q['options'][j]}",
                index=None,
                key=f"quiz_q_{i}",
                disabled=submitted,
                label_visibility="collapsed",
            )
            st.session_state["quiz_answers"][i] = choice

            if submitted:
                if choice == q["correct"]:
                    st.success("Correct ✅")
                else:
                    st.error(f"Wrong ❌ — correct answer: {'ABCD'[q['correct']]}) {q['options'][q['correct']]}")
                with st.expander("Explanation"):
                    show_multilang(q.get("explanation_en", ""), q.get("explanation_ur", ""),
                                   q.get("explanation_ro", ""), langs)
            st.divider()

        if not submitted:
            if st.button("Submit quiz"):
                st.session_state["quiz_submitted"] = True
                st.rerun()
        else:
            score = sum(
                1 for i, q in enumerate(quiz)
                if st.session_state["quiz_answers"].get(i) == q["correct"]
            )
            st.metric("Your score", f"{score}/{len(quiz)}", f"{round(100 * score / len(quiz))}%")
