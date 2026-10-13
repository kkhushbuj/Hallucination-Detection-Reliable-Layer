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
        background: #0d0a14;
        color: #f3f1f8;
    }

    .block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 760px; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* ---------- Hero ---------- */
    .hero { text-align: center; margin-bottom: 3rem; }
    .hero-icon-box {
        display: inline-flex; align-items: center; justify-content: center;
        width: 76px; height: 76px; border-radius: 22px; margin-bottom: 1.1rem;
        background: linear-gradient(135deg, #8b5cf6, #ec4899);
        box-shadow: 0 0 50px rgba(168, 85, 247, 0.55), 0 0 0 1px rgba(255,255,255,0.05) inset;
    }
    .hero-icon { font-size: 2.1rem; line-height: 1; }
    .hero-title {
        font-size: 2.3rem; font-weight: 800; margin: 0.2rem 0 0.6rem 0;
        background: linear-gradient(90deg, #8b5cf6, #a855f7, #ec4899);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-sub {
        color: #a1a1b5; font-size: 1.03rem; max-width: 520px;
        margin: 0 auto; line-height: 1.6;
    }

    /* ---------- Cards ---------- */
    .card {
        background: #161220;
        border: 1px solid rgba(168, 85, 247, 0.25);
        border-radius: 16px;
        padding: 1.5rem 1.75rem;
        box-shadow: 0 0 24px rgba(139, 92, 246, 0.08);
        margin-bottom: 1.25rem;
    }
    .card-label { font-weight: 700; font-size: 1.05rem; color: #e5e1f0; margin-bottom: 0.6rem; }
    .answer-text { font-size: 1.05rem; line-height: 1.6; color: #f3f1f8; white-space: pre-wrap; }

    /* ---------- How It Works ---------- */
    .info-card {
        background: #161220;
        border: 1px solid rgba(168, 85, 247, 0.22);
        border-radius: 14px;
        padding: 1.1rem 1rem;
        height: 100%;
        box-shadow: 0 0 18px rgba(139, 92, 246, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .info-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 0 32px rgba(168, 85, 247, 0.28);
        border-color: rgba(168, 85, 247, 0.5);
    }
    .info-card-icon { font-size: 1.5rem; margin-bottom: 0.4rem; }
    .info-card-title { font-weight: 700; font-size: 0.95rem; color: #f3f1f8; margin-bottom: 0.35rem; }
    .info-card-desc { font-size: 0.82rem; color: #a1a1b5; line-height: 1.45; }

    .section-heading {
        color: #f3f1f8; font-weight: 700; font-size: 1.3rem;
        margin: 1.75rem 0 1rem 0;
    }

    /* ---------- Score ---------- */
    .score-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
    .score-number {
        font-size: 2.6rem; font-weight: 800; color: #ffffff;
        text-shadow: 0 0 24px rgba(168, 85, 247, 0.65);
    }

    .badge {
        display: inline-block; padding: 0.3rem 0.85rem; border-radius: 999px;
        font-weight: 600; font-size: 0.85rem; white-space: nowrap;
    }
    .badge-high { background: #052e1a; color: #4ade80; }
    .badge-medium { background: #3f2a05; color: #fbbf24; }
    .badge-low { background: #3f0a0a; color: #f87171; }

    .judge-chip {
        display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.3rem 0.7rem;
        border-radius: 8px; font-size: 0.85rem; font-weight: 500; margin: 0.2rem 0.3rem 0.2rem 0;
    }
    .judge-agree { background: #052e1a; color: #4ade80; }
    .judge-disagree { background: #3f0a0a; color: #f87171; }
    .judge-warn { background: #211d2e; color: #9b96ab; }

    /* ---------- Button ---------- */
    .stButton>button {
        border-radius: 10px; padding: 0.65rem 0; font-weight: 700; font-size: 1rem; width: 100%;
        background: linear-gradient(135deg, #8b5cf6, #ec4899);
        color: #ffffff; border: none;
        box-shadow: 0 0 24px rgba(168, 85, 247, 0.45);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 38px rgba(168, 85, 247, 0.7);
        color: #ffffff;
    }
    .stButton>button:active { transform: translateY(0); }

    /* ---------- Text area ---------- */
    .stTextArea textarea {
        background: #161220 !important;
        color: #f3f1f8 !important;
        border: 1px solid rgba(168, 85, 247, 0.3) !important;
        border-radius: 10px !important;
    }
    .stTextArea textarea:focus {
        border-color: #a855f7 !important;
        box-shadow: 0 0 0 1px #a855f7, 0 0 20px rgba(168, 85, 247, 0.4) !important;
    }
    .stTextArea textarea::placeholder { color: #6b6680 !important; }

    /* ---------- Progress bar ---------- */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #8b5cf6, #ec4899) !important;
    }
    .stProgress > div > div > div { background: #211d2e !important; }

    /* ---------- Tabs ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: #161220;
        border-radius: 10px;
        color: #a1a1b5;
        padding: 0.5rem 1rem;
        border: 1px solid rgba(168, 85, 247, 0.15);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #8b5cf6, #ec4899) !important;
        color: #ffffff !important;
        border: none !important;
    }

    /* ---------- Footer ---------- */
    .app-footer {
        text-align: center; color: #6b6680; font-size: 0.82rem;
        margin-top: 3rem; padding-top: 1.25rem;
        border-top: 1px solid rgba(168, 85, 247, 0.12);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-icon-box"><div class="hero-icon">🔍</div></div>
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
            <div class="info-card-icon">🎲</div>
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
            <div class="info-card-icon">⚖️</div>
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
            <div class="info-card-icon">📊</div>
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
