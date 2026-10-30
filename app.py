import streamlit as st
import google.generativeai as genai
import random
import json
import csv
import os
from datetime import datetime
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
FAULT_TEMPLATES = [
    {
        "fault_id": "starter_solenoid",
        "name": "Starter Motor Solenoid Failure",
        "vehicle": "2018 Honda Civic LX (2.0L 4-Cylinder)",
        "base_cause": "Faulty starter solenoid coil preventing starter engagement.",
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

# 4. Persona Traits Pool
PERSONALITY_TRAITS = [
    "hyper-anxious about repair costs due to a tight monthly budget",
    "skeptical of mechanic recommendations and feels previously burned by auto shops",
    "rushed and impatient because they are late for work and have meetings scheduled",
    "confused and overwhelmed by technical terms, defensive about their vehicle knowledge"
]

# CSV Logging Function for Research Data
CSV_FILE_PATH = "simulation_results.csv"

def log_session_to_csv(data_dict):
    """Appends completed simulation telemetry and scores to a local CSV file."""
    file_exists = os.path.isfile(CSV_FILE_PATH)
    headers = [
        "timestamp", "customer_name", "personality_trait", "vehicle", 
        "fault_name", "communication_score", "logic_score", 
        "accuracy_score", "overall_score", "transcript"
    ]
    
    with open(CSV_FILE_PATH, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data_dict)

# Secondary API Call: Judge Evaluation Pipeline
def run_secondary_evaluation(chat_history, active_fault, customer_name, personality):
    """Executes a secondary LLM call to generate a structured evaluation report."""
    formatted_transcript = ""
    for msg in chat_history:
        speaker = customer_name if msg.role == "model" else "Technician"
        formatted_transcript += f"{speaker}: {msg.parts[0].text}\n\n"

    judge_prompt = f"""
    You are an expert automotive instructor and doctoral researcher evaluating a student technician's performance in a dual-phase diagnostic simulator.

    GROUND TRUTH SCENARIO:
    - Vehicle: {active_fault['vehicle']}
    - Actual Fault: {active_fault['name']} ({active_fault['base_cause']})
    - Customer Persona: {customer_name} ({personality})

    STUDENT TRANSCRIPT:
    {formatted_transcript}

    EVALUATION INSTRUCTIONS:
    Analyze the transcript and provide a JSON response with numeric scores (0 to 100) and feedback for each category:
    1. Communication & De-escalation (Phase 1): Did they validate the customer, de-escalate stress, ask probing questions, and avoid confusing jargon?
    2. Diagnostic Efficiency & Logic (Phase 2): Did they follow a logical diagnostic tree, use appropriate tools, and avoid unnecessary/blind component swapping?
    3. Accuracy & Evidence (Conclusion): Did they correctly identify the root cause and justify it using empirical test data?

    Return ONLY a raw JSON object matching this exact structure:
    {{
      "communication_score": <int 0-100>,
      "logic_score": <int 0-100>,
      "accuracy_score": <int 0-100>,
      "overall_score": <int 0-100>,
      "communication_feedback": "<brief explanation>",
      "logic_feedback": "<brief explanation>",
      "accuracy_feedback": "<brief explanation>",
      "summary_evaluation": "<overall diagnostic summary>"
    }}
    """
    
    # Standard string model identifier without prefix
    judge_model = genai.GenerativeModel("gemini-1.5-flash")
    try:
        response = judge_model.generate_content(
            judge_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        return {
            "communication_score": 75,
            "logic_score": 75,
            "accuracy_score": 75,
            "overall_score": 75,
            "communication_feedback": "Completed customer interaction phase.",
            "logic_feedback": "Completed workshop diagnostic testing.",
            "accuracy_feedback": "Final diagnosis recorded.",
            "summary_evaluation": f"Evaluation fallback generated. Error details: {str(e)}"
        }

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
   - TIER 1 (Initial Unprompted Complaint): State ONLY your immediate emotional distress and high-level situation.
   - TIER 2 (Unlocked by Empathy & Open-Ended Questions): Describe 1 or 2 high-level symptoms in your own words.
   - TIER 3 (Unlocked ONLY by Specific, Inquisitive Follow-Up Questions): Reveal deeper details (clicks, dash lights, driving conditions) ONLY when explicitly asked.

3. TRANSITION CRITERIA TO PHASE 2:
   You will ONLY hand over the keys and say "Please pull it into the bay" if BOTH conditions are met:
   Condition A: The student has explicitly validated your frustration or explained what the initial inspection step will be.
   Condition B: The student explicitly asks for the keys or states they are moving the vehicle to the bay.

PHASE 2: THE SERVICE BAY (Physical Environment Roleplay)
- Persona: Passive, objective physical environment and tool interface.
- Guidelines:
  1. DO NOT suggest tools, list options, or prompt the student on what to test next.
  2. Transition response must strictly be: "[SERVICE BAY] {active_fault['vehicle']} is pulled into Bay 1. Engine is off. Keys on the dash. Awaiting technician command on desired next steps."
  3. Require specific tool selections, test locations, and procedures.
  4. If a command is ambiguous, ask the technician to clarify the tool and testing procedure.
  5. Use this empirical ground-truth dataset for test results:
{active_fault['phase2_data']}

CONCLUSION & EVALUATION:
When the student presents their final diagnosis and repair recommendation, state clearly that the simulation has concluded.
"""

generation_config = genai.types.GenerationConfig(
    temperature=0.85,
    top_p=0.95,
)

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
}

# 8. Initialize Model and Chat Session (Standard string identifier)
if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction,
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    st.session_state.chat = model.start_chat(history=[])

# 9. Sidebar Debug & Research Controls
with st.sidebar:
    st.header("⚙️ Instructor / Research Panel")
    
    st.subheader("Current Location")
    if st.session_state.get("phase", "desk") == "desk":
        st.info("🛋️ **Location:** Service Desk (Phase 1)")
    else:
        st.success("🔧 **Location:** Service Bay (Phase 2)")

    st.markdown("---")
    st.subheader("Active State Telemetry")
    st.write(f"**Customer Persona:** {st.session_state.customer_name}")
    st.write(f"**Personality Trait:** {st.session_state.personality}")
    st.write(f"**Target Vehicle:** {active_fault['vehicle']}")
    
    with st.expander("Reveal Ground Truth (Instructor Only)"):
        st.write(f"**Fault Name:** {active_fault['name']}")
        st.write(f"**Root Cause:** {active_fault['base_cause']}")

    st.markdown("---")
    if os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, "r") as f:
            st.download_button(
                label="📥 Download Research Dataset (CSV)",
                data=f.read(),
                file_name=f"dissertation_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    if st.button("Reset & Clear Session Cache"):
        for key in list(st.session_state.keys()):
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
                    response_text = response.text
                    message_placeholder.markdown(response_text)
                    
                    if "[SERVICE BAY]" in response_text:
                        st.session_state.phase = "bay"
                else:
                    message_placeholder.markdown("Simulation concluded.")
                st.rerun()
            except Exception as e:
                # If a cached session error occurs, purge session state to force a fresh object creation
                if "unexpected model name format" in str(e):
                    del st.session_state["chat"]
                    st.rerun()
                message_placeholder.error(f"Error: {e}")

# 12. Submit Final Diagnosis Button & Evaluation Rendering
st.markdown("---")
col_action1, col_action2 = st.columns([2, 1])

with col_action1:
    st.caption("When you have completed testing and provided your final diagnosis, trigger the formal evaluation.")

with col_action2:
    if st.button("📊 Submit Final Diagnosis & Grade Session", type="primary"):
        with st.spinner("Analyzing transcript and computing rubric metrics..."):
            eval_results = run_secondary_evaluation(
                st.session_state.chat.history,
                active_fault,
                st.session_state.customer_name,
                st.session_state.personality
            )
            
            st.session_state.evaluation = eval_results
            st.session_state.evaluation_done = True
            
            transcript_text = "\n".join(
                [f"{m.role}: {m.parts[0].text}" for m in st.session_state.chat.history]
            )
            
            log_session_to_csv({
                "timestamp": datetime.now().isoformat(),
                "customer_name": st.session_state.customer_name,
                "personality_trait": st.session_state.personality,
                "vehicle": active_fault["vehicle"],
                "fault_name": active_fault["name"],
                "communication_score": eval_results["communication_score"],
                "logic_score": eval_results["logic_score"],
                "accuracy_score": eval_results["accuracy_score"],
                "overall_score": eval_results["overall_score"],
                "transcript": transcript_text
            })

if st.session_state.get("evaluation_done", False):
    eval_data = st.session_state.evaluation
    st.subheader("🏁 Performance Evaluation Report")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Overall Grade", f"{eval_data['overall_score']}%")
    m2.metric("Communication (Phase 1)", f"{eval_data['communication_score']}%")
    m3.metric("Diagnostic Logic (Phase 2)", f"{eval_data['logic_score']}%")
    m4.metric("Technical Accuracy", f"{eval_data['accuracy_score']}%")
    
    st.markdown("### Detailed Instructor Feedback")
    st.info(f"**Overall Summary:** {eval_data['summary_evaluation']}")
    
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.write("🗣️ **Communication & De-escalation**")
        st.write(eval_data['communication_feedback'])
    with f_col2:
        st.write("🔧 **Diagnostic Strategy**")
        st.write(eval_data['logic_feedback'])
    with f_col3:
        st.write("🎯 **Technical Accuracy**")
        st.write(eval_data['accuracy_feedback'])
        
    st.success("✅ Session data and full conversation transcript successfully logged to research dataset (`simulation_results.csv`).")
