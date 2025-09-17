import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from utils.functions import show_session_state_sidebar
from utils.functions import initialize_session_state
from utils.auth import check_auth

# --- Authentication ---
# Ensure only authorized users can access this page.
#check_auth() 

# --- Session State Initialization ---
# Sets up default session state variables (if they are not already defined).
initialize_session_state()

# --- Short references and variables ---
options = ['Default', 'Somewhat important', 'Important', 'Very important', "Exclude"]
factors = {"Default": 1.0, "Somewhat important": 1.25, "Important": 1.5, "Very important": 2.0, "Exclude": 0.0}
macros_weight = st.session_state.profile['Weights']['Macros']
micros_weight = st.session_state.profile['Weights']['Micros']
nutrients_importance = st.session_state.profile['Importance']
environment_weight = st.session_state.profile['Weights']['Environment']
environment_importance = st.session_state.profile['Importance']['Environment']

# ----------------------------------------------------------------------------------------------------
# --- Helper functions ---

def create_importance_radio(category, item):
    """
    Render a horizontal radio for an importance choice and return the selection.

    Args:
        category: One of "Macros", "Micros", or "Environment".
        item: The metric label to display and key into session-state dictionaries.

    Returns:
        The selected importance option as a string (must exist in `options`).
    """
    selected = st.radio(
        label=f"How important is {item} to you?",
        options=options, 
        index=options.index(st.session_state.profile['Importance'][f'{category}'][f'{item}']),
        horizontal=True,
        key=f'radio_{category}_{item}', 
        label_visibility="collapsed"
    )
    return selected

def set_default_nutritional_weights():
    """
    Overwrite macros/micros weights with a neutral default distribution.

    The defaults act as a baseline. The user's qualitative importance choices
    will scale these defaults before normalization.
    """
    default_macros_weight = {
    "Protein": 0.15,
    "Carbohydrates": 0.15,
    "Sugar": 0.10,
    "Fat": 0.15,
    "Saturated Fat": 0.05,
    "Trans Fat": 0.05,
    "Fiber": 0.05
    }

    default_micros_weights = {
    "Calcium": 1/60,
    "Iodine": 1/60,
    "Iron": 1/60,
    "Magnesium": 1/60,
    "Selenium": 1/60,
    "Salt": 1/60,
    "Zinc": 1/60,
    "Vitamin A": 1/60,
    "Vitamin B1": 1/60,
    "Vitamin B2": 1/60,
    "Vitamin B3": 1/60,
    "Vitamin B6": 1/60,
    "Vitamin B9": 1/60,
    "Vitamin B12": 1/60,
    "Vitamin C": 1/60,
    "Vitamin D": 1/60,
    "Vitamin E": 1/60,
    "Vitamin K": 1/60
    }

    for key, value in default_macros_weight.items():
        macros_weight[f'{key}'] = value

    for key, value in default_micros_weights.items():
        micros_weight[f'{key}'] = value

def set_default_environmental_weights():
    """
    Overwrite environmental weights with a neutral default distribution.
    """
    default_environment_weights = {
    "Climate Change": 1/11,
    "Ozone Layer Depletion": 1/11,
    "Particulate Matter": 1/11,
    "Toxicological Effects": 1/11,
    "Toxicological Effects (carcinogenic)": 1/11,
    "Acidification": 1/11,
    "Freshwater Eutrophication": 1/11,
    "Marine Eutrophication": 1/11,
    "Land Use": 1/11,
    "Water Use": 1/11,
    "Energy Use": 1/11
    }

    for key, value in default_environment_weights.items():
        environment_weight[f'{key}'] = value
    
def adjust_weights_nutritional():
    """
    Apply importance factors to macro/micro defaults and normalize to sum to 1.

    Steps:
        1) Reset to defaults.
        2) Multiply each default weight by its importance factor.
        3) Normalize so the sum across all macro+micro metrics equals 1.
        4) Write back normalized weights into session state.
    """
    # Set to default
    set_default_nutritional_weights()
    adjusted_weights = {}
    total_sum = 0
    
    # Scale macros by importance
    for metric in macros_weight:
        adjusted_weights[f'Macros {metric}'] = macros_weight[metric] * factors.get(nutrients_importance['Macros'][metric])
        total_sum += adjusted_weights[f'Macros {metric}']
    
    # Scale micros by importance
    for metric in micros_weight:
        adjusted_weights[f'Micros {metric}'] = micros_weight[metric] * factors.get(nutrients_importance['Micros'][f'{metric}'])
        total_sum += adjusted_weights[f'Micros {metric}']

    # Normalize back to per-group dicts
    for item in adjusted_weights:
        item_list = item.split(" ", maxsplit=1)
        category = item_list[0]
        metric = item_list[1]
        if "Macros" in category:
            macros_weight[f'{metric}'] = adjusted_weights[f'{category} {metric}'] / total_sum
        else:
            micros_weight[f'{metric}'] = adjusted_weights[f'{category} {metric}'] / total_sum

