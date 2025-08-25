import streamlit as st
from find_recipe import get_recipe
from data.data_loader import load_recipes_data, load_ingredients_data
import pandas as pd
from functions import show_session_state_sidebar, initialize_session_state
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import ast
import math
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from auth import check_auth

check_auth()  # 🔐 Protect this page


# ----------------------------------------------------------------------------------------------------
st.markdown("# Find your Recipe")
initialize_session_state()
#show_session_state_sidebar()
# ----------------------------------------------------------------------------------------------------
# Load data
# ----------------------------------------------------------------------------------------------------
recipes_df = load_recipes_data()
ingredients_df = load_ingredients_data()
meals = st.session_state.profile['General']['Number_of_meals']
macros = st.session_state.profile['Macros']
micros = st.session_state.profile['Micros']
environment = st.session_state.profile['Environment']
weights = st.session_state.profile['Weights']
health_weight = st.session_state.profile['Weights']['Overall']['Health']
environment_weight = st.session_state.profile['Weights']['Overall']['Environment']

# ----------------------------------------------------------------------------------------------------
# Helper Functions - Calculations
# ----------------------------------------------------------------------------------------------------
# Macros
def calculate_macros_interval_score(name, value):
    weight = st.session_state.profile['Weights']['Macros'][name]
    lower_bound = (st.session_state.profile['Macros'][name][0]) / meals
    upper_bound = (st.session_state.profile['Macros'][name][1]) / meals
    interval = upper_bound - lower_bound

    # Check if the value is withing the interval, then it returns 1
    if lower_bound <= value <= upper_bound:
        return weight
    
    # Check if the value is below the lower bound of the interval
    elif lower_bound > value:
        return weight - min(weight, weight * ((lower_bound - value) / interval))
        
    else: 
        return weight - min(weight, weight * ((value - upper_bound) / interval))

# ----------------------------------------------------------------------------------------------------
def calculate_macros_UL_score(name, value):
    weight = st.session_state.profile['Weights']['Macros'][name]
    upper_limit = (st.session_state.profile['Macros'][name])/ meals

    if value <= upper_limit:
        return weight
    
    else:
        return weight - min(weight, weight * ((value - upper_limit) / upper_limit))
# ----------------------------------------------------------------------------------------------------
def calculate_macros_RDI_score(name, value):
    weight = st.session_state.profile['Weights']['Macros'][name]
    RDI = (st.session_state.profile['Macros'][name]) / meals

    if value == RDI:
        return weight

    else:
        deviation = abs((value - RDI) / RDI)
        return weight - min(weight, weight * deviation)

# ----------------------------------------------------------------------------------------------------
# Micros
def calculate_micros_UL_score(name, value):
    weight = st.session_state.profile['Weights']['Micros'][name]
    lower_bound = (st.session_state.profile['Micros'][name]) / meals # RDI
    upper_bound = (st.session_state.profile['Micros'][f'{name} UL']) / meals # Tolerable Upper Limit
    interval = upper_bound - lower_bound

    # Case 1: Value is within the optimal range → full score
    if lower_bound <= value <= upper_bound:
        return weight

    # Case 2: Value is below RDI → penalize based on how far below RDI (relative to RDI)
    elif value < lower_bound:
        deviation = (lower_bound - value) / lower_bound
        return weight - min(weight, weight * deviation)

    # Case 3: Value is above UL → penalize based on how far above UL (relative to interval)
    else:
        deviation = (value - upper_bound) / interval
        return weight - min(weight, weight * deviation)

# ----------------------------------------------------------------------------------------------------
def calculate_micros_RDI_score(name, value):
    weight = st.session_state.profile['Weights']['Micros'][name]
    RDI = (st.session_state.profile['Micros'][name]) / meals

    # Perfect match → full score
    if value == RDI:
        return weight

    # Calculate proportional deviation (absolute)
    deviation = abs(value - RDI) / RDI

    # Apply penalty
    return weight - min(weight, weight * deviation)

# ----------------------------------------------------------------------------------------------------
# Environment

def calculate_environment_score(name, value, servings):
    weight = st.session_state.profile['Weights']['Environment'][name]
    threshold = st.session_state.profile['Environment'][name] / servings
    ratio = value / threshold

    if ratio <= 1:
        return weight
    else:
        # Linear penalty proportional to how much value exceeds threshold
        penalty = min(weight, weight * (ratio - 1))  # Cap at full weight
        return round(weight - penalty, 4)
    
def calculate_environment_reverse_score(name, value, divider):
    weight = st.session_state.profile['Weights']['Environment'][name]
    value = (1 / float(value)) / divider
    threshold = st.session_state.profile['Environment'][name] / divider
    ratio = value / threshold
    if ratio >= 1:
            return weight
    else:
        penalty = min(weight, weight * (1 - ratio))
        return round(weight - penalty, 4)

