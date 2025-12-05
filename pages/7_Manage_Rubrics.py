import sys
import os
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from rubric_helper import (
    list_available_rubrics, list_rubric_versions, restore_rubric_version, get_rubrics_dir
)

st.set_page_config(
    page_title="📊 Rubric Dashboard - AI Video Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Rubric Dashboard")
st.markdown("View rubric overview, manage versions, and restore previous states.")

# Load available rubrics
available_rubrics = list_available_rubrics()

# Overview metrics
col1, col2, col3 = st.columns(3)
sample_rubrics = [r for r in available_rubrics if r['filename'].startswith('sample')]
with col1:
    customized_rubrics = len(available_rubrics) - len(sample_rubrics)
    st.metric("Customized Rubrics", customized_rubrics)
    
with col2:
    st.metric("Sample Rubrics", len(sample_rubrics))
    
with col3:
    # Check if archived version rubrics directory exists and count files
    versions_dir = get_rubrics_dir() / "versions"
    versions_count = len(list(versions_dir.glob("*.json"))) if versions_dir.exists() else 0
    st.metric("Archived Rubric Versions", versions_count)

st.markdown("---")

if not available_rubrics:
    st.warning("No rubrics available to manage.")
else:
    # Add empty option for no selection
    version_options = [""] + [r['filename'] for r in available_rubrics]
    
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
    
    version_rubric_name = st.selectbox(
        "Select rubric",
        options=version_options,
        index=default_index,
        key="version_rubric_select"
    )

    if version_rubric_name:
        versions = list_rubric_versions(version_rubric_name)

        if not versions:
            st.info(f"No versions found for rubric '{version_rubric_name}'.")
        else:
            st.markdown(f"**Available Versions for '{version_rubric_name}':**")

            # Create a table-like display
            for version in versions:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 3, 1])

                    with col1:
                        version_type = "📄 Current" if version['type'] == 'current' else "💾 Backup"
                        st.markdown(f"**{version_type}**")

                    with col2:
                        st.markdown(f"**v{version['version']}**")

                    with col3:
                        timestamp = version.get('timestamp', 'Current')
                        st.markdown(f"*{timestamp}*")

                    with col4:
                        if version['type'] == 'backup':
                            if st.button("🔄", key=f"restore_{version['version']}_{version_rubric_name}_{version.get('timestamp', 'current')}", help="Restore this version"):
                                with st.spinner("Restoring version..."):
                                    success, error = restore_rubric_version(version_rubric_name, version['version'])
                                    if success:
                                        st.success(f"✅ Restored '{version_rubric_name}' to version {version['version']}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error: {error}")
                        else:
                            st.markdown("*Current*")

                    st.divider()

# Navigation
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("✏️ View/Edit Rubric", use_container_width=True):
        if version_rubric_name:  # If a rubric is currently selected
            st.session_state['auto_select_rubric'] = version_rubric_name
        st.switch_page("pages/3_View_or_Edit_Rubric.py")
with col2:
    if st.button("➕ Create Rubric", use_container_width=True):
        st.switch_page("pages/4_Create_Rubric.py")
with col3:
    if st.button("📥 Import Rubric", use_container_width=True):
        st.switch_page("pages/5_Import_Rubric.py")