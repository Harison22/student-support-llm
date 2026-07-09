import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000/ask"

st.set_page_config(page_title="Student Support Assistant", layout="centered")

# --- CUSTOM CSS FOR CHATGPT-LIKE ALIGNMENT ---
st.markdown("""
    <style>
        /* Target the user message container and pull it to the right */
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
            flex-direction: row-reverse !important;
            text-align: right !important;
        }
        
        /* Keep the inner content bubble clean when flipped */
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) .stMarkdown {
            display: inline-block;
            text-align: left;
            background-color: #f0f2f6;
            padding: 10px 15px;
            border-radius: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# --- CLEAN HEADER SECTION (NO LOGO) ---
st.title("🎓 Student Support Assistant")
st.caption("Ask about registration, financial aid, housing, and academic support.")

# 1. Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! How can I help you with university services today?"}
    ]

# 2. Display existing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. Accept user input
if question := st.chat_input("Ask a question about university services..."):
    
    with st.chat_message("user"):
        st.markdown(question)
        
    st.session_state.messages.append({"role": "user", "content": question})

    # 4. Fetch response from backend
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = requests.post(
                    BACKEND_URL,
                    json={"question": question},
                    timeout=60
                )

                if response.status_code == 200:
                    answer = response.json()["response"]
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_msg = f"Backend error: {response.text}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the backend server. Please make sure it is running.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")