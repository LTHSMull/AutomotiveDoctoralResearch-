import streamlit as st
import google.generativeai as genai
import random
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. Page Setup
st.set_page_config(page_title="Auto Diagnostics Lab", page_icon="🔧", layout="wide")
st.title("🔧 Auto Diagnostics Lab: Dual-Phase Simulator")

# 2. Configure API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

# 3. Dynamic Archetype Pool (Core Mechanical Grounding)
# Updated FAULT_TEMPLATES with explicit phase1_complaint keys
FAULT_TEMPLATES = [
    {
        "fault_id": "starter_solenoid",
        "name": "Starter Motor Solenoid Failure",
        "vehicle": "2018 Honda Civic LX (2.0L 4-Cylinder)",
        "base_cause": "Faulty starter solenoid coil preventing starter engagement.",
        # Raw factual constraints instead of a rigid sentence
        "core_symptoms": [
            "Bought a brand new battery yesterday",
            "Vehicle fails to turn over/crank this morning",
            "Single sharp metallic click heard when key is turned",
            "Cabin lights, radio, and dashboard illuminate normally"
        ],
        "phase2_data": """
          - Multimeter at battery terminals (Engine Off): 12.6V.
          - Ignition attempt: Single sharp click from starter solenoid; engine does not turn over.
          - Jump-start attempt: Fails to crank (solenoid unresponsive).
          - Voltage drop test at starter main terminal during key turn: 12.5V present at main post, 12.5V at S-terminal, starter motor does not spin.
        """
    },
    {
        "fault_id": "charging_system",
        "name": "Alternator Diode / Charging Failure",
        "vehicle": "2017 Ford Focus SE (2.0L 4-Cylinder)",
        "base_cause": "Internal alternator failure causing no voltage output under load.",
        "core_symptoms": [
            "Car completely died while actively driving at night",
            "Headlights and dashboard instruments dimmed sequentially right before stalling",
            "Radio shut off on its own",
            "Stalled out at a stoplight and would not restart"
        ],
        "phase2_data": """
          - Multimeter at battery terminals (Engine Off): 11.2V (Discharged).
          - Jump-start attempt: Engine starts successfully with external pack.
          - Multimeter at battery terminals (Engine Running under jump): 11.5V and dropping.
          - Removing jump pack: Engine immediately stalls.
          - Belt inspection: Serpentine belt is intact and properly tensioned.
        """
    }
]
# 4. Persona Traits Pool for Procedural Customer Generation
PERSONALITY_TRAITS = [
    "hyper-anxious about repair costs due to a tight monthly budget",
    "skeptical of mechanic recommendations and feels previously burned by auto shops",
    "rushed and impatient because they are late for work and have meetings scheduled",
    "confused and overwhelmed by technical terms, defensive about their vehicle knowledge"
]

# 5. Initialize Simulation State
if "fault" not in st.session_state:
    st.session_state.fault = random.choice(FAULT_TEMPLATES)
    st.session_state.personality = random.choice(PERSONALITY_TRAITS)
    st.session_state.customer_name = random.choice(["Alex", "Jordan", "Morgan", "Taylor", "Chris"])
    st.session_state.phase = "desk"

active_fault = st.session_state.fault

