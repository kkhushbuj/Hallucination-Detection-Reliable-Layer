import html
import streamlit as st
from graph import build_graph

st.set_page_config(page_title="LLM Trust Score", page_icon="🔍", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

    .stApp {
        background: #0a0a0c;
        color: #f4f4f5;
    }

    .block-container { padding-top: 3rem; padding-bottom: 3rem; max-width: 720px; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* ---------- Hero ---------- */
    .hero { text-align: center; margin-bottom: 2.75rem; }
    .hero-icon-box {
        display: inline-flex; align-items: center; justify-content: center;
        width: 44px; height: 44px; border-radius: 11px; margin-bottom: 1.25rem;
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    .hero-icon { font-size: 1.15rem; line-height: 1; }
    .hero-eyebrow {
        font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
        color: #818cf8; margin-bottom: 0.6rem;
    }
    .hero-title {
        font-size: 2.05rem; font-weight: 700; margin: 0 0 0.75rem 0;
        color: #f9fafb; letter-spacing: -0.02em;
    }
    .hero-sub {
        color: #9ca3af; font-size: 1rem; max-width: 460px;
        margin: 0 auto; line-height: 1.6;
    }

    /* ---------- Cards ---------- */
    .card {
        background: #111113;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.1rem;
    }
    .card-label {
        font-weight: 600; font-size: 0.78rem; letter-spacing: 0.04em; text-transform: uppercase;
        color: #9ca3af; margin-bottom: 0.7rem;
    }
    .answer-text { font-size: 1rem; line-height: 1.65; color: #f4f4f5; white-space: pre-wrap; }

    /* ---------- How It Works ---------- */
    .info-card {
        background: #111113;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.1rem 1.1rem;
        height: 100%;
        transition: border-color 0.15s ease, background 0.15s ease;
    }
    .info-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        background: #141417;
    }
    .info-card-step {
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em;
        color: #818cf8; margin-bottom: 0.5rem;
    }
    .info-card-title { font-weight: 600; font-size: 0.92rem; color: #f4f4f5; margin-bottom: 0.3rem; }
    .info-card-desc { font-size: 0.8rem; color: #9ca3af; line-height: 1.5; }

    .section-heading {
        color: #f4f4f5; font-weight: 600; font-size: 1.1rem;
        margin: 2rem 0 0.9rem 0;
    }

    /* ---------- Score ---------- */
    .score-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; }
    .score-number { font-size: 2.4rem; font-weight: 700; color: #f9fafb; letter-spacing: -0.02em; }

    .badge {
        display: inline-block; padding: 0.28rem 0.75rem; border-radius: 6px;
        font-weight: 600; font-size: 0.78rem; white-space: nowrap;
    }
    .badge-high { background: rgba(34, 197, 94, 0.12); color: #4ade80; }
    .badge-medium { background: rgba(251, 191, 36, 0.12); color: #fbbf24; }
    .badge-low { background: rgba(248, 113, 113, 0.12); color: #f87171; }

    .judge-chip {
        display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.28rem 0.65rem;
        border-radius: 6px; font-size: 0.8rem; font-weight: 500; margin: 0.2rem 0.3rem 0.2rem 0;
    }
    .judge-agree { background: rgba(34, 197, 94, 0.12); color: #4ade80; }
    .judge-disagree { background: rgba(248, 113, 113, 0.12); color: #f87171; }
    .judge-warn { background: rgba(255, 255, 255, 0.06); color: #9ca3af; }

    /* ---------- Button ---------- */
    .stButton>button {
        border-radius: 8px; padding: 0.6rem 0; font-weight: 600; font-size: 0.95rem; width: 100%;
        background: #6366f1;
        color: #ffffff; border: none;
        transition: background 0.15s ease;
    }
    .stButton>button:hover {
        background: #7577f5;
        color: #ffffff;
    }
    .stButton>button:active { background: #5457d6; }

    /* ---------- Text area ---------- */
    .stTextArea textarea {
        background: #111113 !important;
        color: #f4f4f5 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }
    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 1px #6366f1 !important;
    }
    .stTextArea textarea::placeholder { color: #6b7280 !important; }

    /* ---------- Progress bar ---------- */
    .stProgress > div > div > div > div {
        background: #6366f1 !important;
    }
    .stProgress > div > div > div { background: rgba(255, 255, 255, 0.08) !important; }

    /* ---------- Tabs ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #9ca3af;
        padding: 0.5rem 0.1rem;
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: #f4f4f5 !important;
        border-bottom: 2px solid #6366f1 !important;
    }

    /* ---------- Footer ---------- */
    .app-footer {
        text-align: center; color: #6b7280; font-size: 0.78rem;
        margin-top: 3rem; padding-top: 1.25rem;
        border-top: 1px solid rgba(255, 255, 255, 0.07);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-icon-box"><div class="hero-icon">🔍</div></div>
      <div class="hero-eyebrow">Multi-Model Verification</div>
      <div class="hero-title">LLM Trust Score</div>
      <div class="hero-sub">Get an AI answer, then see exactly how much you can trust it — verified by multiple independent models before you ever see the result.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

trust_graph = build_graph()

question = st.text_area(
    "Ask a question",
    placeholder="e.g. What is the capital of Australia?",
    label_visibility="collapsed",
)

how_it_works_col1, how_it_works_col2, how_it_works_col3 = st.columns(3)
with how_it_works_col1:
    st.markdown(
        """
        <div class="info-card">
            <div class="info-card-step">01</div>
            <div class="info-card-title">Generate</div>
            <div class="info-card-desc">The model answers the same question multiple times at different temperatures.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with how_it_works_col2:
    st.markdown(
        """
        <div class="info-card">
            <div class="info-card-step">02</div>
            <div class="info-card-title">Judge</div>
            <div class="info-card-desc">Independent AI judges — separate from the generator — verify each answer on its own.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with how_it_works_col3:
    st.markdown(
        """
        <div class="info-card">
            <div class="info-card-step">03</div>
            <div class="info-card-title">Score</div>
            <div class="info-card-desc">Judge votes and answer consistency combine into one clear Trust Score.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")


def friendly_error(error_text: str) -> str:
    """Turn a raw error message into something a normal person can read."""
    lowered = error_text.lower()
    if "503" in error_text or "unavailable" in lowered or "high demand" in lowered:
        return "Server busy right now"
    elif "429" in error_text or "rate limit" in lowered or "quota" in lowered:
        return "Usage limit reached"
    elif "401" in error_text or "unauthorized" in lowered or "api key" in lowered:
        return "Connection issue"
    else:
        return "Temporarily unavailable"


def safe_html(text: str) -> str:
    """Escape user/model-generated text before dropping it into a raw HTML block."""
    return html.escape(text, quote=False).replace("$", "&#36;")


if st.button("Get Answer & Check Trust", type="primary"):
    if not question.strip():
        st.warning("Please enter a question first.")
    else:
        with st.spinner("Getting answers and running trust checks..."):
            result = trust_graph.invoke({"question": question})

        verification = result["verification_result"]

        score = verification["trust_score"]
        label = verification["label"]
        if score >= 80:
            badge_class = "badge-high"
        elif score >= 50:
            badge_class = "badge-medium"
        else:
            badge_class = "badge-low"

        st.markdown(
            f"""
            <div class="card">
                <div class="card-label">Answer</div>
                <div class="answer-text">{safe_html(verification['winner_answer'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="card">
                <div class="score-row">
                    <div class="card-label" style="margin-bottom:0;">Trust Score</div>
                    <span class="badge {badge_class}">{html.escape(label)}</span>
                </div>
                <div class="score-number">{score}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(min(int(score), 100))
        st.caption(verification["reasoning"].replace("$", "\\$"))

        tie_breaker = verification.get("tie_breaker")
        if tie_breaker:
            if tie_breaker["failed"]:
                st.caption(f"⚠️ Tie-breaker check (Llama 3.3 70B) unavailable: {friendly_error(tie_breaker.get('error', ''))}")
            else:
                verdict = "CORRECT" if tie_breaker["correct"] else "HALLUCINATED"
                st.caption(f"Tie-breaker check (Llama 3.3 70B): {verdict}")
                if verification.get("tie_breaker_disagreed"):
                    st.warning("⚠️ Note: an independent high-capability check disagreed with this result — treat with extra caution.")

        per_answer = verification["per_answer"]

        if not per_answer:
            pass  # nothing to break down when every answer-generation attempt failed
        else:
            st.markdown('<div class="section-heading">Judge Breakdown</div>', unsafe_allow_html=True)
            tabs = st.tabs([f"Answer {i}" for i in range(1, len(per_answer) + 1)])

            for tab, a in zip(tabs, per_answer):
                with tab:
                    st.markdown(
                        f"<div class='answer-text'>{safe_html(a['answer'])}</div>",
                        unsafe_allow_html=True,
                    )
                    st.write("")

                    chips = ""
                    for j in a["judges"]:
                        if j["failed"]:
                            reason = friendly_error(j.get("error", ""))
                            chips += f"<span class='judge-chip judge-warn'>⚠️ {j['provider']}: {reason}</span>"
                        elif j["correct"]:
                            chips += f"<span class='judge-chip judge-agree'>✅ {j['provider']}</span>"
                        else:
                            chips += f"<span class='judge-chip judge-disagree'>❌ {j['provider']}</span>"
                    st.markdown(chips, unsafe_allow_html=True)

                    failed_judges = [j for j in a["judges"] if j["failed"]]
                    if failed_judges:
                        with st.expander("Show raw judge error(s)"):
                            for j in failed_judges:
                                st.code(f"{j['provider']}: {j.get('error', '(no error message)')}")

                    correct_count = sum(1 for j in a["judges"] if j["correct"])
                    total_responding = sum(1 for j in a["judges"] if not j["failed"])

                    if total_responding == 0:
                        st.warning("⚠️ No judges responded")
                    elif correct_count > total_responding / 2:
                        st.success(f"🟢 Stable — {correct_count}/{total_responding} judges agree")
                    else:
                        st.error(f"🔴 Not Stable — only {correct_count}/{total_responding} judges agree")

                    st.caption(
                        f"Score: {round(a['score']*100, 1)}% | Agreed with {round(a['consistency_fraction']*100)}% of other answers"
                    )

        if verification.get("failed_generations"):
            with st.expander("Some answer attempts failed"):
                for f in verification["failed_generations"]:
                    st.caption(f"Temperature {f['temperature']}: {friendly_error(f.get('error', ''))}")

st.markdown(
    '<div class="app-footer">Built with Multi-Model Verification · Powered by LangGraph</div>',
    unsafe_allow_html=True,
)
