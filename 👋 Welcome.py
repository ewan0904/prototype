import streamlit as st
from utils.functions import initialize_session_state
from utils.auth import check_auth

# --- Authentication ---
# This ensures only authorized users can access the page.
#check_auth()

# --- Session State Initialization ---
# Sets up default session state variables (if they are not already defined).
initialize_session_state()

# --- Page Configuration ---
# Sets the browser tab title and layout for this page.
st.set_page_config(
    page_title="Welcome",
    layout="wide"
)

# --- Page Content ---
# Renders a markdown-formatted welcome message to guide the user for the purpose of my survey.
st.markdown(
"""
# Welcome, and Thank You for Participating!

We appreciate your time and interest in taking part in this research project.

---

## 🧠 Motivation  

Many existing applications recommend recipes based on your preferences and search input. This prototype is not claiming to offer only the best or most highly reviewed recipes—after all, taste is personal and subjective. The goal here is different.

This prototype was created to address a common gap: the lack of clear, accessible information about the **environmental impact** and **nutritional composition** of the recipes you choose. While cooking can be a source of sensory enjoyment, food choices also have deeper implications. If you’re curious about how your meals affect your health and the planet, this tool is designed with you in mind.

---

## 📱 How to Use This Application

- Use the **sidebar on the left** to navigate between different tabs.
- Each tab represents a specific step in the process and contains guidance on what to input and how it contributes to your personalized recipe suggestions.
- If you're interested in the technical side—how the filtering and recommendation system works, or other questions regarding the metrics and datasets used—check out the **More Information** section in the sidebar for more insights.

---

## ⚠️ Important Notes

- Before searching for recipes, please complete the form under the **"Personal Information"** tab.
- You can **adjust your preferences** if you don't want to rely on the default settings provided.

---

## 🥘 Enjoy Your Experience!

We hope this prototype helps you discover a recipe that suits both your taste and values.  
Thank you again for being part of this study!

"""
)