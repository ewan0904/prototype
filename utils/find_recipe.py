import requests
import streamlit as st

def get_recipe(input):
    """
    Sends a recipe-related question to a remote API and retrieves a list of recipe IDs.

    This function uses the DATASTAX_API endpoint stored in Streamlit secrets to send
    a POST request containing the user's question. It expects the API to return JSON
    with a 'text' field containing comma-separated recipe IDs.

    Args:
        input (str): The user-provided question or query about recipes.

    Returns:
        list[str] | str:
            - On success: A list of recipe ID strings.
            - On failure: A descriptive error message string.

    Raises:
        None directly — all exceptions are caught and handled gracefully.
    """
    
    # Prepare the payload with the user's query
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
