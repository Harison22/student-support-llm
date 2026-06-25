import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000/ask"

st.set_page_config(page_title="Student Support Assistant")

st.title("🎓 Student Support Assistant")

question = st.text_input(
    "Ask a question about university services:"
)

if st.button("Ask"):

    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            with st.spinner("Generating response..."):

                response = requests.post(
                    BACKEND_URL,
                    json={"question": question},
                    timeout=60
                )

                if response.status_code == 200:
                    answer = response.json()["response"]
                    st.success(answer)
                else:
                    st.error(
                        f"Backend error: {response.text}"
                    )

        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend.")

        except Exception as e:
            st.error(f"Error: {e}")