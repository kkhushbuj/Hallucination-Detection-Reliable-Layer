import streamlit as st
from graph import build_graph

st.set_page_config(page_title="LLM Trust Score", page_icon="🔍", layout="centered")

st.title("🔍 LLM Trust Score")
st.caption("Get an AI answer, then see how much you can trust it.")

trust_graph = build_graph()

question = st.text_area("Ask a question", placeholder="e.g. What is the capital of Australia?")


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


if st.button("Get Answer & Check Trust", type="primary"):
    if not question.strip():
        st.warning("Please enter a question first.")
    else:
        with st.spinner("Getting answers and running trust checks..."):
            result = trust_graph.invoke({"question": question})

        verification = result["verification_result"]

        if verification.get("failed_generations"):
            with st.expander("Debug: raw generation errors"):
                st.write(verification["failed_generations"])

        st.markdown("### Answer")
        st.write(verification["winner_answer"].replace("$", "\\$"))

        st.divider()

        score = verification["trust_score"]
        if score >= 80:
            color = "green"
        elif score >= 50:
            color = "orange"
        else:
            color = "red"

        st.markdown(f"**Trust Score:** :{color}[{score}%] — {verification['label']}")
        st.write(verification["reasoning"].replace("$", "\\$"))

        st.divider()
        st.markdown("### Each Answer — Judge Breakdown")

        for i, a in enumerate(verification["per_answer"], 1):
            st.markdown(f"**Answer {i}:** {a['answer'].replace('$', chr(92)+'$')}")

            for j in a["judges"]:
                if j["failed"]:
                    reason = friendly_error(j.get("error", ""))
                    st.markdown(f"- {j['provider']}: ⚠️ {reason}")
                elif j["correct"]:
                    st.markdown(f"- {j['provider']}: ✅ Agree")
                else:
                    st.markdown(f"- {j['provider']}: ❌ Disagree (flagged hallucination)")

            correct_count = sum(1 for j in a["judges"] if j["correct"])
            total_responding = sum(1 for j in a["judges"] if not j["failed"])

            if total_responding == 0:
                st.warning("⚠️ No judges responded")
            elif correct_count > total_responding / 2:
                st.success(f"🟢 Stable — {correct_count}/{total_responding} judges agree")
            else:
                st.error(f"🔴 Not Stable — only {correct_count}/{total_responding} judges agree")

            st.caption(f"Score: {round(a['score']*100, 1)}% | Agreed with {round(a['consistency_fraction']*100)}% of other answers")
            st.markdown("---")