# ----------------------------------------------------------------------------------------------------
# Total score
def calculate_score(recipe_id):
    health_contributions = {}
    environmental_contributions = {}
    recipe = recipes_df[recipes_df['recipe_id'] == recipe_id].copy().iloc[0]
    servings = int(recipe['Servings'])

    # Macros - Interval
    health_contributions['Protein'] = calculate_macros_interval_score('Protein', recipe['protein'])
    health_contributions['Fat'] = calculate_macros_interval_score('Fat', recipe['fat'])
    health_contributions['Carbohydrates'] = calculate_macros_interval_score('Carbohydrates', recipe['carbs'])
    # Macros - UL
    health_contributions['Saturated Fat'] = calculate_macros_UL_score('Saturated Fat', recipe['saturates'])
    health_contributions['Trans Fat'] = calculate_macros_UL_score('Trans Fat', recipe['Trans Fat (g)'])
    health_contributions['Sugar'] = calculate_macros_UL_score('Sugar', recipe['sugars'])
    # Macros - RDI
    health_contributions['Fiber'] = calculate_macros_RDI_score('Fiber', recipe['fibre'])
    # Micros - UL
    health_contributions['Calcium'] = calculate_micros_UL_score('Calcium', recipe['Calcium (mg)'])
    health_contributions['Iodine'] = calculate_micros_UL_score('Iodine', recipe['Iodine (µg)'])
    health_contributions['Iron'] = calculate_micros_UL_score('Iron', recipe['Iron (mg)'])
    health_contributions['Selenium'] = calculate_micros_UL_score('Selenium', recipe['Selenium (µg)'])
    health_contributions['Zinc'] = calculate_micros_UL_score('Zinc', recipe['Zinc (mg)'])
    health_contributions['Vitamin A'] = calculate_micros_UL_score('Vitamin A', recipe['Vitamin A RE (µg)'])
    health_contributions['Vitamin D'] = calculate_micros_UL_score('Vitamin D', recipe['Vitamin D (µg)'])
    health_contributions['Vitamin E'] = calculate_micros_UL_score('Vitamin E', recipe['Vitamin E (mg)'])
    # Micros - RDI
    health_contributions['Magnesium'] = calculate_micros_RDI_score('Magnesium', recipe['Magnesium (mg)'])
    health_contributions['Salt'] = calculate_micros_RDI_score('Salt', recipe['salt'])
    health_contributions['Vitamin B1'] = calculate_micros_RDI_score('Vitamin B1', recipe['Vitamin B1 (mg)'])
    health_contributions['Vitamin B2'] = calculate_micros_RDI_score('Vitamin B2', recipe['Vitamin B2 (mg)'])
    health_contributions['Vitamin B3'] = calculate_micros_RDI_score('Vitamin B3', recipe['Vitamin B3 (mg)'])
    health_contributions['Vitamin B6'] = calculate_micros_RDI_score('Vitamin B6', recipe['Vitamin B6 (mg)'])
    health_contributions['Vitamin B9'] = calculate_micros_RDI_score('Vitamin B9', recipe['Vitamin B9 (µg)'])
    health_contributions['Vitamin B12'] = calculate_micros_RDI_score('Vitamin B12', recipe['Vitamin B12 (µg)'])
    health_contributions['Vitamin C'] = calculate_micros_RDI_score('Vitamin C', recipe['Vitamin C (mg)'])
    health_contributions['Vitamin K'] = calculate_micros_RDI_score('Vitamin K', recipe['Vitamin K (µg)'])
    # Environment
    environmental_contributions['Climate Change'] = calculate_environment_score('Climate Change', recipe['Total - Co2 eq'], servings)
    environmental_contributions['Ozone Layer Depletion'] = calculate_environment_score('Ozone Layer Depletion', recipe['Total - CFC11 eq'] * 1000000000, servings)
    environmental_contributions['Particulate Matter'] = calculate_environment_reverse_score('Particulate Matter', recipe['Total - disease inc.'], 1000000)
    environmental_contributions['Toxicological Effects'] = calculate_environment_reverse_score('Toxicological Effects', recipe['Total - NC CTUh'], 1000000)
    environmental_contributions['Toxicological Effects (carcinogenic)'] = calculate_environment_reverse_score('Toxicological Effects (carcinogenic)', recipe['Total - C CTUh'], 1000000)
    environmental_contributions['Acidification'] = calculate_environment_score('Acidification', recipe['Total - mol H+ eq'], servings)
    environmental_contributions['Freshwater Eutrophication'] = calculate_environment_score('Freshwater Eutrophication', recipe['Total - P eq'] * 1000, servings)
    environmental_contributions['Marine Eutrophication'] = calculate_environment_score('Marine Eutrophication', recipe['Total - N eq'] * 1000, servings)
    environmental_contributions['Land Use'] = calculate_environment_score('Land Use', recipe['Total - pt dimensionless'], servings)
    environmental_contributions['Water Use'] = calculate_environment_score('Water Use', recipe['Total - m3'], servings)
    environmental_contributions['Energy Use'] = calculate_environment_score('Energy Use', recipe['Total - MJ'], servings)
    return health_contributions, environmental_contributions

# ----------------------------------------------------------------------------------------------------
# Helper Functions - HTML/Warning
# ----------------------------------------------------------------------------------------------------
def render_bar_macros_interval(name, unit, value, lower, upper):
    try:
        value = float(value)
        lower = float(lower) / meals
        upper = float(upper) / meals
        target_str = f"{lower:.1f}–{upper:.1f} {unit}"
    except (ValueError, TypeError):
        st.warning(f"{name} value is not numeric")
        return
    
    # Color logic
    if value < lower:
        color = "#FFA500"  # orange
    elif value > upper:
        color = "#FF4136"  # red
    else:
        color = "#2ECC71"  # green

    # Determine max scale
    max_value = max(value, upper)

    # Percent widths
    value_percent = min(value / max_value, 1.0) * 100
    interval_start = (lower / max_value) * 100
    interval_width = ((upper - lower) / max_value) * 100 if upper != lower else 0

    bar = f"""
    <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 4px;">
            <span>{name}</span>
            <span>Actual: {value:.1f} g &nbsp;&nbsp;|&nbsp;&nbsp; Recommended: {target_str}</span>
        </div>
        <div style="position: relative; height: 14px; background-color: #eee; border-radius: 7px; overflow: hidden;">
        <div style="width: {value_percent:.1f}%; background-color: {color}; height: 100%;"></div>
        <div style="
            position: absolute;
            left: {interval_start:.1f}%;
            width: {interval_width:.1f}%;
            top: 0;
            bottom: 0;
            background-color: rgba(0, 120, 0, 0.5);
            border-radius: 6px;
            z-index: 1;">
        </div>

    </div>
    """
    st.markdown(bar, unsafe_allow_html=True)

