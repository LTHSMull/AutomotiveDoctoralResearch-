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
    file_exists = os.path.isfile
