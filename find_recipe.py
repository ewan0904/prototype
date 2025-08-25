import requests
import streamlit as st

def get_recipe(input):

    payload = {"question": input}
    try:
        response = requests.post(st.secrets['DATASTAX_API'], json=payload)
        response_text = response.json()['text']
        recipe_ids = response_text.split(",")
        recipe_ids = [x.strip() for x in recipe_ids]
        return recipe_ids
    except requests.exceptions.RequestException as e:
        return f"Error making API request: Please inform me about this."
    except (IndexError, KeyError, ValueError) as e:
        return f"Probably no recipes were found. Please try to alter your prompt or search for another recipe."        
