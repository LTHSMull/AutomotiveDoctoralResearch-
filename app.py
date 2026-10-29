import streamlit as st
import google.generativeai as genai

# 1. Page Setup
st.title("🔧 Auto Diagnostics Lab: Phase 1")
st.write("You are at the service desk. Talk to the customer to figure out what is wrong.")

# 2. Securely get the API key from Streamlit's secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. Configure the AI Model and the "Hidden Prompt"
# This is where your dissertation design happens!
system_instruction = """
You are an angry customer at an auto repair shop. 
Your car is shaking when braking, but do not say that directly. 
Only say you are frustrated and late for work. 
Force the student to ask you calming, probing questions to figure out the symptoms.
"""

# Initialize the model with the instructions
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=system_instruction
)

# 4. Set up the Chat Memory
# This keeps the AI from forgetting the conversation after every message
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# Display all previous messages in the chat window
for message in st.session_state.chat.history:
    role = "assistant" if message.role == "model" else "user"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# 5. The Chat Input Box
user_input = st.chat_input("What do you say to the customer?")

if user_input:
    # Show what the student typed
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Send it to Gemini and show the response
    with st.chat_message("assistant"):
        response = st.session_state.chat.send_message(user_input)
        st.markdown(response.text)
