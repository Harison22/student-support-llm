import requests
import streamlit as st

BACKEND_BASE_URL = "http://localhost:8000"
ASK_URL = f"{BACKEND_BASE_URL}/ask"

st.set_page_config(page_title="Student Support Assistant", page_icon="🎓", layout="wide")

st.title("🎓 Student Support Assistant")
st.caption("Ask about registration, financial aid, housing, and academic support.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "saved_answers" not in st.session_state:
    st.session_state.saved_answers = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input("Ask a question about university services")

with st.sidebar:
    st.subheader("Quick actions")
    if st.button("Save latest answer"):
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            st.session_state.saved_answers.append(st.session_state.messages[-1]["content"])
            st.success("Saved the latest answer.")
        else:
            st.info("Ask a question first to save an answer.")

    st.subheader("Saved answers")
    if st.session_state.saved_answers:
        for entry in st.session_state.saved_answers[-5:]:
            st.write(f"- {entry[:90]}{'...' if len(entry) > 90 else ''}")
    else:
        st.caption("No saved answers yet.")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    recent_context = [
        message["content"]
        for message in st.session_state.messages[:-1]
        if message["role"] == "user"
    ][-4:]

    try:
        with st.spinner("Generating response..."):
            response = requests.post(
                ASK_URL,
                json={
                    "question": prompt,
                    "conversation_context": recent_context,
                },
                timeout=60,
            )

        if response.status_code == 200:
            payload = response.json()
            answer = payload["response"]
            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.write(answer)
        else:
            error_message = response.text
            st.session_state.messages.append({"role": "assistant", "content": f"Backend error: {error_message}"})
            with st.chat_message("assistant"):
                st.error(error_message)

    except requests.exceptions.ConnectionError:
        error_message = "Cannot connect to the backend. Please ensure the API is running."
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        with st.chat_message("assistant"):
            st.error(error_message)

    except Exception as exc:
        st.session_state.messages.append({"role": "assistant", "content": f"Error: {exc}"})
        with st.chat_message("assistant"):
            st.error(f"Error: {exc}")