# ----------------------------------------------------------------------------------------------------
def render_bar_macros_UL(name, unit, value, upper):
    try:
        value = float(value)
        upper = float(upper) / meals
        target_str = f"{upper:.1f} {unit}"
    except (ValueError, TypeError):
        st.warning(f"{name} value is not numeric")
        return
    
    # Color logic
    if value <= upper:
        color = "#2ECC71"  # orange
    else:
        color = "#FF4136"  # red

    # Determine max scale
    max_value = max(value, upper)

    # Percent widths
    value_percent = min(value / max_value, 1.0) * 100
    upper_percent = min(upper/max_value, 1.0) * 100

    bar = f"""
    <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 4px;">
            <span>{name}</span>
            <span>Actual: {value:.1f} g &nbsp;&nbsp;|&nbsp;&nbsp; Limit: {target_str}</span>
        </div>
        <div style="position: relative; height: 14px; background-color: #eee; border-radius: 7px; overflow: hidden;">
        <div style="width: {value_percent:.1f}%; background-color: {color}; height: 100%;"></div>
            <div style="
                position: absolute;
                left: {upper_percent:.1f}%;
                top: 0;
                bottom: 0;
                width: 5px;
                background-color: #FF4136;
                z-index: 2;">
            </div>
    </div>
    """
    st.markdown(bar, unsafe_allow_html=True)

# ----------------------------------------------------------------------------------------------------
def render_bar_macros_RDI(name, unit, value, RDI):
    try:
        value = float(value)
        RDI = float(RDI) / meals
        target_str = f"{RDI:.1f} {unit}"
    except (ValueError, TypeError):
        st.warning(f"{name} value is not numeric")
        return
    
    # Target range ±15%
    lower = RDI * 0.85
    upper = RDI * 1.15

    # Color logic
    if value < RDI:
        color = "#FFA500"  # orange
    elif value > RDI:
        color = "#FF4136"  # red
    elif value > lower & value < upper:
        color = "#2ECC71" # green
    else:
        color = "#2ECC71"  # green

    # Determine max scale
    max_value = max(value, RDI)

    # Percent widths
    value_percent = min(value / max_value, 1.0) * 100
    interval_start = (lower / max_value) * 100
    interval_width = ((upper - lower) / max_value) * 100 if upper != lower else 0
    RDI_percent = min(RDI/max_value, 1.0) * 100

    bar = f"""
    <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 4px;">
            <span>{name}</span>
            <span>Actual: {value:.1f} g &nbsp;&nbsp;|&nbsp;&nbsp; Recommended: {target_str}</span>
        </div>
        <div style="position: relative; height: 14px; background-color: #eee; border-radius: 7px; overflow: hidden;">
        <div style="width: {value_percent:.1f}%; background-color: {color}; height: 100%;"></div>
            <div style="
                position: absolute;
                left: {interval_start:.1f}%;
                width: {interval_width:.1f}%;
                top: 0;
                bottom: 0;
                background-color: rgba(0, 120, 0, 0.5);
                border-radius: 6px;
                z-index: 1;">
            </div>
    </div>
    """
    st.markdown(bar, unsafe_allow_html=True)

# ----------------------------------------------------------------------------------------------------
def render_bar_micros_RDI(name, unit, value, RDI):
    try:
        value = float(value)
        RDI = float(RDI) / meals
        target_str = f"{RDI:.1f} {unit}"
    except (ValueError, TypeError):
        st.warning(f"{name} value is not numeric")
        return
    
    # Target range ±15%
    lower = RDI * 0.85
    upper = RDI * 1.15

    # Color logic
    if value < lower:
        color = "#FFA500"  # orange
    elif value > upper:
        color = "#FFA500"  # red
    else:
        color = "#2ECC71"  # green

    # Determine max scale
    max_value = max(value, upper)

    # Percent widths
    value_percent = min(value / max_value, 1.0) * 100
    interval_start = (lower / max_value) * 100
    interval_width = ((upper - lower) / max_value) * 100 if upper != lower else 0
    RDI_percent = min(RDI/max_value, 1.0) * 100

    # Render bar
    bar = f"""
    <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 4px;">
        <span>{name}</span>
        <span>Actual: {value:.1f} {unit} &nbsp;&nbsp;|&nbsp;&nbsp; Recommended: {target_str}</span>
    </div>

    <div style="position: relative; height: 14px; background-color: #eee; border-radius: 7px; overflow: hidden; margin-bottom: 12px;">
        <div style="width: {value_percent:.1f}%; background-color: {color}; height: 100%;"></div>
        <div style="
            position: absolute;
            left: {interval_start:.1f}%;
            width: {interval_width:.1f}%;
            top: 0;
            bottom: 0;
            background-color: rgba(0, 120, 0, 0.5);
            border-radius: 6px;
            z-index: 1;">
        </div>
    </div>
    """

    st.markdown(bar, unsafe_allow_html=True)

# ----------------------------------------------------------------------------------------------------
def render_bar_micros_RDI_UL(name, unit, value, RDI, UL):
    try:
        value = float(value)
        RDI = float(RDI) / meals
        UL = float(UL) / meals
    except (ValueError, TypeError):
        st.warning(f"{name} value is not numeric")
        return
    
    # Target range ±15%
    lower = RDI * 0.85
    upper = RDI * 1.15

    # Color logic
    if value < lower:
        color = "#FFA500"  # orange
    elif value > UL:
        color = "#FF4136"  # red
    elif value > upper:
        color = "#FFA500"  # orange
    else:
        color = "#2ECC71"  # green

    # Determine max scale
    max_value = max(value, upper)

    # Percent widths
    value_percent = min(value / max_value, 1.0) * 100
    interval_start = (lower / max_value) * 100
    interval_width = ((upper - lower) / max_value) * 100 if upper != lower else 0
    limit_percent = min(UL/max_value, 1.0) * 100

    # Render bar
    bar = f"""
    <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 4px;">
        <span>{name}</span>
        <span>Actual: {value:.1f} {unit} &nbsp;&nbsp;|&nbsp;&nbsp; Recommended: {RDI:.1f} {unit} &nbsp;&nbsp;|&nbsp;&nbsp; Limit: {UL:.1f} {unit}</span>
    </div>

    <div style="position: relative; height: 14px; background-color: #eee; border-radius: 7px; overflow: hidden; margin-bottom: 12px;">
        <div style="width: {value_percent:.1f}%; background-color: {color}; height: 100%;"></div>
        <div style="
            position: absolute;
            left: {interval_start:.1f}%;
            width: {interval_width:.1f}%;
            top: 0;
            bottom: 0;
            background-color: rgba(0, 120, 0, 0.5);
            border-radius: 6px;
            z-index: 1;">
        </div>
        <div style="
                position: absolute;
                left: {limit_percent:.1f}%;
                top: 0;
                bottom: 0;
                width: 5px;
                background-color: #000000;
                z-index: 2;">
        </div>

    </div>
    """

    st.markdown(bar, unsafe_allow_html=True)

