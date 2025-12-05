import sys
import os
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

def renumber_criteria(categories):
    """Reset criterion labels within categories to placeholder names that encourage customization."""
    # Placeholder names that don't imply sequence
    criterion_placeholders = ["New Criterion", "Custom Criterion", "Assessment Item", "Evaluation Point", "Quality Measure"]
    
    for cat in categories:
        criteria = cat.get('criteria', [])
        for j, crit in enumerate(criteria):
            # Cycle through placeholder names
            placeholder = criterion_placeholders[j % len(criterion_placeholders)]
            crit['label'] = placeholder

st.set_page_config(
    page_title="📋 View & Edit Rubric - AI Video Analyzer",
    page_icon="📋",
    layout="wide"
)

st.title("📋 View & Edit Rubric")
st.markdown("View rubric details or edit existing evaluation rubrics.")

available_rubrics = list_available_rubrics()

if not available_rubrics:
    st.warning("No rubrics available to view or edit.")
else:
    # Add empty option for no selection
    edit_options = [""] + [r['filename'] for r in available_rubrics]
    
    # Determine default index for selectbox
    default_index = 0
    if 'auto_select_rubric' in st.session_state:
        # Auto-select the specified rubric
        rubric_name = st.session_state['auto_select_rubric']
        available_filenames = [r['filename'] for r in available_rubrics]
        if rubric_name in available_filenames:
            default_index = available_filenames.index(rubric_name) + 1  # +1 because of empty option
        else:
            # Clear invalid auto-select state
            del st.session_state['auto_select_rubric']
    
    rubric_name = st.selectbox(
        "Select rubric to view or edit",
        options=edit_options,
        index=default_index,
        key="view_edit_rubric_select"
    )

    if rubric_name:
        # Load the rubric data
        rubric_data, error = load_rubric_from_file(rubric_name)
        if error:
            st.error(f"Error loading rubric: {error}")
        elif rubric_data is None:
            st.error(f"Rubric '{rubric_name}' not found.")
        else:
            # Check if it's a new format rubric
            is_new_format = "categories" in rubric_data
            if not is_new_format:
                st.warning("⚠️ This rubric uses the legacy format (flat criteria). The edit form supports the new hierarchical format. You can still edit basic info and thresholds.")

            # Calculate summary statistics for both View and Edit tabs
            if 'categories' in rubric_data:
                total_categories = len(rubric_data['categories'])
                total_criteria = sum(len(cat['criteria']) for cat in rubric_data['categories'])
                total_points = sum(cat['max_points'] for cat in rubric_data['categories'])
                total_weight = sum(cat.get('weight', 0) for cat in rubric_data['categories'])
            else:
                total_categories = total_criteria = total_points = total_weight = 0

            # Add tabs for View and Edit modes
            tab1, tab2 = st.tabs(["👁️ View", "✏️ Edit"])
            
            with tab1:
                # View Mode - Display rubric details                
                st.markdown(rubric_data.get('description', 'No description'))
                st.markdown(f'<p style="color:#0068c9; font-size:42px; font-weight:600;">{rubric_data.get("name", rubric_name)}</p>', unsafe_allow_html=True)

                # Three-column row: Version, Pass Threshold, Resubmit Threshold
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Version", rubric_data.get('version', 'N/A'))
                with col2:
                    thresholds = rubric_data.get('thresholds', {})
                    max_score = rubric_data.get('scale', {}).get('max', 10)
                    pass_threshold_pct = (thresholds.get('pass', 7) / max_score * 100) if max_score > 0 else 0
                    st.metric("Pass Threshold", f"≥{pass_threshold_pct:.0f}%")
                with col3:
                    thresholds = rubric_data.get('thresholds', {})
                    max_score = rubric_data.get('scale', {}).get('max', 10)
                    resubmit_threshold_pct = (thresholds.get('revise', 5) / max_score * 100) if max_score > 0 else 0
                    st.metric("Resubmit Threshold", f"≥{resubmit_threshold_pct:.0f}%")
                    st.caption("Minimum score to allow video resubmission")

                # Show structure info
                if 'categories' in rubric_data:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Categories", total_categories)
                    with col2:
                        st.metric("Total Criteria", total_criteria)
                    with col3:
                        st.metric("Total Points", total_points)

                    st.markdown("#### 📂 Categories & Criteria")
                    for cat in rubric_data['categories']:
                        with st.expander(f"📁 {cat['label']} ({cat['max_points']} points)", expanded=False):
                            st.write(f"**ID:** {cat['category_id']}")
                            st.write(f"**Weight:** {cat.get('weight', 0):.1f}")
                            st.write("**Criteria:**")
                            for criterion in cat['criteria']:
                                st.write(f"  • {criterion['label']} ({criterion['max_points']} points)")
                                if criterion.get('desc'):
                                    st.caption(criterion['desc'])

                elif 'criteria' in rubric_data:
                    st.metric("Criteria", len(rubric_data['criteria']))
                    st.markdown("### Criteria (Legacy Format)")
                    for criterion in rubric_data['criteria']:
                        st.write(f"• **{criterion['label']}** (Weight: {criterion['weight']:.1f})")
                        if criterion.get('desc'):
                            st.caption(criterion['desc'])

                # st.markdown("---")
                st.subheader("📄 Rubric as Code")

                # Show full JSON
                with st.expander("📄 View Full JSON"):
                    st.json(rubric_data)
            
            with tab2:
                # Edit Mode - Redesigned for better UX
                # st.subheader("✏️ Edit Rubric")

                # Initialize session state for undo functionality
                if 'rubric_backup' not in st.session_state:
                    st.session_state['rubric_backup'] = None
                if 'last_action' not in st.session_state:
                    st.session_state['last_action'] = None

                # Main editing form with tabs (Recommendations #2, #3, #4)
                with st.form(f"edit_rubric_form_{rubric_name}"):
                    # Form tabs for progressive disclosure
                    form_tab1, form_tab2, form_tab3 = st.tabs(["📝 Basic Info", "🎯 Scoring Thresholds", "📂 Categories & Criteria"])

                    with form_tab1:
                        col1, col2 = st.columns(2)
                        with col1:
                            name = st.text_input("Rubric Name", value=rubric_data.get('name', ''),
                                               help="Display name for the rubric")
                            version = st.text_input("Version", value=rubric_data.get('version', '1.0'),
                                                  help="Current version (auto-incremented when saved)", disabled=True)
                        with col2:
                            rubric_id = st.text_input("Rubric ID", value=rubric_data.get('rubric_id', ''),
                                                    help="Unique identifier (read-only)", disabled=True)
                            # Calculate max score from criteria
                            calculated_max_score = sum(crit.get('max_points', 0) for cat in rubric_data.get('categories', []) for crit in cat.get('criteria', []))
                            st.number_input("Maximum Score (Calculated)", min_value=0, value=calculated_max_score,
                                          disabled=True, help="Automatically calculated from all criteria points", key="edit_max_score_display")

                        description = st.text_area("Description", value=rubric_data.get('description', ''),
                                                 help="Brief description of what this rubric evaluates", height=100)

                    with form_tab2:
                        st.info("Set the percentage thresholds for pass/fail decisions.")

                        current_max_score = rubric_data.get('scale', {}).get('max', 50)
                        col1, col2 = st.columns(2)
                        with col1:
                            current_pass_abs = rubric_data.get('thresholds', {}).get('pass', 35)
                            current_pass_pct = (current_pass_abs / current_max_score * 100) if current_max_score > 0 else 70
                            pass_threshold_pct = st.number_input("Pass Threshold (%)", min_value=0, max_value=100, step=1,
                                                               value=int(current_pass_pct),
                                                               help="Percentage score required to pass")
                        with col2:
                            current_revise_abs = rubric_data.get('thresholds', {}).get('revise', 25)
                            current_revise_pct = (current_revise_abs / current_max_score * 100) if current_max_score > 0 else 50
                            revise_threshold_pct = st.number_input("Resubmit Threshold (%)", min_value=0, max_value=100, step=1,
                                                                 value=int(current_revise_pct),
                                                                 help="Minimum score to allow video resubmission")

                    with form_tab3:
                        if is_new_format:
                            st.info("Edit the content and details of existing categories and criteria.")

                            categories = rubric_data.get('categories', [])
                            if categories:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Categories", total_categories)
                                    st.caption(f"Total weight: {total_weight:.3f} (should be 1.0)")
                                with col2:
                                    st.metric("Total Criteria", total_criteria)
                                with col3:
                                    st.metric("Total Points", total_points)

                                for i, cat in enumerate(categories):
                                    with st.expander(f"📁 {cat.get('label', f'Category {i+1}')} (Weight: {cat.get('weight', 0):.3f})", expanded=False):
                                        col1, col2, col3 = st.columns([2, 1, 1])
                                        with col1:
                                            cat['label'] = st.text_input("Category Label", value=cat.get('label', ''),
                                                                       key=f"edit_cat_label_{i}")
                                            cat['category_id'] = st.text_input(f"Category ID", value=cat.get('category_id', ''),
                                                                             key=f"edit_cat_id_{i}")
                                        with col2:
                                            cat['weight'] = st.number_input(f"Weight", min_value=0.0, max_value=1.0, step=0.01,
                                                                          value=cat.get('weight', 0.0), key=f"edit_cat_weight_{i}")
                                        with col3:
                                            cat['max_points'] = st.number_input(f"Max Points", min_value=1,
                                                                              value=cat.get('max_points', 10), key=f"edit_cat_points_{i}")

                                        # Criteria editing
                                        criteria = cat.get('criteria', [])
                                        st.markdown(f"**Criteria for {cat.get('label', f'Category {i+1}')}**")

                                        for j, criterion in enumerate(criteria):
                                            st.markdown(f"**Criterion {j+1:02d}:**")
                                            col1, col2 = st.columns([2, 1])
                                            with col1:
                                                criterion['label'] = st.text_input(f"Label", value=criterion.get('label', ''),
                                                                                 key=f"edit_crit_label_{i}_{j}")
                                                criterion['criterion_id'] = st.text_input(f"ID", value=criterion.get('criterion_id', ''),
                                                                                        key=f"edit_crit_id_{i}_{j}")
                                            with col2:
                                                criterion['max_points'] = st.number_input(f"Points", min_value=1,
                                                                                        value=criterion.get('max_points', 5),
                                                                                        key=f"edit_crit_points_{i}_{j}")

                                            criterion['desc'] = st.text_area(f"Description", value=criterion.get('desc', ''),
                                                                           key=f"edit_crit_desc_{i}_{j}", height=80)
                                            st.divider()
                            else:
                                st.info("No categories found. Add Categories and Criteria with the button below.")
                        else:
                            st.warning("⚠️ Legacy format rubric - only basic info and thresholds can be edited. Convert to new format for full editing capabilities.")

                    # Submit button (Recommendation #5 - unified action)
                    submitted = st.form_submit_button("💾 Save All Changes", use_container_width=True, type="primary")

                    if submitted:
                        # Update the rubric data
                        rubric_data['name'] = str(name).strip()
                        rubric_data['description'] = str(description).strip()
                        rubric_data['rubric_id'] = str(rubric_id).strip()
                        rubric_data['version'] = str(version).strip()

                        # Calculate max score from criteria
                        calculated_max_score = sum(crit.get('max_points', 0) for cat in rubric_data.get('categories', []) for crit in cat.get('criteria', []))
                        rubric_data['scale']['max'] = calculated_max_score

                        # Convert percentage thresholds to absolute values
                        pass_threshold = int((pass_threshold_pct / 100.0) * calculated_max_score)
                        revise_threshold = int((revise_threshold_pct / 100.0) * calculated_max_score)
                        rubric_data['thresholds']['pass'] = pass_threshold
                        rubric_data['thresholds']['revise'] = revise_threshold

                        # Validate the updated rubric
                        is_valid = validate_and_display(rubric_data, name, mode="inline")
                        if is_valid:
                            # Auto-increment version for new-format rubrics
                            if is_new_format:
                                current_version = rubric_data.get('version', '1.0')
                                new_version = increment_version(current_version)
                                rubric_data['version'] = new_version
                                st.info(f"📈 Version incremented: {current_version} → {new_version}")

                            # Save the rubric
                            success, error = save_rubric_to_file(rubric_data, rubric_name)
                            if success:
                                st.success(f"✅ Rubric '{name}' updated successfully!")
                                st.balloons()
                                # Clear undo state after successful save
                                st.session_state['rubric_backup'] = None
                                st.session_state['last_action'] = None
                                st.rerun()
                            else:
                                st.error(f"❌ Error saving rubric: {error}")

                # Consolidated Structure Management (Recommendation #1) - Moved below form for better workflow
                if is_new_format:
                    with st.expander("🏗️ Add Categories & Criteria", expanded=False):
                        st.markdown("**Add/Remove Categories and Criteria**")
                        st.info("Changes here are applied immediately. Use 'Undo Last Change' if needed.")

                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col1:
                            if st.button("➕ Add Category", use_container_width=True, help="Add a new evaluation category"):
                                # Create backup for undo
                                st.session_state['rubric_backup'] = json.loads(json.dumps(rubric_data))
                                st.session_state['last_action'] = 'add_category'

                                categories = rubric_data.get('categories', [])
                                # Use varied placeholder names to encourage customization
                                category_placeholders = ["New Category", "Custom Category", "Evaluation Area", "Assessment Category"]
                                placeholder = category_placeholders[len(categories) % len(category_placeholders)]
                                categories.append({
                                    'category_id': f'category_{len(categories)+1}',
                                    'label': placeholder,
                                    'weight': 0.0,
                                    'max_points': 10,
                                    'criteria': [{
                                        'criterion_id': 'criterion_1',
                                        'label': 'New Criterion',
                                        'desc': '',
                                        'max_points': 5
                                    }]
                                })
                                rubric_data['categories'] = categories
                                st.success("✅ Category added!")
                                st.rerun()

                        with col2:
                            if st.button("🔄 Reset Labels", use_container_width=True, help="Reset criterion labels to varied placeholder names that encourage customization"):
                                st.session_state['rubric_backup'] = json.loads(json.dumps(rubric_data))
                                st.session_state['last_action'] = 'reset_labels'

                                categories = rubric_data.get('categories', [])
                                renumber_criteria(categories)
                                rubric_data['categories'] = categories
                                st.success("✅ Labels reset successfully!")
                                st.rerun()

                        with col3:
                            if st.button("↶ Undo Last Change", use_container_width=True,
                                       disabled=st.session_state['rubric_backup'] is None,
                                       help="Undo the last structural change"):
                                if st.session_state['rubric_backup'] is not None:
                                    rubric_data.clear()
                                    rubric_data.update(st.session_state['rubric_backup'])
                                    action = st.session_state['last_action']
                                    st.success(f"✅ Undid: {action.replace('_', ' ').title()}")
                                    st.session_state['rubric_backup'] = None
                                    st.session_state['last_action'] = None
                                    st.rerun()
                                else:
                                    st.warning("No action to undo")

                        # Category-specific management
                        categories = rubric_data.get('categories', [])
                        if categories:
                            st.markdown("---")
                            st.markdown("**Category Management:**")

                            for i, cat in enumerate(categories):
                                with st.expander(f"📁 {cat.get('label', f'Category {i+1}')} ({len(cat.get('criteria', []))} criteria)", expanded=False):
                                    col1, col2, col3 = st.columns([1, 1, 1])

                                    with col1:
                                        if st.button(f"➕ Add Criterion", key=f"add_crit_{i}",
                                                   help=f"Add criterion to {cat.get('label', f'Category {i+1}')}"):
                                            st.session_state['rubric_backup'] = json.loads(json.dumps(rubric_data))
                                            st.session_state['last_action'] = f'add_criterion_to_{cat.get("label", f"category_{i+1}")}'

                                            criteria = cat.get('criteria', [])
                                            # Use varied placeholder names to encourage customization
                                            criterion_placeholders = ["New Criterion", "Custom Criterion", "Assessment Item", "Evaluation Point", "Quality Measure"]
                                            placeholder = criterion_placeholders[len(criteria) % len(criterion_placeholders)]
                                            criteria.append({
                                                'criterion_id': f'criterion_{len(criteria)+1}',
                                                'label': placeholder,
                                                'desc': '',
                                                'max_points': 5
                                            })
                                            rubric_data['categories'] = categories
                                            st.success("✅ Criterion added!")
                                            st.rerun()

                                    with col2:
                                        if len(cat.get('criteria', [])) > 1:
                                            if st.button(f"🗑️ Remove Category", key=f"remove_cat_{i}",
                                                       help=f"Remove {cat.get('label', f'Category {i+1}')} and all its criteria"):
                                                st.session_state['rubric_backup'] = json.loads(json.dumps(rubric_data))
                                                st.session_state['last_action'] = f'remove_category_{cat.get("label", f"category_{i+1}")}'

                                                categories.pop(i)
                                                rubric_data['categories'] = categories
                                                st.success("✅ Category removed!")
                                                st.rerun()

                                    with col3:
                                        criteria = cat.get('criteria', [])
                                        if criteria:
                                            # Show remove criterion buttons
                                            st.markdown("Remove criteria:")
                                            crit_cols = st.columns(min(len(criteria), 3))
                                            for j, criterion in enumerate(criteria):
                                                col_idx = j % 3
                                                with crit_cols[col_idx]:
                                                    if st.button(f"🗑️ {criterion.get('label', f'C{j+1}')}",
                                                               key=f"remove_crit_{i}_{j}",
                                                               help=f"Remove {criterion.get('label', f'Criterion {j+1}')}"):
                                                        st.session_state['rubric_backup'] = json.loads(json.dumps(rubric_data))
                                                        st.session_state['last_action'] = f'remove_criterion_{criterion.get("label", f"criterion_{j+1}")}'

                                                        criteria.pop(j)
                                                        rubric_data['categories'] = categories
                                                        renumber_criteria(categories)
                                                        st.success("✅ Criterion removed!")
                                                        st.rerun()

            # Rubric Actions - Grouped together above delete warning
            st.markdown("### 🛠️ Rubric Actions")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Create Backup", use_container_width=True, help="Create a timestamped backup of this rubric without changing its version"):
                    with st.spinner("Creating backup..."):
                        # Create backup by saving the current rubric (this will create a timestamped backup automatically)
                        success, error = save_rubric_to_file(rubric_data, rubric_name, create_backup=True)
                        if success:
                            st.session_state['backup_result'] = {'success': True, 'message': "✅ Backup created successfully!", 'info': "The backup has been saved to the versions directory with a timestamp."}
                        else:
                            st.session_state['backup_result'] = {'success': False, 'message': f"❌ Error creating backup: {error}"}
                        st.rerun()
            with col2:
                if st.button("🗑️ Delete This Rubric", use_container_width=True, help="Permanently delete this rubric"):
                    st.session_state['confirm_delete'] = True
                    st.rerun()
            with col3:
                if st.button("📚 Manage Versions", use_container_width=True, help="View and manage rubric versions"):
                    if 'view_edit_rubric_select' in st.session_state and st.session_state['view_edit_rubric_select']:
                        st.session_state['auto_select_rubric'] = st.session_state['view_edit_rubric_select']
                    st.switch_page("pages/7_Manage_Rubrics.py")

            # Display backup result outside column structure
            if 'backup_result' in st.session_state:
                result = st.session_state['backup_result']
                if result['success']:
                    st.success(result['message'])
                    st.info(result['info'])
                else:
                    st.error(result['message'])
                del st.session_state['backup_result']

    # Delete rubric functionality
    if rubric_name:
        if 'confirm_delete' not in st.session_state:
            st.session_state['confirm_delete'] = False

        if st.session_state['confirm_delete']:
            st.warning("⚠️ Deleting a rubric is permanent and cannot be undone. The current rubric will be removed, but archived versions will be preserved.")
            st.error("Are you sure you want to delete this rubric? Archived versions will be preserved.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete Permanently", key="confirm_delete_btn"):
                    # Delete the file
                    rubrics_dir = get_rubrics_dir()
                    file_path = rubrics_dir / f"{rubric_name}.json"
                    try:
                        if file_path.exists():
                            file_path.unlink()
                            st.success(f"✅ Rubric '{rubric_name}' has been deleted. Archived versions are preserved.")
                        else:
                            st.error(f"❌ File {file_path} not found.")
                    except Exception as e:
                        st.error(f"❌ Error deleting file: {e}")

                    st.session_state['confirm_delete'] = False
                    st.rerun()
            with col2:
                if st.button("Cancel", key="cancel_delete_btn"):
                    st.session_state['confirm_delete'] = False
                    st.rerun()

# Remove the old navigation section since Manage Versions is now in the actions section
# Navigation
# st.markdown("---")
# st.markdown("### 📚 Rubric Management")
# if st.button("📚 Manage Versions", use_container_width=True):
#     if 'view_edit_rubric_select' in st.session_state and st.session_state['view_edit_rubric_select']:
#         st.session_state['auto_select_rubric'] = st.session_state['view_edit_rubric_select']
#     st.switch_page("pages/7_Manage_Rubrics.py")