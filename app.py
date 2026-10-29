import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. Page Setup
st.set_page_config(page_title="Auto Diagnostics Lab", page_icon="🔧")
st.title("🔧 Auto Diagnostics Lab: Phase 1")
st.write("You are at the service desk. Talk to the customer to figure out what is wrong.")

# 2. Configure API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

# 3. System Instructions & Safety Settings
system_instruction = """
You are an angry customer at an auto repair shop. 
Your car is shaking when braking, but do not say that directly. 
Only say you are frustrated and late for work. 
Force the student to ask you calming, probing questions to figure out the symptoms.
"""

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
}

# 4. Initialize Model and Chat Session in Session State Once
if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-3.5-flash-lite",
        system_instruction=system_instruction,
        safety_settings=safety_settings
    )
    st.session_state.chat = model.start_chat(history=[])

# 5. Display Chat History
for message in st.session_state.chat.history:
    role = "assistant" if message.role == "model" else "user"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# 6. User Input & Response Generation
if user_input := st.chat_input("What do you say to the customer?"):
    # Display user's message immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response from Gemini
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Customer is responding..."):
            try:
                response = st.session_state.chat.send_message(user_input)
                message_placeholder.markdown(response.text)
                st.rerun()  # Forces Streamlit to update the UI cleanly
            except Exception as e:
                message_placeholder.error(f"Error: {e}")
