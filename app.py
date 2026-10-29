import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. Page Setup
st.title("🔧 Auto Diagnostics Lab: Phase 1")
st.write("You are at the service desk. Talk to the customer to figure out what is wrong.")

# 2. Securely get the API key
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. Configure the AI Model and the "Hidden Prompt"
system_instruction = """
You are an angry customer at an auto repair shop. 
Your car is shaking when braking, but do not say that directly. 
Only say you are frustrated and late for work. 
Force the student to ask you calming, probing questions to figure out the symptoms.
"""

# Lower the safety settings so it is allowed to roleplay an angry person
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel(
    model_name="gemini-3.8-flash",
    system_instruction=system_instruction,
    safety_settings=safety_settings
)

# 4. Set up the Chat Memory
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# Display all previous messages
for message in st.session_state.chat.history:
    role = "assistant" if message.role == "model" else "user"
    with st.chat_message(role):
        try:
            st.markdown(message.parts[0].text)
        except Exception:
            st.markdown("*[Message blocked or unreadable]*")

# 5. The Chat Input Box
user_input = st.chat_input("What do you say to the customer?")

if user_input:
    # Show what the student typed
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Send it to Gemini and show the response safely
    with st.chat_message("assistant"):
        try:
            # We use a spinner so you know it's actually "thinking" and not just frozen
            with st.spinner("Customer is responding..."):
                response = st.session_state.chat.send_message(user_input)
                st.markdown(response.text)
        except ValueError as e:
            st.error("Google's safety filters blocked the AI's response. It got too angry!")
        except Exception as e:
            st.error(f"System Error: {e}")