def adjust_weights_environmental():
    """
    Apply importance factors to environmental defaults and normalize to sum to 1.

    Steps:
        1) Reset to defaults.
        2) Multiply each default weight by its importance factor.
        3) Normalize so the sum across all environmental metrics equals 1.
        4) Write back normalized weights into session state.
    """
    # Set to default
    set_default_environmental_weights()
    adjusted_weights = {}
    total_sum = 0

    for metric in environment_weight:
        adjusted_weights[metric] = environment_weight[metric] * factors.get(environment_importance[metric])
        total_sum += adjusted_weights[metric]
    
    for item in adjusted_weights:
        environment_weight[metric] = adjusted_weights[metric] / total_sum
        
# ----------------------------------------------------------------------------------------------------
# --- Front-End ---
st.title("Your preferences")

st.markdown("""
<div style='font-size: 0.875rem; font-family: "Source Sans Pro", sans-serif; line-height: 1.6;'>

The ranking fo the recipes is based on a variety of metrics, each with an associated weight. Below, you'll find all the metrics we take into account.

We’ve provided default values for each metric. However, you can adjust them by stating how important each one is to you.  
You can also choose to **exclude** certain metrics entirely. Excluded metrics won’t affect the recipe ranking, though we’ll still display their values for your reference.

⚠️ Please note: you must keep **at least one metric selected in each category** (Health and Environment).

</div>
""", unsafe_allow_html=True)
st.write("---")

# --- Overall (Health vs Environment) ---
st.subheader("**Combined**")
with st.expander("**Overall Weights**", expanded=False, icon="⚖️"):
    st.markdown(f"""
    <div style='font-size: 0.875rem; font-family: "Source Sans Pro", sans-serif; line-height: 1.6;'>
    The following slider allows you to set your overall preference of your health-environment distribution. <br>
    If you wish to prioritize <b>Health</b>, move the slider to the left. <br>
    If you wish to prioritize <b>Environment</b>, move the slider to the right. <br>
    If you are equally concerned about the environment as about your health, you can stick with the <b>50/50 default</b>.<br> 
    </div>
    """, unsafe_allow_html=True)
    with st.form("overall_weights_form"):
        col1, col2, col3 = st.columns([1.5, 5, 1.5])  # adjust column ratios to suit layout

        with col1:
            st.markdown("⬅️ *Health*")

        with col2:
            importance = st.slider(
                "Select the importance",
                min_value=0,
                max_value=100,
                value=int(st.session_state.profile['Weights']['Overall']['Environment']),
                step=1,
                label_visibility="collapsed"
            )

        with col3:
            st.markdown("➡️ *Environment*")

        if st.form_submit_button("Save"):
            st.session_state.profile['Weights']['Overall']['Environment'] = importance
            st.session_state.profile['Weights']['Overall']['Health'] = 100 - st.session_state.profile['Weights']['Overall']['Environment']

# --- Health: Macro-Nutrients ---
st.subheader("Health")
with st.expander("**Macro-Nutrients**", expanded=False, icon="📊"):

    with st.form("radio_macros_weights"):
        overall_preferences = {}

        for item in st.session_state.profile['Importance']['Macros']:
            st.write(f'**{item}**')
            selected = create_importance_radio('Macros', item)
            overall_preferences[f"{item}"] = selected
            st.write("---")

        if st.form_submit_button("Save"):
            for key in overall_preferences:
                st.session_state.profile['Importance']['Macros'][f'{key}'] = overall_preferences[key]

            adjust_weights_nutritional()
        
# --- Health: Micro-Nutrients ---
with st.expander("**Micro-Nutrients**", expanded=False, icon="🥕"):

    with st.form("radio_micros_weights"):
        overall_preferences = {}

        for item in st.session_state.profile['Importance']['Micros']:
            st.write(f'**{item}**')
            selected = create_importance_radio('Micros', item)
            overall_preferences[f"{item}"] = selected
            st.write("---")

        if st.form_submit_button("Save"):
            for key in overall_preferences:
                st.session_state.profile['Importance']['Micros'][f'{key}'] = overall_preferences[key]

            adjust_weights_nutritional()

# --- Environment ---
st.subheader("Environment")
with st.expander("**Environmental Aspects**", expanded=False, icon="🌎"):
        
    with st.form("radio_environment_weights"):
        overall_preferences = {}

        for item in st.session_state.profile['Importance']['Environment']:
            st.write(f'**{item}**')
            selected = create_importance_radio('Environment', item)
            overall_preferences[f"{item}"] = selected
            st.write("---")

        if st.form_submit_button("Save"):
            for key in overall_preferences:
                st.session_state.profile['Importance']['Environment'][f'{key}'] = overall_preferences[key]

            adjust_weights_environmental()