# ----------------------------------------------------------------------------------------------------
def render_bar_micros_UL(name, unit, value, UL):
    try:
        value = float(value)
        UL = float(UL) / meals
    except (ValueError, TypeError):
        st.warning(f"{name} value is not numeric")
        return

    # Color logic
    if value > UL:
        color = "#FF4136"  # red
    else:
        color = "#2ECC71"  # green

    # Determine max scale
    max_value = max(value, UL)

    # Percent widths
    value_percent = min(value / max_value, 1.0) * 100
    limit_percent = min(UL/max_value, 1.0) * 100

    # Render bar
    bar = f"""
    <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 4px;">
        <span>{name}</span>
        <span>Actual: {value:.1f} {unit} &nbsp;&nbsp;|&nbsp;&nbsp; Limit: {UL:.1f} {unit}</span>
    </div>

    <div style="position: relative; height: 14px; background-color: #eee; border-radius: 7px; overflow: hidden; margin-bottom: 12px;">
        <div style="width: {value_percent:.1f}%; background-color: {color}; height: 100%;"></div>
        <div style="
                position: absolute;
                left: {limit_percent:.1f}%;
                top: 0;
                bottom: 0;
                width: 5px;
                background-color: #000000;
                z-index: 2;">
        </div>
    </div>
    """

    st.markdown(bar, unsafe_allow_html=True)

# ----------------------------------------------------------------------------------------------------
def blend_hex(c1, c2, t: float) -> str:
    """
    Linear-interpolate between two hex colours.
    c1, c2  – strings like '#RRGGBB'
    t       – 0 → return c1, 1 → return c2
    """
    c1 = c1.lstrip('#'); c2 = c2.lstrip('#')
    r1, g1, b1 = tuple(int(c1[i : i+2], 16) for i in (0, 2, 4))
    r2, g2, b2 = tuple(int(c2[i : i+2], 16) for i in (0, 2, 4))
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02X}{g:02X}{b:02X}"

# ----------------------------------------------------------------------------------------------------
def render_bar_environment(name, unit, value, threshold, multiplier, decimal, servings):
    try:
        value = float(value) * multiplier
        threshold = (float(threshold)) / servings
    except (ValueError, TypeError):
        st.warning(f"{name} value is not numeric")
        return

    # Color logic
    SAFE_COLOUR   = "#2ECC71"   # deep green
    ALERT_COLOUR  = "#FFA500"   # orange
    DANGER_COLOUR = "#FF4136"   # red

    ratio = value / threshold

    if ratio <= 1:
        color = SAFE_COLOUR
    elif ratio < 2:
        color = ALERT_COLOUR
    else:
        color = DANGER_COLOUR

    # Determine max scale
    max_value = max(value, threshold)

    # Percent widths
    value_percent = min(value / max_value, 1.0) * 100
    limit_percent = min(threshold/max_value, 1.0) * 100

    # Render bar
    bar = f"""
    <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 4px;">
        <span>{name}</span>
        <span>Actual: {value:.{decimal}f} {unit} &nbsp;&nbsp;|&nbsp;&nbsp; Threshold: {threshold:.{decimal}f} {unit}</span>
    </div>

    <div style="position: relative; height: 14px; background-color: #eee; border-radius: 7px; overflow: hidden; margin-bottom: 12px;">
        <div style="width: {value_percent:.1f}%; background-color: {color}; height: 100%;"></div>
        <div style="
                position: absolute;
                left: {limit_percent:.{decimal}f}%;
                top: 0;
                bottom: 0;
                width: 5px;
                background-color: #000000;
                z-index: 2;">
        </div>
    </div>
    """

    st.markdown(bar, unsafe_allow_html=True)

# ----------------------------------------------------------------------------------------------------
def render_bar_environment_median(name, unit, value, threshold, multiplier, decimal):
    try:
        value = float(value) * multiplier
        threshold = (float(threshold)) * multiplier
    except (ValueError, TypeError):
        st.warning(f"{name} value is not numeric")
        return

    # Color logic
    SAFE_COLOUR   = "#2ECC71"   # deep green
    ALERT_COLOUR  = "#FFA500"   # orange
    DANGER_COLOUR = "#FF4136"   # red

    ratio = value / threshold
    if ratio <= 1:
        color = SAFE_COLOUR
    elif ratio < 2:
        color = ALERT_COLOUR
    else:
        color = DANGER_COLOUR

    # Determine max scale
    max_value = max(value, threshold)

    # Percent widths
    value_percent = min(value / max_value, 1.0) * 100
    limit_percent = min(threshold/max_value, 1.0) * 100

    # Render bar
    bar = f"""
    <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 4px;">
        <span>{name}</span>
        <span>Actual: {value:.{decimal}f} {unit} &nbsp;&nbsp;|&nbsp;&nbsp; Median: {threshold:.{decimal}f} {unit}</span>
    </div>

    <div style="position: relative; height: 14px; background-color: #eee; border-radius: 7px; overflow: hidden; margin-bottom: 12px;">
        <div style="width: {value_percent:.1f}%; background-color: {color}; height: 100%;"></div>
        <div style="
                position: absolute;
                left: {limit_percent:.{decimal}f}%;
                top: 0;
                bottom: 0;
                width: 5px;
                background-color: #000000;
                z-index: 2;">
        </div>
    </div>
    """

    st.markdown(bar, unsafe_allow_html=True)

