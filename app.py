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

# 3. Define the Master Scenario Pool (7 Scenarios)
SCENARIO_POOL = [
    {
        "name": "Starter Motor Solenoid Failure",
        "vehicle": "2018 Honda Civic LX (2.0L 4-Cylinder, Automatic)",
        "phase1_complaint": "Frustrated. Spent $200 on a new battery yesterday, but the car won't start this morning. Hears a single sharp click when turning the key, but dashboard/lights work fine.",
        "phase2_data": """
          - Multimeter at battery terminals (Engine Off): 12.6 Volts.
          - Key turn attempt: Single sharp click from starter solenoid in engine bay; engine does not turn over.
          - Jump-starting attempt: Fails to crank engine (solenoid unresponsive).
        """
    },
    {
        "name": "Alternator Charging System Failure",
        "vehicle": "2017 Ford Focus SE (2.0L 4-Cylinder, Automatic)",
        "phase1_complaint": "Stressed. Was driving last night, dashboard lights dimmed, radio cut out, and the vehicle died at a stoplight. Spent money on a battery recently.",
        "phase2_data": """
          - Multimeter at battery terminals (Engine Off): 11.2 Volts (Discharged).
          - Jump-starting attempt: Engine starts successfully with external pack.
          - Multimeter at battery terminals (Engine Running under jump): 11.5 Volts and dropping (Alternator not supplying 13.5V-14.5V).
          - Removing jump pack while running: Engine immediately stalls.
        """
    },
    {
        "name": "HVAC Blend Door Actuator Failure (Clicking Dash)",
        "vehicle": "2016 Dodge Charger SXT (3.6L V6, Automatic)",
        "phase1_complaint": "Annoyed and distracted. Loud, repetitive clicking sound coming from behind the center dashboard whenever climate control is on. A/C or heat stuck blowing on the floor and won't switch to vents.",
        "phase2_data": """
          - Visual/Audible Inspection behind dashboard: Rapid clicking noise originating from climate control unit.
          - OBD-II / HVAC Scan Tool: Code B1081 (HVAC Blend Door Actuator Circuit / Position Error).
          - Multimeter at engine battery/charging system: 12.6 Volts (Engine compartment electrical systems operate normally).
          - Physical inspection under dash: Plastic gear teeth stripped on the driver-side blend door actuator assembly.
        """
    },
    {
        "name": "Timing Chain Stretch & Cam/Crank Correlation",
        "vehicle": "2015 Chevrolet Traverse LT (3.6L V6, Automatic)",
        "phase1_complaint": "Worried about major engine damage. Engine makes a loud rattling noise for a few seconds on cold startup, check engine light is illuminated, and acceleration feels sluggish under load.",
        "phase2_data": """
          - OBD-II Scan Tool: Codes P0008 / P0017 (Camshaft/Crankshaft Position Correlation Error Bank 1).
          - Engine visual/audible test (Engine running): Rattling noise present near front engine timing cover.
          - Multimeter / Charging system test: 13.8 Volts (Charging system operational).
          - Mechanical Scope / Compression: Timing chain stretch causing camshaft timing to lag behind crankshaft position.
        """
    },
    {
        "name": "AFM / DFM Lifter Collapse & Misfire",
        "vehicle": "2016 Chevrolet Silverado 1500 LT (5.3L V8 with AFM, Automatic)",
        "phase1_complaint": "Panicked. Truck is shaking violently while idling, check engine light is flashing continuously, and a loud, rhythmic ticking noise is coming from under the hood.",
        "phase2_data": """
          - OBD-II Scan Tool: Code P0300 / P0307 (Cylinder 7 Misfire Detected).
          - Audible Inspection: Loud metallic ticking sound originating from the driver-side valve cover (Cylinder 7 area).
          - Compression Test on Cylinder 7: 0 PSI (Dead cylinder).
          - Mechanical Inspection: Active Fuel Management (AFM) collapsed intake lifter on Cylinder 7, keeping valve closed.
        """
    },
    {
        "name": "Transmission Fluid Leak & Slippage",
        "vehicle": "2014 Nissan Altima 2.5 S (Continuously Variable Transmission)",
        "phase1_complaint": "Upset. Vehicle 'jumps' and lurches violently when accelerating from stops, struggles on hills, and noticed a reddish-brown fluid puddle under the car on the driveway.",
        "phase2_data": """
          - Fluid Spot Inspection: Sweet-smelling reddish-brown fluid leaking from transmission pan area.
          - Transmission Dipstick / Level Inspection: Fluid level far below minimum threshold; fluid dark and scorched.
          - Road/Bay Drive Test: Transmission slips significantly under load due to insufficient hydraulic pressure.
          - Underbody Inspection: Damaged transmission pan gasket leaking profusely under pressure.
        """
    },
    {
        "name": "Parasitic Electrical Draw",
        "vehicle": "2019 Jeep Wrangler Unlimited (3.6L V6 with Aftermarket Audio)",
        "phase1_complaint": "Frustrated. Battery dies every single night. Installed a brand-new battery twice this month, but every morning the vehicle is completely dead.",
        "phase2_data": """
          - Multimeter at battery (Engine Off, after sitting): 10.4 Volts (Depleted).
          - Alternator Charging Test (Engine running): 14.2 Volts (Charging system operates properly).
          - Parasitic Draw Test (Digital Multimeter in series with negative battery cable, vehicle asleep): Reads 650 mA draw (Normal threshold is under 50 mA).
          - Fuse Pull Test: Parasitic draw drops to 15 mA when Fuse F24 (Aftermarket amplifier/accessory circuit) is pulled.
        """
    }
]

