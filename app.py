import html
import streamlit as st
from graph import build_graph

st.set_page_config(page_title="LLM Trust Score", page_icon="🔍", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

    .block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 760px; }

    .hero { text-align: center; margin-bottom: 2rem; }
    .hero-icon { font-size: 2.75rem; line-height: 1; }
    .hero-title {
        font-size: 2.1rem; font-weight: 800; margin: 0.4rem 0 0.25rem 0;
        background: linear-gradient(90deg, #6366f1, #ec4899);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero-sub { color: #6b7280; font-size: 1rem; }

    .card {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 16px;
        padding: 1.5rem 1.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); margin-bottom: 1.25rem;
    }
    .card-label { font-weight: 700; font-size: 1.05rem; color: #374151; margin-bottom: 0.6rem; }
    .answer-text { font-size: 1.05rem; line-height: 1.6; color: #111827; white-space: pre-wrap; }

    .score-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
    .score-number { font-size: 2.5rem; font-weight: 800; color: #111827; }

    .badge {
        display: inline-block; padding: 0.3rem 0.85rem; border-radius: 999px;
        font-weight: 600; font-size: 0.85rem; white-space: nowrap;
    }
    .badge-high { background: #dcfce7; color: #15803d; }
    .badge-medium { background: #fef3c7; color: #b45309; }
    .badge-low { background: #fee2e2; color: #b91c1c; }

    .judge-chip {
        display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.3rem 0.7rem;
        border-radius: 8px; font-size: 0.85rem; font-weight: 500; margin: 0.2rem 0.3rem 0.2rem 0;
    }
    .judge-agree { background: #ecfdf5; color: #047857; }
    .judge-disagree { background: #fef2f2; color: #b91c1c; }
    .judge-warn { background: #f9fafb; color: #6b7280; }

    .stButton>button { border-radius: 10px; padding: 0.6rem 0; font-weight: 600; font-size: 1rem; width: 100%; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-icon">🔍</div>
      <div class="hero-title">LLM Trust Score</div>
      <div class="hero-sub">Get an AI answer, then see exactly how much you can trust it.</div>
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

        st.markdown("### Judge Breakdown")

        per_answer = verification["per_answer"]
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