# ----------------------------------------------------------------------------------------------------
def render_bar_human_health(name, value, threshold, divider):
    try:
        value = (1 / float(value)) / divider
        threshold = float(threshold) /divider
        print(f"value: {value}, threshold: {threshold}")
    except (ValueError, TypeError):
        st.warning(f"{name} value is not numeric")
        return

    # Color logic
    SAFE_COLOUR   = "#2ECC71"   # deep green
    ALERT_COLOUR  = "#FFA500"   # orange
    DANGER_COLOUR = "#FF4136"   # red

    # Determine max scale
    value_2 = 1 / value
    threshold_2 = 1 / threshold
    max_value = max((value_2), threshold_2)

    if value_2 <= threshold_2:
        color = SAFE_COLOUR
    elif value_2 < threshold_2 * 2:
        color = ALERT_COLOUR
    else:
        color = DANGER_COLOUR

    # Percent widths
    value_percent = min(value_2 / max_value, 1.0) * 100
    limit_percent = min(threshold_2/max_value, 1.0) * 100

    # Render bar
    bar = f"""
    <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 4px;">
        <span>{name}</span>
        <span>Actual: 1 in {value:.2f} million &nbsp;&nbsp;|&nbsp;&nbsp; Median: 1 in {threshold:.2f} million</span>
    </div>

    <div style="position: relative; height: 14px; background-color: #eee; border-radius: 7px; overflow: hidden; margin-bottom: 12px;">
        <div style="width: {value_percent:.1f}%; background-color: {color}; height: 100%;"></div>
        <div style="
                position: absolute;
                left: {limit_percent:.1f}%;
                top: 0;
                bottom: 0;
                width: 5px;
                background-color: #000000;
                z-index: 2;">
        </div>
    </div>
    """
    st.markdown(bar, unsafe_allow_html=True)

# ----------------------------------------------------------------------------------------------------
def render_warning_environmental(value, description, recipe_id):
    if value == 0:
        st.success(f"✅ All ingredients were able to be backed up by {description} data!")
    else:
        missing_codes = ingredients_df[(ingredients_df['recipe_id'] == recipe_id) & (ingredients_df['Agribalyse Code'].isna())]
        missing_codes['quantity'] = missing_codes['quantity'].fillna('')
        missing_ingredients_list = (missing_codes['quantity'].str.strip() + ' ' + missing_codes['ingredient'].str.strip()).str.strip().tolist()
        formatted_list = '\n' + '\n'.join(f"- {item}" for item in missing_ingredients_list)
        st.warning(f"""🟠 {value} ingredients could not be backed up by {description} data. The {description} rating could slightly vary from the actual rating!\nMissing data on: {formatted_list}""")

# ----------------------------------------------------------------------------------------------------
def render_warning_nutritional(value, description, recipe_id):
    if value == 0:
        st.success(f"✅ All ingredients were able to be backed up by {description} data!")
    else:
        missing_codes = ingredients_df[(ingredients_df['recipe_id'] == recipe_id) & (ingredients_df['NEVO Code'].isna())]
        missing_codes['quantity'] = missing_codes['quantity'].fillna('')
        missing_ingredients_list = (missing_codes['quantity'].str.strip() + ' ' + missing_codes['ingredient'].str.strip()).str.strip().tolist()
        formatted_list = '\n' + '\n'.join(f"- {item}" for item in missing_ingredients_list)
        st.warning(f"""🟠 {value} ingredients could not be backed up by {description} data. The {description} rating regarding the **vitamins and minerals** could slightly vary from the actual rating!\nMissing data on: {formatted_list}""")

# ----------------------------------------------------------------------------------------------------
# Beginning of the UI
# ----------------------------------------------------------------------------------------------------

def recipe_tab(prompt):
    recipe_ids = get_recipe(prompt)

    recipe_ids_int = []
    for rid in recipe_ids:
        try:
            recipe_ids_int.append(int(rid))
        except ValueError:
            pass  # or log/collect invalid ones if needed
    results = []
    filtered_recipes = recipes_df[recipes_df['recipe_id'].isin(recipe_ids_int)]

    # Iterate over all recipes
    for _, recipe_row in filtered_recipes.iterrows():
        recipe_id = recipe_row['recipe_id']
        rating = float(recipe_row['Rating'])
        title = recipe_row['Title']  # Make sure 'title' matches your actual column name

        try:
            # Calculate scores
            health_contributions, environmental_contributions = calculate_score(recipe_id)
            health_score = int(round((sum(health_contributions.values()) * 100), 0))
            environment_score = int(round((sum(environmental_contributions.values()) * 100), 0))
            final_score = int(round(((health_weight / 100) * health_score + (environment_weight / 100) * environment_score), 0))

            # Append result
            results.append({
                'recipe_id': recipe_id,
                'title': title,
                'rating': rating,
                'health_score': health_score,
                'environment_score': environment_score,
                'final_score': final_score
            })

        except Exception as e:
            print("")

    # Convert to DataFrame
    df = pd.DataFrame(results)
    st.session_state.profile['other']['recipe_df'] = df

# ----------------------------------------------------------------------------------------------------
# Find Recipe Form
# ----------------------------------------------------------------------------------------------------
with st.form("find_recipe_form"):
    st.markdown(f"""
    <div style='font-size: 0.875rem; font-family: "Source Sans Pro", sans-serif; line-height: 1.6;'>
        Now, you can finally find the recipe you want! Here are some more tips to make your experience even better:<br>
        1. Just focus on the recipe without thinking too much about the health and environmental aspects; the model will take care of it. <br>
        2. You might include ingredients, a cuisine type, a meal type, diet type, and ingredients you want to exclude.<br>
        Here's an example of a query that you can use:<br>
                "Show me a recipe from the Asian cuisine, with chicken and vegetables. I am allergic to nuts and gluten; so please exclude these ingredients."
    """, unsafe_allow_html=True)

    recipe_description = st.text_input("Recipe Description")

    find_recipe_form_submit = st.form_submit_button("Find Recipe")
    if find_recipe_form_submit:
        if not recipe_description.strip():
            st.error("Please enter a recipe description")
        else:
            recipe_tab(recipe_description)