# 6. Dynamically Constructed Master Instruction
system_instruction = f"""
Role & Objective:
You are an advanced educational simulator for a post-secondary automotive technology program. You play two distinct roles sequentially:
1. "{st.session_state.customer_name}," an automotive service customer bringing in a vehicle.
2. The physical workshop environment, vehicle components, and diagnostic tools in the service bay.

ACTIVE SCENARIO SPECIFICATION:
- Vehicle: {active_fault['vehicle']}
- Root Technical Cause: {active_fault['base_cause']}
- Customer Behavioral Profile: {st.session_state.personality}
(DO NOT explicitly reveal the exact root technical cause or scenario name to the student until the final evaluation).

PHASE 1: THE SERVICE DESK (Customer Roleplay)
- Name: {st.session_state.customer_name}
- Behavioral Profile: {st.session_state.personality}
- Raw Vehicle Symptoms Known to Customer: {active_fault['core_symptoms']}

STRICT CONVERSATIONAL PACING RULES:
1. DYNAMIC REFORMULATION: Do NOT quote the raw vehicle symptoms word-for-word. Synthesize them dynamically using the voice, vocabulary level, and emotional stress dictated by your behavioral profile ({st.session_state.personality}). Rephrase your story entirely on every playthrough.

2. INFORMATION TIERS (Reveal details ONLY when earned):
   
   - TIER 1 (Initial Unprompted Complaint): 
     State ONLY your immediate emotional distress and high-level situation (e.g., "I can't believe this, I just spent money fixing this car and now it's completely useless on my driveway!"). Do NOT describe symptoms or sounds yet.
   
   - TIER 2 (Unlocked by Empathy & Open-Ended Questions): 
     When the student listens attentively or asks what happened, describe 1 or 2 high-level symptoms from your known raw symptoms in your own informal words.
   
   - TIER 3 (Unlocked ONLY by Specific, Inquisitive Follow-Up Questions):
     Reveal deeper details (like specific click sounds, dash light behaviors, or driving conditions) ONLY when the student explicitly asks targeted questions about them.

3. TRANSITION CRITERIA TO PHASE 2:
   You will ONLY hand over the keys and say "Please pull it into the bay" if BOTH conditions are met:
   Condition A: The student has explicitly validated your frustration or explained what the initial inspection step will be.
   Condition B: The student explicitly asks for the keys or states they are moving the vehicle to the bay.

PHASE 2: THE SERVICE BAY (Physical Environment Roleplay)
- Persona: Passive, objective physical environment and tool interface.
- Guidelines:
  1. DO NOT suggest tools, list options, or prompt the student on what to test next.
  2. Transition response must strictly be: "[SERVICE BAY] {active_fault['vehicle']} is pulled into Bay 1. Engine is off. Keys on the dash. Awaiting technician command on desired next steps."
  3. Require specific tool selections, test locations, and procedures (e.g., "I connect a multimeter set to DC Volts across the battery terminals").
  4. If a command is ambiguous, ask the technician to clarify the tool and testing procedure.
  5. Use this empirical ground-truth dataset for test results:
{active_fault['phase2_data']}

CONCLUSION & EVALUATION:
When the student presents their final diagnosis and repair recommendation:
1. Evaluate their communication strategy during Phase 1 (de-escalation, empathy, clarity).
2. Evaluate their diagnostic logic in Phase 2 (systematic testing vs. component swapping/guessing).
3. Confirm whether the root cause was correctly identified and supported by empirical evidence.
"""

# 7. Model Configuration with Temperature for Variation
generation_config = genai.types.GenerationConfig(
    temperature=0.85,  # Slightly higher temperature introduces dialogue and response variation
    top_p=0.95,
)

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
}

# 8. Initialize Model and Chat Session
if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-3.5-flash-lite",
        system_instruction=system_instruction,
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    st.session_state.chat = model.start_chat(history=[])

# 9. Sidebar Debug & Research Controls
with st.sidebar:
    st.header("⚙️ Instructor / Research Panel")
    st.subheader("Active State Telemetry")
    st.write(f"**Customer Persona:** {st.session_state.customer_name}"
    st.write(f"**Target Vehicle:** {active_fault['vehicle']}")
    
    # Hide root cause behind an expander for testing
    with st.expander("Reveal Ground Truth (Instructor Only)"):
        st.write(f"**Fault Name:** {active_fault['name']}")
        st.write(f"**Root Cause:** {active_fault['base_cause']}")

    st.markdown("---")
    if st.button("Reset & Generate New Persona/Fault"):
        for key in ["chat", "fault", "personality", "customer_name", "phase"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# 10. Render Conversation Interface
for message in st.session_state.chat.history:
    role = "assistant" if message.role == "model" else "user"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# 11. Process Inputs
if user_input := st.chat_input("Type your response to the customer or diagnostic action in the bay..."):
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Simulating environment..."):
            try:
                response = st.session_state.chat.send_message(user_input)
                if response.candidates and response.candidates[0].content.parts:
                    message_placeholder.markdown(response.text)
                else:
                    message_placeholder.markdown("Simulation concluded. Diagnostics and communication logs recorded.")
                st.rerun()
            except Exception as e:
                message_placeholder.error(f"Error: {e}")
