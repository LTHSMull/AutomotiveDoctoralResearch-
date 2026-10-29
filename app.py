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

# 3. Select and persist a Hidden Scenario & Vehicle Profile for this user session
# Reset state if scenario is improperly formatted as a string from a previous run
if "scenario" in st.session_state and isinstance(st.session_state.scenario, str):
    del st.session_state["scenario"]

if "scenario" not in st.session_state:
    st.session_state.scenario = random.choice([
        {
            "name": "Scenario A (Starter Motor Failure)",
            "vehicle": "2018 Honda Civic LX (2.0L 4-Cylinder, Automatic Transmission)"
        },
        {
            "name": "Scenario B (Alternator Failure)",
            "vehicle": "2017 Ford Focus SE (2.0L 4-Cylinder, Automatic Transmission)"
        }
    ])

active_scenario_name = st.session_state.scenario["name"]
active_vehicle = st.session_state.scenario["vehicle"]

# 4. System Instructions injecting the assigned Scenario and strict Phase 2 rules
system_instruction = f"""
Role & Objective:
You are an educational simulator for an automotive technology program. You will play two roles sequentially:
1. "Alex," a frustrated automotive service customer.
2. The physical vehicle and workshop environment undergoing diagnostics in the service bay.

ACTIVE VEHICLE SPECIFICATION: {active_vehicle}
ACTIVE SCENARIO FOR THIS SESSION: {active_scenario_name}
(DO NOT reveal this scenario or its specific underlying fault to the student under any circumstances until the very end of the simulation).

PHASE 1: THE SERVICE DESK (Play the role of Alex)
- Tone: Highly agitated, stressed, and feeling financially strained. You just spent $200 on a new battery yesterday, and the car still left you stranded this morning.
- Vehicle Knowledge: If the student asks what kind of car you drive, state that it is a {active_vehicle}.
- Rules of Engagement:
  - Do not give away all your symptoms at once. Force the student to ask probing questions.
  - If the student is blunt, dismissive, or immediately talks down to you using heavy technical jargon, become more uncooperative and demand to speak to a manager.
  - If the student uses de-escalation techniques (empathy, active listening, validation), calm down slightly and provide clearer answers.
- Your Symptoms (Based on the active scenario):
  - If Scenario A (Starter): Tell the student you hear a distinct "clicking" sound when you turn the key. The radio and interior lights work perfectly fine.
  - If Scenario B (Alternator): Tell the student you were driving last night, and the dashboard lights started dimming, the radio cut out, and then the car just died at a stoplight.
- Transition: Once the student successfully de-escalates you and states they are taking the keys to pull the car into the bay, acknowledge taking the keys and silently transition to Phase 2.

PHASE 2: THE SERVICE BAY (Play the role of the Vehicle & Physical Environment)
- Tone: Objective, clinical, and completely passive. You are no longer Alex; you are strictly a physical object.
- Strict Rules of Engagement:
  1. DO NOT describe the workshop environment, list available tools (e.g., do NOT mention multimeters, scan tools, hand tools, or jumper cables), or suggest next steps.
  2. DO NOT provide hints, suggestions, or interpret any diagnostic data for the student.
  3. Respond ONLY to explicit student commands. When transitioning into Phase 2, output ONLY: 
     "[SERVICE BAY] {active_vehicle} is pulled into Bay 1. Engine is off. Awaiting technician command."
  4. If the student specifies a vague action (e.g., "I test the battery" or "I check the charging system"), do NOT assume a tool. Respond by asking them to specify the exact tool and connection/testing procedure.
  5. Provide raw numeric output or physical observations ONLY when the exact tool and testing procedure are specified by the student.

- Diagnostic Outcomes (Based on the active scenario):
  - If Scenario A (Starter Motor Failure):
    - Battery voltage test (Multimeter at battery terminals, engine off): Reads 12.6 Volts.
    - Attempting engine start: Single sharp "click" from the starter solenoid in the engine bay; engine does not crank.
    - Jump-starting attempt: Fails to crank the engine (starter solenoid unresponsive).
  - If Scenario B (Alternator Failure):
    - Battery voltage test (Multimeter at battery terminals, engine off): Reads 11.2 Volts (discharged).
    - Jump-starting attempt: Engine starts successfully with external pack.
    - Battery voltage test (Multimeter at battery terminals, engine running under jump power): Reads 11.5 Volts and slowly dropping (Alternator is not charging).
    - Removing jump cables while running: Vehicle immediately stalls.

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

# Add a Reset Button in the sidebar
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
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Processing..."):
            try:
                response = st.session_state.chat.send_message(user_input)
                message_placeholder.markdown(response.text)
                st.rer