# ----------------------------------------------------------------------------------------------------
# # Grid options
# ----------------------------------------------------------------------------------------------------
recipe_df = st.session_state.profile['other']['recipe_df']
# ==== REPLACE FROM HERE (AgGrid setup + selection) ====
if recipe_df is not None and not recipe_df.empty:
    st.info("""
            The table below shows you a collection of different recipes that matched with your prompt. 
            You can click on any of them to get more details.

            The user rating represents real users' feedback, ranging from 1 star (worst) to 5 star (best).

            The other ratings show how well a recipe is performing when looking at its nutritional composition related to human health, environmental impact, and a combined score. 
            All of the ratings are calculated based on your preferences, and range from 0 (worst) to 100 (best).
            """,  icon="ℹ️")

    # --- Make data JSON-serializable to avoid BigInt issues in the JS bridge ---
    df = recipe_df.copy()
    int_like_cols = df.select_dtypes(include=["int64", "Int64", "uint64", "UInt64"]).columns.tolist()
    for c in int_like_cols:
        # Use pandas nullable ints, replace NaN with None, then cast to Python int
        df[c] = df[c].astype("Int64")
        df[c] = df[c].where(df[c].notna(), None)
        df[c] = df[c].apply(lambda v: int(v) if v is not None else None)

    # Build grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection('single', use_checkbox=False)
    gb.configure_grid_options(
        domLayout="normal",
        # Force a string row id so the grid never creates a BigInt key
        getRowId=JsCode("function(p){ return String(p.data.recipe_id ?? p.rowIndex); }"),
    )
    gb.configure_pagination(enabled=True, paginationPageSize=5)
    gb.configure_column("final_score", sort='desc')
    gb.configure_column("recipe_id", header_name="ID", width=70)
    gb.configure_column("title", header_name="Title", width=250)
    gb.configure_column("rating", header_name="User\nRating", width=80,
                        headerTooltip="Actual user ratings, from 1 (worst) to 5 (best)")
    gb.configure_column("health_score", valueFormatter="Number(value).toFixed(0)",
                        header_name="Health\nRating", width=120,
                        headerTooltip="Nutritional rating, from 0 (worst) to 100 (best)")
    gb.configure_column("environment_score", valueFormatter="Number(value).toFixed(0)",
                        header_name="Environment\nRating", width=140,
                        headerTooltip="Environmental rating, from 0 (worst) to 100 (best)")
    gb.configure_column("final_score", valueFormatter="Number(value).toFixed(0)",
                        header_name="Overall\nRating", width=120,
                        headerTooltip="Combined rating (nutritional & environmental), from 0 (worst) to 100 (best)")
    grid_options = gb.build()

    grid_response = AgGrid(
        df,  # use the cleaned df
        gridOptions=grid_options,
        theme='streamlit',
        update_on="value_changed",
        enable_enterprise_modules=False,
        fit_columns_on_grid_load=True,
        reload_data=True,
        allow_unsafe_jscode=True,
        data_return_mode="AS_INPUT",
        update_mode="SELECTION_CHANGED",
    )

    # Robust selection handling (list or DataFrame depending on st_aggrid version)
    selected_rows = grid_response.get('selected_rows')
    recipe_id = None
    if isinstance(selected_rows, list) and selected_rows:
        recipe_id = selected_rows[0].get('recipe_id')
    elif hasattr(selected_rows, "empty") and not selected_rows.empty:
        recipe_id = selected_rows['recipe_id'].values[0]

    if recipe_id is not None:
        recipe_id = int(recipe_id)
        selected_recipe = recipes_df[recipes_df['recipe_id'] == recipe_id].iloc[0]
        recipe_tab, nutrition_tab, environment_tab, calculation_tab = st.tabs(
            ['**🥘 Recipe**', '**🥗 Nutrition**', '**🌳 Environment**', '**🔢 Calculation**']
        )
# ==== REPLACE UNTIL HERE ====


# ----------------------------------------------------------------------------------------------------
# Recipe Tab
# ----------------------------------------------------------------------------------------------------
        with recipe_tab:
            image_url = selected_recipe['Image_url']
            recipe_name = selected_recipe['Title']
            serves = selected_recipe['Servings']
            difficulty = selected_recipe['Difficulty']
            prep_time = selected_recipe['Prep_time']
            cook_time = selected_recipe['Cook_time']
            recipe_url = selected_recipe['Url']
            ingredients = selected_recipe['Ingredients']
            instructions = selected_recipe['Instructions']
            rating = selected_recipe['Rating']
            rating_percentage = (rating / 5) * 100
            number_of_ratings = selected_recipe['Number_of_ratings']

# ----------------------------------------------------------------------------------------------------
            # Build HTML
            html_content = f"""
            <div style="text-align: center;">
                <h1 style="margin-bottom: 0;">{recipe_name}</h1>
                    <div style="display:inline-block; position: relative; font-size: 24px; line-height: 1;">
                    <div style="color: lightgray;">★★★★★</div>
                    <div style="position: absolute; top: 0; left: 0; overflow: hidden; width: {rating_percentage}%; color: gold;">★★★★★</div>
                        <span style="font-size: 16px; color: #555;">(Out of {number_of_ratings} ratings)</span>
                    </div>
                <p style="margin-bottom: 8px;">
                    <a href="{recipe_url}" target="_blank" style="text-decoration: none; font-size: 14px; color: #1f77b4;">
                        View full recipe on BBC Good Food
                    </a>
                </p>

                <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin: 10px 0 20px 0;">
                    <div style="border: 1px solid black; border-radius: 8px; padding: 8px 12px;">Serves {serves}</div>
                    <div style="border: 1px solid black; border-radius: 8px; padding: 8px 12px;">{difficulty}</div>
                    <div style="border: 1px solid black; border-radius: 8px; padding: 8px 12px;"><strong>Prep:</strong> {prep_time}</div>
                    <div style="border: 1px solid black; border-radius: 8px; padding: 8px 12px;"><strong>Cook:</strong> {cook_time}</div>
                </div>

                <img src="{image_url}" alt="no image found" width="400" style="border-radius: 15px;" />
            </div>
            """

            # ✅ Render with full HTML support
            components.html(html_content, height=500)
