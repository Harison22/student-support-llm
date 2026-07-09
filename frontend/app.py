import streamlit as st
import requests
from datetime import datetime

BACKEND_URL = "http://localhost:8000/ask"

st.set_page_config(
    page_title="UDSM Student Assistant",
    page_icon="🎓",
    layout="wide"
)

# ========== SESSION STATE ==========
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! How can I help you with university services today?"}
    ]
if "conversation_count" not in st.session_state:
    st.session_state.conversation_count = 0

# ========== SIDEBAR ==========
with st.sidebar:
    st.title("📚 Student Support")
    
    # --- FAQ SECTION ---
    st.subheader("❓ Frequently Asked Questions")
    with st.expander("How do I register for courses?"):
        st.write("Course registration at UDSM is done online through the student portal. The registration period is typically announced at the start of each semester. Please check the academic calendar for specific dates.")
    with st.expander("Where are the hostels?"):
        st.write("UDSM hostels are located on the main campus in Dar es Salaam. Accommodation is allocated on a first-come, first-served basis, with priority given to first-year students and international students.")
    with st.expander("What are the library hours?"):
        st.write("The UDSM library is open from 8:00 AM to 10:00 PM on weekdays, and 9:00 AM to 5:00 PM on weekends. Hours may change during holidays.")
    with st.expander("How do I pay my fees?"):
        st.write("Fees can be paid through the UDSM student portal, via bank transfer, or at designated banks. Payment deadlines are published in the academic calendar.")
    with st.expander("When is the academic calendar?"):
        st.write("The academic calendar is published on the UDSM website. It includes important dates for registration, exams, and holidays.")
    st.divider()

    # --- Q&A HISTORY SECTION ---
    st.subheader("📝 Your Conversation History")
    
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! How can I help you with university services today?"}
        ]
        st.session_state.conversation_count = 0
        st.rerun()
    
    # Display Q&A history correctly
    if len(st.session_state.messages) > 1:
        qa_pairs = []
        for i in range(len(st.session_state.messages)):
            if st.session_state.messages[i]["role"] == "user":
                question = st.session_state.messages[i]["content"]
                answer = ""
                if i + 1 < len(st.session_state.messages) and st.session_state.messages[i+1]["role"] == "assistant":
                    answer = st.session_state.messages[i+1]["content"]
                qa_pairs.append({"q": question, "a": answer})
        
        for idx, pair in enumerate(qa_pairs, 1):
            with st.expander(f"Q{idx}: {pair['q'][:50]}..."):
                st.markdown(f"**Question:** {pair['q']}")
                st.markdown(f"**Answer:** {pair['a']}")
    else:
        st.info("No conversations yet. Ask a question to get started!")

# ========== MAIN CHAT AREA ==========
st.title("🎓 Student Support Assistant")
st.caption("Ask about registration, financial aid, housing, and academic support.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
question = st.chat_input("Ask a question about university services...")

if question:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.conversation_count += 1
    
    with st.chat_message("user"):
        st.write(question)
    
    # Fetch response from backend
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = requests.post(
                    BACKEND_URL,
                    json={"question": question},
                    timeout=60
                )
                
                if response.status_code == 200:
                    answer = response.json().get("response", "No response received.")
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_msg = f"Backend error: {response.status_code}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to the backend server. Please make sure it is running."
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    st.rerun()