# 4. Handle State Reset or Persistence
if "scenario" in st.session_state and not isinstance(st.session_state.scenario, dict):
    del st.session_state["scenario"]

if "scenario" not in st.session_state:
    st.session_state.scenario = random.choice(SCENARIO_POOL)

active_scenario = st.session_state.scenario

# 5. System Instructions injecting the assigned Scenario and strict Phase 2 rules
system_instruction = f"""
Role & Objective:
You are an educational simulator for an automotive technology program. You will play two roles sequentially:
1. "Alex," a frustrated automotive service customer.
2. The physical vehicle and workshop environment undergoing diagnostics in the service bay.

ACTIVE VEHICLE SPECIFICATION: {active_scenario['vehicle']}
ACTIVE SCENARIO NAME: {active_scenario['name']}
(DO NOT reveal the active scenario name, exact failure mechanism, or diagnostic answers to the student under any circumstances until the conclusion).

PHASE 1: THE SERVICE DESK (Play the role of Alex)
- Tone: Agitated, stressed, and concerned about repair costs or reliability.
- Vehicle Knowledge: State that you drive a {active_scenario['vehicle']}.
- Customer Complaint / Symptoms: {active_scenario['phase1_complaint']}
- Rules of Engagement:
  - Do not give away all symptoms at once. Force the student to ask probing, professional questions.
  - If the student is dismissive or talks down using unhelpful jargon, become uncooperative.
  - If the student uses de-escalation techniques (empathy, active listening, clear explanations), calm down and provide clearer answers.
- Transition: Once the student de-escalates you and states they are pulling the vehicle into the bay, acknowledge taking the keys and silently transition to Phase 2.

PHASE 2: THE SERVICE BAY (Play the role of the Vehicle & Physical Environment)
- Tone: Objective, clinical, and completely passive. You are no longer Alex; you are strictly a physical object.
- Strict Rules of Engagement:
  1. DO NOT describe the workshop environment, list available tools (e.g., do NOT mention multimeters, scan tools, hand tools, scope probes, or jumper cables), or suggest next steps.
  2. DO NOT provide hints, suggestions, or interpret any diagnostic data for the student.
  3. Respond ONLY to explicit student commands. When transitioning into Phase 2, output ONLY: 
     "[SERVICE BAY] {active_scenario['vehicle']} is pulled into Bay 1. Engine is off. Awaiting technician command."
  4. If the student specifies a vague action (e.g., "I check the engine" or "I test the electrical system"), do NOT assume a tool or test. Ask them to specify the exact tool, connection points, and procedure.
  5. Provide raw numeric output or physical observations ONLY when the exact tool and testing procedure are specified by the student.

- Diagnostic Outcomes (Based on student execution):
{active_scenario['phase2_data']}

CONCLUSION & EVALUATION:
When the student provides their final diagnosis and estimated repair approach:
1. Provide a detailed evaluation of their diagnostic path in your own words.
2. State whether their final diagnosis accurately identifies the root cause for {active_scenario['name']}.
3. Assess whether they gathered sufficient empirical evidence before drawing their conclusion.
"""

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
}

# 6. Initialize Model and Chat Session in Session State Once
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
    if st.button("Restart Simulation (New Random Scenario)"):
        for key in ["chat", "scenario"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# 7. Display Chat History
for message in st.session_state.chat.history:
    role = "assistant" if message.role == "model" else "user"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# 8. User Input & Response Generation
if user_input := st.chat_input("Type your response to the customer or action in the bay..."):
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Processing..."):
            try:
                response = st.session_state.chat.send_message(user_input)
                
                if response.candidates and response.candidates[0].content.parts:
                    message_placeholder.markdown(response.text)
                else:
                    message_placeholder.markdown("The simulation has concluded. Your diagnosis and evaluation have been recorded.")
                
                st.rerun()
            except Exception as e:
                message_placeholder.error(f"Error: {e}")