# ----------------------------------------------------------------------------------------------------

            ingredients_tab, instructions_tabs = st.columns([1, 1.5])  # image left, info right

            with ingredients_tab:

                def render_ingredients(items):
                    lines = [
                        f'<li>{item["quantity"]} {item["ingredient"]}</li>'
                        for item in items
                    ]
                    html = "<ul style='margin:0 0 0 1.2em; padding:0; line-height:1.6;'>{}</ul>".format("".join(lines))
                    st.markdown(html, unsafe_allow_html=True)

                st.markdown("### 📝 Ingredients")
                render_ingredients(ingredients)

            with instructions_tabs:
                # Flatten and sort the steps
                sorted_steps = sorted(
                    [(int(list(step.keys())[0]), list(step.values())[0]) for step in instructions],
                    key=lambda x: x[0]
                )

                # Title
                st.markdown("### 🧑‍🍳 Instructions")

                # Display steps with numbering
                for num, text in sorted_steps:
                    st.markdown(f"**Step {num}**  \n{text}")

# ----------------------------------------------------------------------------------------------------
# Nutrition Tab
# ----------------------------------------------------------------------------------------------------
        with nutrition_tab:
            with st.expander("**🔥 Calories**"):
                kcal_per_day = int(st.session_state.profile['Macros']['Calories'])
                kcal_per_meal = int(kcal_per_day / meals)
                kcal_recipe = int(selected_recipe['kcal'])
                st.markdown(f"""
                <div style='font-family: "Source Sans Pro", sans-serif; font-size: 1rem;'>
                Based on your personal information, your advised caloric intake per day is <b>{kcal_per_day} kcal</b>. \n
                And since you prefer to have {meals} meals per day, the caloric intake per meal is <b>{kcal_per_meal} kcal</b>.\n
                This recipe contains <b>{kcal_recipe} kcal</b> per serving.
                </div>
                """, unsafe_allow_html=True)

            with st.expander("🥦 **Macro-Nutrients**"):
                render_bar_macros_interval("Protein", "g", selected_recipe['protein'], macros['Protein'][0], macros['Protein'][1])
                render_bar_macros_interval("Carbohydrates", "g", selected_recipe['carbs'], macros['Carbohydrates'][0], macros['Carbohydrates'][1])
                render_bar_macros_UL("Sugar", "g", selected_recipe['sugars'], macros['Sugar'])
                render_bar_macros_interval("Fat", "g", selected_recipe['fat'], macros['Fat'][0], macros['Fat'][1])
                render_bar_macros_UL("Saturated Fat", "g", selected_recipe['saturates'], macros['Saturated Fat'])
                render_bar_macros_UL("Trans Fat", "g", selected_recipe['Trans Fat (g)'], macros['Trans Fat'])
                render_bar_macros_RDI("Fiber", "g", selected_recipe['fibre'], macros['Fiber'])

            with st.expander("🍊 **Vitamins**"):
                render_bar_micros_RDI_UL("Vitamin A", "µg", selected_recipe['Vitamin A RE (µg)'], micros['Vitamin A'], micros['Vitamin A UL'])
                render_bar_micros_RDI("Vitamin B1", "g", selected_recipe['Vitamin B1 (mg)'], micros['Vitamin B1'])
                render_bar_micros_RDI("Vitamin B2", "g", selected_recipe['Vitamin B2 (mg)'], micros['Vitamin B2'])
                render_bar_micros_RDI("Vitamin B3", "g", selected_recipe['Vitamin B3 (mg)'], micros['Vitamin B3'])
                render_bar_micros_RDI("Vitamin B6", "g", selected_recipe['Vitamin B6 (mg)'], micros['Vitamin B6'])
                render_bar_micros_RDI("Vitamin B9", "µg", selected_recipe['Vitamin B9 (µg)'], micros['Vitamin B9'])
                render_bar_micros_RDI("Vitamin B12", "µg", selected_recipe['Vitamin B12 (µg)'], micros['Vitamin B12'])
                render_bar_micros_RDI("Vitamin C", "mg", selected_recipe['Vitamin C (mg)'], micros['Vitamin C'])
                render_bar_micros_RDI_UL("Vitamin D", "µg", selected_recipe['Vitamin D (µg)'], micros['Vitamin D'], micros['Vitamin D UL'])
                render_bar_micros_RDI_UL("Vitamin E", "mg", selected_recipe['Vitamin E (mg)'], micros['Vitamin E'], micros['Vitamin E UL'])
                render_bar_micros_RDI("Vitamin K", "µg", selected_recipe['Vitamin K (µg)'], micros['Vitamin K'])

            with st.expander("🧂 **Minerals**"):
                render_bar_micros_UL("Salt", "g", selected_recipe['salt'], micros['Salt'])
                render_bar_micros_RDI_UL("Calcium", "mg", selected_recipe['Calcium (mg)'], micros['Calcium'], micros['Calcium UL'])
                render_bar_micros_RDI_UL("Iodine", "mg", selected_recipe['Iodine (µg)'], micros['Iodine'], micros['Iodine UL'])
                render_bar_micros_RDI_UL("Iron", "mg", selected_recipe['Iron (mg)'], micros['Iron'], micros['Iron UL'])
                render_bar_micros_RDI("Magnesium", 'mg', selected_recipe['Magnesium (mg)'], micros['Magnesium'])
                render_bar_micros_RDI_UL("Selenium", "µg", selected_recipe['Selenium (µg)'], micros['Selenium'], micros['Selenium UL'])
                render_bar_micros_RDI_UL("Zinc", "mg", selected_recipe['Zinc (mg)'], micros['Zinc'], micros['Zinc UL'])
            st.markdown("---")
            render_warning_nutritional(selected_recipe['number_of_ingredients'] - selected_recipe['number_of_nevo_codes'], "nutritional", recipe_id)
