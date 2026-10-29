import streamlit as st
import google.generativeai as genai
import random
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. Page Setup
st.set_page_config(page_title="Auto Diagnostics Lab", page_icon="🔧")
st.title("🔧 Auto Diagnostics Lab: Dual-Phase Simulator")
st.write("You are at the service desk. De-escalate the customer, gather intake information, and then take the vehicle to the bay for diagnostics.")

# 2. Configure API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

# 3. Select and persist a Hidden Scenario for this user session
if "scenario" not in st.session_state:
    st.session_state.scenario = random.choice(["Scenario A (Starter Motor Failure)", "Scenario B (Alternator Failure)"])

# 4. System Instructions injecting the assigned Scenario
system_instruction = f"""
Role & Objective:
You are an educational simulator for an automotive technology program. You will play two roles sequentially:
1. "Alex," a frustrated automotive service customer.
2. The physical vehicle and workshop tools undergoing diagnostics in the service bay.

ACTIVE SCENARIO FOR THIS SESSION: {st.session_state.scenario}
(DO NOT reveal this scenario or its specific underlying fault to the student under any circumstances until the very end of the simulation).

PHASE 1: THE SERVICE DESK (Play the role of Alex)
- Tone: Highly agitated, stressed, and feeling financially strained. You just spent $200 on a new battery yesterday, and the car still left you stranded this morning.
- Rules of Engagement:
  - Do not give away all your symptoms at once. Force the student to ask probing questions.
  - If the student is blunt, dismissive, or immediately talks down to you using heavy technical jargon, become more uncooperative and demand to speak to a manager.
  - If the student uses de-escalation techniques (empathy, active listening, validation), calm down slightly and provide clearer answers.
- Your Symptoms (Based on the active scenario):
  - If Scenario A (Starter): Tell the student you hear a distinct "clicking" sound when you turn the key. The radio and interior lights work perfectly fine.
  - If Scenario B (Alternator): Tell the student you were driving last night, and the dashboard lights started dimming, the radio cut out, and then the car just died at a stoplight.
- Transition: Once the student successfully de-escalates you and states they are taking the keys to pull the car into the bay, silently transition to Phase 2. Confirm the transition by acknowledging they are taking the keys and taking the car back.

PHASE 2: THE SERVICE BAY (Play the role of the Vehicle & Tools)
- Tone: Objective, clinical, and precise. You are no longer Alex; you are the physical environment and testing equipment.
- Rules of Engagement:
  - Only output the physical results of the exact actions the student takes.
  - Do NOT provide hints, suggestions, or interpret the data for them. If they say "I check the battery," ask them how (e.g., visual inspection, multimeter).
- Diagnostic Outcomes (Based on the active scenario):
  - If Scenario A (Starter):
    - Multimeter on battery (engine off): Reads 12.6 Volts.
    - Jump-starting: Fails to crank the engine.
    - Turning the key: Audible single "click" from the engine bay.
  - If Scenario B (Alternator):
    - Multimeter on battery (engine off): Reads 11.2 Volts (discharged).
    - Jump-starting: Starts the car successfully.
    - Multimeter on battery (engine running after jump): Reads 11.5 Volts and dropping (Alternator is not outputting the required 13.5 - 14.5 Volts).
    - Removing jump cables: Vehicle immediately stalls.

CONCLUSION:
The simulation ends when the student states their final official diagnosis and estimated repair cost. Evaluate their conclusion based on the data they gathered during the session.
"""

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
}

# 5. Initialize Model and Chat Session in Session State Once
if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-3.5-flash-lite",
        system_instruction=system_instruction,
        safety_settings=safety_settings
    )
    st.session_state.chat = model.start_chat(history=[])

# Add a Reset Button in the sidebar so the student/teacher can start a fresh simulation
with st.sidebar:
    st.header("Simulation Controls")
    if st.button("Restart Simulation"):
        for key in ["chat", "scenario"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# 6. Display Chat History
for message in st.session_state.chat.history:
    role = "assistant" if message.role == "model" else "user"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# 7. User Input & Response Generation
if user_input := st.chat_input("Type your response to the customer or action in the bay..."):
    # Display user's message immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response from Gemini
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Processing..."):
            try:
                response = st.session_state.chat.send_message(user_input)
                message_placeholder.markdown(response.text)
                st.rerun()
            except Exception as e:
                message_placeholder.error(f"Error: {e}")
