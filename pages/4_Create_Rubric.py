import sys
import os
import secrets
import string
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from pathlib import Path
import json
from rubric_helper import (
    list_available_rubrics, load_rubric_from_file, validate_rubric,
    list_rubric_versions, restore_rubric_version, show_rubric_details,
    save_rubric_to_file, increment_version, get_rubrics_dir
)
from validation_ui import validate_and_display

def generate_random_id(length=4):
    """Generate a random alphanumeric string of specified length."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_rubric_id(name):
    """Generate the rubric ID from the name."""
    if not name:
        return ''
    base_id = name.lower().replace(' ', '-').replace('_', '-')
    base_id = ''.join(c for c in base_id if c.isalnum() or c == '-')
    while '--' in base_id:
        base_id = base_id.replace('--', '-')
    base_id = base_id.strip('-')

    # Ensure uniqueness
    rubric_id = base_id
    existing_ids = [r['filename'].replace('-rubric', '').replace('.json', '') for r in list_available_rubrics()]
    counter = 1
    while rubric_id in existing_ids:
        rubric_id = f"{base_id}-{counter}"
        counter += 1

    return rubric_id

st.set_page_config(
    page_title="➕ Create Rubric - AI Video Analyzer",
    page_icon="➕",
    layout="wide"
)

st.title("➕ Create New Rubric")
st.markdown("Create a new evaluation rubric with categories and criteria.")

# Get available rubrics for uniqueness check
available_rubrics = list_available_rubrics()
existing_rubric_names = set()
for r in available_rubrics:
    data, _ = load_rubric_from_file(r['filename'])
    if data and 'name' in data:
        existing_rubric_names.add(data['name'].strip())

# Initialize session state for rubric creation
if 'create_rubric_data' not in st.session_state:
    st.session_state.create_rubric_data = {
        'name': '',
        'description': '',
        'pass_threshold_pct': 70,  # Integer percentage
        'revise_threshold_pct': 55,  # Integer percentage
        'categories': []
    }

with st.form("create_rubric_form"):
    st.markdown("#### 📝 Basic Information")
    name = st.text_input("Rubric Name", value='', help="Display name for the rubric")

    description = st.text_area("Description", value='',
                             help="Brief description of what this rubric evaluates")

    st.markdown("#### 🎯 Scoring Thresholds")
    col1, col2 = st.columns(2)
    with col1:
        pass_threshold_pct = st.number_input("Pass Threshold (%)", min_value=0, max_value=100, step=1,
                                           value=70,
                                           help="Minimum percentage score to pass (integer 0-100%)")
    with col2:
        revise_threshold_pct = st.number_input("Revise Threshold (%)", min_value=0, max_value=100, step=1,
                                             value=55,
                                             help="Minimum percentage score to allow revision (integer 0-100%). Resubmissions should not be allowed by submitters scoring below this threshold.")


    # Submit button
    submitted = st.form_submit_button("🚀 Create Rubric", use_container_width=True, type="primary")

    if submitted:
        # Generate rubric ID
        rubric_id = generate_rubric_id(name.strip())

        # Auto-add default categories
        categories = []
        # Category 1
        cat1_random = generate_random_id()
        category1_id = f"{rubric_id}_cat-{cat1_random}"
        crit1_random = generate_random_id()
        criterion1_id = f"{rubric_id}_{category1_id}_crit-{crit1_random}"
        crit2_random = generate_random_id()
        criterion2_id = f"{rubric_id}_{category1_id}_crit-{crit2_random}"
        categories.append({
            'category_id': category1_id,
            'label': 'Category 01',
            'weight': 0.5,
            'max_points': 10,
            'criteria': [{
                'criterion_id': criterion1_id,
                'label': 'Criterion 01',
                'desc': '',
                'max_points': 5
            }, {
                'criterion_id': criterion2_id,
                'label': 'Criterion 02',
                'desc': '',
                'max_points': 5
            }]
        })
        # Category 2
        cat2_random = generate_random_id()
        category2_id = f"{rubric_id}_cat-{cat2_random}"
        crit3_random = generate_random_id()
        criterion3_id = f"{rubric_id}_{category2_id}_crit-{crit3_random}"
        crit4_random = generate_random_id()
        criterion4_id = f"{rubric_id}_{category2_id}_crit-{crit4_random}"
        categories.append({
            'category_id': category2_id,
            'label': 'Category 02',
            'weight': 0.5,
            'max_points': 10,
            'criteria': [{
                'criterion_id': criterion3_id,
                'label': 'Criterion 01',
                'desc': '',
                'max_points': 5
            }, {
                'criterion_id': criterion4_id,
                'label': 'Criterion 02',
                'desc': '',
                'max_points': 5
            }]
        })

        # Validate form data
        errors = []

        if not name.strip():
            errors.append("Rubric name is required")

        # Check if name already exists
        if name.strip() in existing_rubric_names:
            errors.append("A rubric with this name already exists. Please choose a different name.")

        if not rubric_id:
            errors.append("Rubric ID could not be generated")

        # Validate categories
        total_weight = sum(cat.get('weight', 0) for cat in categories)
        if not (0.99 <= total_weight <= 1.01):
            errors.append(f"Category weights must sum to 1.0 (current: {total_weight:.3f})")

        # Check category and criterion IDs are unique
        all_cat_ids = [cat.get('category_id', '') for cat in categories]
        if len(all_cat_ids) != len(set(all_cat_ids)):
            errors.append("Category IDs must be unique")

        all_crit_ids = []
        for cat in categories:
            for crit in cat.get('criteria', []):
                all_crit_ids.append(crit.get('criterion_id', ''))
        if len(all_crit_ids) != len(set(all_crit_ids)):
            errors.append("Criterion IDs must be unique across all categories")

        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            # Calculate maximum score from criteria
            calculated_max_score = sum(crit.get('max_points', 0) for cat in categories for crit in cat.get('criteria', []))

            # Convert percentage thresholds to absolute values
            pass_threshold = int((pass_threshold_pct / 100.0) * calculated_max_score)
            revise_threshold = int((revise_threshold_pct / 100.0) * calculated_max_score)

            # Create the rubric
            rubric = {
                'rubric_id': rubric_id,
                'version': '1.0',
                'status': 'current',
                'name': name.strip(),
                'description': description.strip(),
                'categories': categories,
                'scale': {
                    'min': 0,
                    'max': calculated_max_score
                },
                'overall_method': 'total_points',
                'thresholds': {
                    'pass': pass_threshold,
                    'revise': revise_threshold
                }
            }

            # Validate the rubric
            is_valid = validate_and_display(rubric, name.strip(), mode="inline")
            if is_valid:
                # Save the rubric
                filename = rubric_id
                success, error = save_rubric_to_file(rubric, filename)
                if success:
                    # Store success info in session state for auto-selection
                    st.session_state['auto_select_rubric'] = filename
                    # No rerun here, let the success display outside the form
                else:
                    st.error(f"❌ Error saving rubric: {error}")

# Handle creation success outside the form
if 'auto_select_rubric' in st.session_state:
    rubric_name = st.session_state['auto_select_rubric']
    # Try to get the rubric data to show the name
    rubric_data, error = load_rubric_from_file(rubric_name)
    if rubric_data:
        display_name = rubric_data.get('name', rubric_name)
        st.success(f"✅ Rubric '{display_name}' created successfully!")
        st.info("Use the buttons below to view, edit, or manage it.")
        st.balloons()
    else:
        # Rubric doesn't exist, clear the session state
        del st.session_state['auto_select_rubric']

# Navigation
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📋 View/Edit Rubrics", use_container_width=True):
        # Keep auto_select_rubric for auto-selection in target page
        st.switch_page("pages/3_View_or_Edit_Rubric.py")
with col2:
    if st.button("📥 Import Rubric", use_container_width=True):
        st.switch_page("pages/5_Import_Rubric.py")
with col3:
    if st.button("📚 Manage Versions", use_container_width=True):
        # Keep auto_select_rubric for auto-selection in target page
        st.switch_page("pages/7_Manage_Rubrics.py")