# ----------------------------------------------------------------------------------------------------
# Environment Tab
# ----------------------------------------------------------------------------------------------------
        with environment_tab:
            with st.expander("**🟢 Categories with safe thresholds**"):
                servings = int(selected_recipe['Servings'])
                render_bar_environment("Acification", "mol H+", selected_recipe['Total - mol H+ eq'], environment['Acidification'], 1, 3, servings)
                render_bar_environment("Climate Change", "kg CO₂", selected_recipe['Total - Co2 eq'], environment['Climate Change'], 1, 2, servings)
                render_bar_environment("Energy Use", "MJ", selected_recipe['Total - MJ'], environment['Energy Use'], 1, 1, servings)
                render_bar_environment("Freshwater Eutrophication", "g Phospherus", selected_recipe['Total - P eq'], environment['Freshwater Eutrophication'], 1000, 1, servings)
                render_bar_environment("Marine Eutrophication", "g Nitrogen", selected_recipe['Total - N eq'], environment['Marine Eutrophication'], 1000, 2, servings)
                render_bar_environment("Ozone Layer Depletion", "µg CFC-11", selected_recipe['Total - CFC11 eq'], environment['Ozone Layer Depletion'], 1000000000, 2, servings)
                render_bar_environment("Water Use", "m³", selected_recipe['Total - m3'], environment['Water Use'], 1, 2, servings)
            
            with st.expander("**📊 Categories compared with median values**"):
                render_bar_environment_median("Land Use", "", selected_recipe['Total - pt dimensionless'], environment['Land Use'], 1, 1)
                render_bar_human_health("Particulate Matter", selected_recipe['Total - disease inc.'], environment['Particulate Matter'], 1000000)
                render_bar_human_health("Toxicological Effects", selected_recipe['Total - NC CTUh'], environment['Toxicological Effects'], 1000000)
                render_bar_human_health("Toxicological Effects (carcinogenic)", selected_recipe['Total - C CTUh'], environment['Toxicological Effects (carcinogenic)'], 1000000)               

            st.markdown("---")
            render_warning_environmental(selected_recipe['number_of_ingredients'] - selected_recipe['number_of_agribalyse_codes'], "environmental", recipe_id)

# ----------------------------------------------------------------------------------------------------
# Calculation Tab
# ----------------------------------------------------------------------------------------------------
        with calculation_tab:
            # Overall and individual ratings
            health_contributions, environmental_contributions = calculate_score(recipe_id)
            health_score = int(round((sum(health_contributions.values()) * 100), 0))
            environment_score = int(round((sum(environmental_contributions.values()) * 100), 0))
            final_score = int(round(((health_weight / 100) * health_score + (environment_weight / 100) * environment_score), 0))
            # st.write(f"""The overall rating is calculated as follows:<br>
            #          Overall Rating = (Health Score x Health Weight) + (Environment Score x Environment Weight)<br>
            #          Overall Rating = ({health_score} x {int(health_weight)}%) + ({environment_score} x {int(environment_weight)}%) = {final_score} %""", unsafe_allow_html=True)
            # st.write("Below you can find an overview of the different contributions of each metric.")
            st.markdown(f"""
            <div style="font-family: 'Source Sans Pro', sans-serif; font-size: 1rem; line-height: 1.6;">

            ### 📊 Overall Rating Calculation

            The overall rating is calculated by combining the health and environment score with your preferences:

            **Formula:**
            <div style="margin-left: 1em;">
                <code>Overall Rating = (Health Score × Health Weight) + (Environment Score × Environment Weight)</code>
            </div>

            **Substitution:**
            <div style="margin-left: 1em;">
                <code>Overall Rating = ({health_score} × {int(health_weight)}%) + ({environment_score} × {int(environment_weight)}%)</code>
            </div><br>

            **Final Result:**
            <div style="margin-left: 1em; font-size: 1.1rem;">
                <strong>Overall Rating = {final_score}</strong>
            </div>

            </div>
            """, unsafe_allow_html=True)

            st.markdown("___")
            st.markdown("### 📋 Metric-by-Metric Contribution Overview")

            st.write("---")
            col1, col2 = st.columns([5,5])
            # Health Contributions
            with col1:
                st.subheader("Health-Contributions")

                # Scale, round, and format scores
                health_scores = {k: f"{round(v * 100, 2):.2f}" for k, v in health_contributions.items()}
                total_health_score = f"{round(sum([float(v) for v in health_scores.values()]), 2):.2f}"

                # Create sorted DataFrame
                health_contributions_df = pd.DataFrame({
                    'Metric': list(health_scores.keys()),
                    'Score': list(health_scores.values())
                })
                health_contributions_df = health_contributions_df.sort_values(by="Score", ascending=False, ignore_index=True)
                health_contributions_df.loc[len(health_contributions_df)] = ['Total Score', total_health_score]

                # Display full table
                st.table(health_contributions_df)

            # Environmental Contributions
            with col2:
                st.subheader("Environment-Contributions")

                # Scale, round, and format scores
                environmental_scores = {k: f"{round(v * 100, 2):.2f}" for k, v in environmental_contributions.items()}
                total_environmental_score = f"{round(sum([float(v) for v in environmental_scores.values()]), 2):.2f}"

                # Create sorted DataFrame
                environmental_contributions_df = pd.DataFrame({
                    'Metric': list(environmental_scores.keys()),
                    'Score': list(environmental_scores.values())
                })
                environmental_contributions_df = environmental_contributions_df.sort_values(by="Score", ascending=False, ignore_index=True)
                environmental_contributions_df.loc[len(environmental_contributions_df)] = ['Total Score', total_environmental_score]

                # Display full table
                st.table(environmental_contributions_df)

# ----------------------------------------------------------------------------------------------------
elif st.session_state.profile['other']['recipe_df'] is None:
    st.write("")
else:
    st.warning("Unfortunately, no recipes were found that fitted the recipe description. Please try again by altering the prompt. You could extend the description with more information, or try to search for another recipe.")
