import streamlit as st
import requests

API_URL = "http://localhost:8000"  # Change if running FastAPI elsewhere

st.set_page_config(page_title="Exam Question Generator", page_icon="📝", layout="centered")

st.title("📝 Exam Question Generator")
st.markdown("Generate medical exam questions from Plabable or Uni sources.")

source = st.selectbox("Select Question Source", ["plabable", "uni"])

with st.form("question_form"):
    n = st.number_input("Number of Questions", min_value=1, max_value=100, value=5)
    topic = None
    level = None

    if source == "uni":
        topic = st.text_input("Topic (optional)")
        level = st.number_input("Level (optional)", min_value=1, max_value=10, value=1)
        submitted = st.form_submit_button("Get Questions")
    else:
        topic = st.text_input("Topic (optional)")
        submitted = st.form_submit_button("Get Questions")

if submitted:
    with st.spinner("Fetching questions..."):
        params = {"n": n}
        if topic:
            params["topic"] = topic
        if source == "uni" and level:
            params["level"] = level

        try:
            endpoint = f"{API_URL}/{source}"
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            questions = response.json()
            if not questions:
                st.warning("No questions found for your query.")
            else:
                for idx, q in enumerate(questions, 1):
                    st.markdown(f"#### Question {idx}")
                    st.write(q.get('question', ''))
                    choices = q.get('choices', [])
                    if choices:
                        st.markdown("**Choices:**")
                        for c in choices:
                            st.write(f"- {c}")
                    st.markdown(f"**Answer:** {q.get('answer', '')}")
                    if q.get("explanation"):
                        with st.expander("Show Explanation"):
                            st.write(q["explanation"])
                    st.divider()
        except Exception as e:
            st.error(f"Error fetching questions: {e}")