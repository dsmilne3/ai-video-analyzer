import sys
import os
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables explicitly
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import streamlit as st
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Analyze Video - AI Video Analyzer",
    page_icon="🎬",
    layout="wide"
)

# Check for dependencies
try:
    from src.video_evaluator import VideoEvaluator, AIProvider, list_available_rubrics, save_results
except ImportError as e:
    st.error("❌ Missing dependencies!")
    st.write(f"Error: {e}")
    st.write("")
    st.write("To check which dependencies are missing, run:")
    st.code("run.sh check", language="bash")
    st.write("To install all dependencies:")
    st.code("pip install -r requirements.txt", language="bash")
    st.stop()

st.title('Demo Video Analyzer')

# Configuration management for default rubric
CONFIG_FILE = Path(__file__).parent.parent / ".streamlit_config.json"

def load_config():
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    """Save configuration to file."""
    try:
        CONFIG_FILE.parent.mkdir(exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save configuration: {e}")

# Get available rubrics (refreshed on each page load)
available_rubrics = list_available_rubrics()
rubric_options = {r['name']: r['filename'] for r in available_rubrics}
rubric_descriptions = {r['name']: r['description'] for r in available_rubrics}

# Configuration management for default rubric
CONFIG_FILE = Path(__file__).parent.parent / ".streamlit_config.json"

def load_config():
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    """Save configuration to file."""
    try:
        CONFIG_FILE.parent.mkdir(exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save configuration: {e}")

# Load configuration and determine default rubric
config = load_config()
default_rubric_filename = config.get('default_rubric', 'sample-rubric')  # Default to 'sample-rubric'

# Validate that the configured default rubric still exists
if default_rubric_filename not in rubric_options.values():
    # Clear invalid default rubric from config
    if 'default_rubric' in config:
        del config['default_rubric']
        save_config(config)
    default_rubric_filename = 'sample-rubric'  # Reset to default

# Find the rubric name that corresponds to the default filename
default_rubric_name = None
for name, filename in rubric_options.items():
    if filename == default_rubric_filename:
        default_rubric_name = name
        break

# If the configured default doesn't exist, fall back to 'sample-rubric' or the first available
if not default_rubric_name:
    if 'sample-rubric' in rubric_options.values():
        for name, filename in rubric_options.items():
            if filename == 'sample-rubric':
                default_rubric_name = name
                break
    else:
        # Fall back to first available rubric
        default_rubric_name = list(rubric_options.keys())[0] if rubric_options else None

# Hide anchor links on headers to prevent link mouseover
st.markdown("""
<style>
/* Hide anchor links on headers */
h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
    display: none !important;
}
/* Also hide any anchor elements within header containers */
.st-emotion-cache-1v0mbdj a,
.st-emotion-cache-10trblm a {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state for file uploads
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'video_url' not in st.session_state:
    st.session_state.video_url = ''
if 'score_overrides' not in st.session_state:
    st.session_state.score_overrides = {}

# Add dependency check status in sidebar
with st.sidebar:
    # Rubric selection (moved to top of sidebar)
    st.subheader("⚙️ Evaluation Settings")
    selected_rubric_name = st.selectbox(
        'Evaluation Rubric',
        options=list(rubric_options.keys()),
        index=list(rubric_options.keys()).index(default_rubric_name) if default_rubric_name in rubric_options else 0,
        help='Choose the rubric to use for evaluation'
    )
    if selected_rubric_name:
        st.caption(f"📋 {rubric_descriptions[selected_rubric_name]}")
    
    # Button to set current selection as default
    if selected_rubric_name and rubric_options[selected_rubric_name] != config.get('default_rubric'):
        if st.button("Set as Default Rubric", use_container_width=True, help="Make this rubric the default for future sessions"):
            config['default_rubric'] = rubric_options[selected_rubric_name]
            save_config(config)
            st.success(f"✅ '{selected_rubric_name}' is now the default rubric!")
            st.rerun()
    
    provider = st.selectbox('AI Provider', ['openai','anthropic'])

    # System Status (moved to bottom of sidebar)
    st.subheader("System Status")
    
    # Check API keys
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    # Check OpenAI key
    if openai_key and openai_key.startswith('sk-') and not openai_key.endswith('your-openai-key-here'):
        st.success("✓ OpenAI API key loaded")
    else:
        st.error("❌ OpenAI API key missing or invalid")
    
    # Check Anthropic key
    if anthropic_key and anthropic_key.startswith('sk-ant-') and not anthropic_key.endswith('your-anthropic-key-here'):
        st.success("✓ Anthropic API key loaded")
    else:
        st.warning("⚠️ Anthropic API key missing or invalid (optional)")
    
    # Quick check for ffmpeg
    import subprocess
    try:
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            st.success("✓ ffmpeg installed")
        else:
            st.error("❌ ffmpeg not found")
            st.caption("Install with: brew install ffmpeg")
    except:
        st.warning("⚠️ Could not check ffmpeg")
    
        st.caption("Run `run.sh check` for full system check")

# Submitter information - moved to top
st.subheader("👤 Submitter Information")
col1, col2 = st.columns(2)
with col1:
    first_name = st.text_input("First Name", placeholder="Enter first name")
with col2:
    last_name = st.text_input("Last Name", placeholder="Enter last name")

partner_name = st.text_input("Partner Name", placeholder="Enter partner name (e.g. AHEAD, Bynet, WWT etc.)")

# Initialize session state for tracking uploaded file and URL
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'video_url' not in st.session_state:
    st.session_state.video_url = ''
if 'score_overrides' not in st.session_state:
    st.session_state.score_overrides = {}

# Input method selection
input_method = st.radio(
    "Input Method",
    ["Upload File", "URL"],
    horizontal=True
)

if input_method == "Upload File":
    # File upload - use disabled parameter to truly prevent clicking
    if st.session_state.uploaded_file is None:
        # No file uploaded - show enabled uploader
        uploaded = st.file_uploader(
            'Upload a local video or audio file', 
            type=['mp4','mov','mkv','avi','mp3','wav','m4a'],
            key='file_uploader_enabled'
        )
        if uploaded:
            st.session_state.uploaded_file = uploaded
            st.session_state.video_url = ''  # Clear URL when file uploaded
            st.rerun()
    else:
        # File already uploaded - show disabled uploader that displays the file
        st.file_uploader(
            'Upload a local video or audio file', 
            type=['mp4','mov','mkv','avi','mp3','wav','m4a'],
            disabled=True,
            key='file_uploader_disabled'
        )
        # Show the stored file with option to clear
        col1, col2 = st.columns([4, 1])
        with col1:
            st.info(f"📄 {st.session_state.uploaded_file.name}")
        with col2:
            if st.button("✕", key="clear_file", help="Remove file"):
                st.session_state.uploaded_file = None
                st.rerun()
else:
    # URL input
    video_url = st.text_input(
        'Video URL',
        value=st.session_state.video_url,
        placeholder='',
        label_visibility='collapsed'
    )
    
    if video_url != st.session_state.video_url:
        st.session_state.video_url = video_url
        st.session_state.uploaded_file = None  # Clear file when URL entered
    
    if st.session_state.video_url:
        # Validate URL format
        from urllib.parse import urlparse
        try:
            parsed = urlparse(st.session_state.video_url)
            is_valid_url = all([parsed.scheme in ['http', 'https'], parsed.netloc])
        except:
            is_valid_url = False
        
        if not is_valid_url:
            st.error("⚠️ Invalid URL format. Please enter a valid http:// or https:// URL.")
        else:
            # Only show the URL box and clear button if valid
            col1, col2 = st.columns([4, 1])
            with col1:
                st.info(f"🔗 {st.session_state.video_url}")
            with col2:
                if st.button("✕", key="clear_url", help="Remove URL"):
                    st.session_state.video_url = ''
                    st.rerun()

# Use the file from session state
uploaded = st.session_state.uploaded_file
video_url = st.session_state.video_url

# Validate URL if provided
from urllib.parse import urlparse
url_is_valid = True
if video_url and video_url.strip():
    try:
        parsed = urlparse(video_url)
        url_is_valid = all([parsed.scheme in ['http', 'https'], parsed.netloc])
    except:
        url_is_valid = False

# Initialize session state for analysis tracking
if 'analyzing' not in st.session_state:
    st.session_state.analyzing = False

# Initialize session state for storing analysis results
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# Initialize session state for triggering analysis
if 'start_analysis' not in st.session_state:
    st.session_state.start_analysis = False

# Enable analyze button if either file or valid URL is provided AND required fields are filled
can_analyze = (uploaded is not None or (video_url and video_url.strip() and url_is_valid)) and first_name.strip() and last_name.strip() and partner_name.strip()

# Processing options
st.subheader("⚙️ Processing Options")

# Determine API key validity for providers
openai_valid = bool(openai_key and openai_key.startswith('sk-') and not openai_key.endswith('your-openai-key-here'))
anthropic_valid = bool(anthropic_key and anthropic_key.startswith('sk-ant-') and not anthropic_key.endswith('your-anthropic-key-here'))

# Gate OpenAI API option on valid OpenAI key (only OpenAI has Whisper API)
openai_api_enabled = openai_valid

# Build transcription method options: show OpenAI Whisper API only when OpenAI key is valid
method_options = ["Local Whisper model"] + (["OpenAI Whisper API"] if openai_api_enabled else [])

# Show header
st.text("Transcription Method")

# Inform user how to enable OpenAI API when key isn't loaded (before the radio)
if not openai_api_enabled:
    st.caption("Load a valid OpenAI API key to enable remote transcription.")

transcription_method = st.radio(
    "Transcription Method",
    options=method_options,
    help="Use Local Whisper model for machines w/ GPUs - slow for CPU only; OpenAI Whisper API for CPU only machines - incurs cost",
    horizontal=True,
    label_visibility="collapsed"
)

translate = st.checkbox('Translate to English', value=True, help='Automatically translate non-English audio to English using Whisper')
vision = st.checkbox('Enable visual alignment checks')

# Dynamic button text and disabled state
button_text = "🚀 Analyzing Video..." if st.session_state.analyzing else "🚀 Analyze Video"
button_disabled = not can_analyze or st.session_state.analyzing

if st.button(button_text, disabled=button_disabled, use_container_width=True, type="primary"):
    # Set flags to start analysis
    st.session_state.start_analysis = True
    st.session_state.analyzing = True
    st.rerun()

# Run analysis if start_analysis flag is set
if st.session_state.start_analysis:
    # Clear the start_analysis flag
    st.session_state.start_analysis = False
    
    # Clear previous results when starting new analysis
    st.session_state.analysis_results = None
    
    # Warn user about UI unresponsiveness
    warning_placeholder = st.empty()
    warning_placeholder.warning("⚠️ **Analysis in progress** - The interface may be slow or unresponsive during processing. This is normal and can take several minutes depending on video length and model used for transcription/translation. Halting the application during analysis may also freeze the console while the processes are gracefully shut down and artifacts are cleaned up.")
    
    tmp = None
    try:
        prov = AIProvider.OPENAI if provider == 'openai' else AIProvider.ANTHROPIC
        rubric_filename = rubric_options[selected_rubric_name]
        
        # Map friendly name to internal value - "OpenAI Whisper API" uses openai for transcription, "Local Whisper model" uses local
        method_internal = "openai" if transcription_method == "OpenAI Whisper API" else "local"
        
        # Progress callback that prints to terminal (stdout)
        def progress_callback(message: str):
            print(message, flush=True)
        
        # Show progress with status updates
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        # Progress callback that updates the UI in real-time
        def ui_progress_callback(message: str):
            # Map internal progress messages to UI step numbers
            if "Downloading from URL" in message:
                progress_placeholder.write("⏳ **Step 1/4:** Downloading video/audio...")
            elif "Download complete" in message:
                progress_placeholder.write("⏳ **Step 2/4:** Transcribing audio with Whisper...")
            elif "Transcribing audio" in message:
                # Extract model and device info from message like "🎤 Transcribing audio with Whisper base model on CPU..."
                if "Whisper" in message and "model" in message:
                    progress_placeholder.write(f"⏳ **Step 2/4:** {message.replace('🎤 ', '')}")
                elif "OpenAI API" in message:
                    progress_placeholder.write("⏳ **Step 2/4:** Transcribing with OpenAI API...")
                else:
                    progress_placeholder.write("⏳ **Step 2/4:** Transcribing audio with Whisper model...")
            elif "Analyzing video frames" in message:
                progress_placeholder.write("⏳ **Step 3/4:** Analyzing video frames...")
            elif "Evaluating transcript" in message:
                progress_placeholder.write("⏳ **Step 3/4:** Evaluating with AI...")
            elif "Generating qualitative feedback" in message:
                progress_placeholder.write("⏳ **Step 4/4:** Generating feedback...")
            # Also print to terminal for debugging
            print(message, flush=True)
        
        evaluator = VideoEvaluator(
            rubric_path=rubric_filename,
            api_key=openai_key if provider == 'openai' else anthropic_key,
            provider=prov, 
            enable_vision=vision, 
            verbose=True,  # Back to normal - chunking now works properly
            progress_callback=ui_progress_callback,
            translate_to_english=translate,
            transcription_method=method_internal,
            openai_api_key=openai_key  # Always pass OpenAI key for Whisper API
        )
        
        with status_placeholder.container():
            progress_placeholder.write("⏳ **Step 1/4:** Preparing audio...")
            progress_placeholder.caption("This may take a few minutes, depending on audio/video length")
            
            # Process based on input type
            if uploaded:
                # File upload - save to temp
                tmp = f"/tmp/{uploaded.name}"
                with open(tmp, 'wb') as f:
                    f.write(uploaded.getbuffer())
                res = evaluator.process(tmp, is_url=False, enable_vision=vision)
                original_filename = uploaded.name
            else:
                # URL - process directly
                res = evaluator.process(video_url, is_url=True, enable_vision=vision)
                # Extract filename from URL for results saving
                from urllib.parse import urlparse
                import os
                parsed_url = urlparse(video_url)
                original_filename = os.path.basename(parsed_url.path) or "video_from_url"
            
            # Print completion to terminal
            print("✅ Analysis complete!", flush=True)
            print("", flush=True)
            print("", flush=True)
        
        # Reorganize results with submitter information at the top
        submitter_info = {
            'first_name': first_name.strip(),
            'last_name': last_name.strip(),
            'partner_name': partner_name.strip()
        }
        
        # Create new result dictionary with submitter at the top
        res = {'submitter': submitter_info, **res}
        
        # Store results in session state for persistence across reruns
        st.session_state.analysis_results = res
        
        # Reset analyzing state after successful completion
        st.session_state.analyzing = False
        
        # Trigger a rerun to update the button state
        st.rerun()
        
        progress_placeholder.empty()
        status_placeholder.empty()
        
        # Clear the warning message now that analysis is complete
        warning_placeholder.empty()

        # Display transcription quality first (for reviewer confidence)
        
    except FileNotFoundError as e:
        st.session_state.analyzing = False
        st.rerun()
        warning_placeholder.empty()
        if 'ffmpeg' in str(e).lower():
            st.error("❌ ffmpeg not found")
            st.write("ffmpeg is required for video/audio processing.")
            st.write("Install with:")
            st.code("brew install ffmpeg", language="bash")
        else:
            st.error(f"File not found: {e}")
    except Exception as e:
        st.session_state.analyzing = False
        st.rerun()
        warning_placeholder.empty()
        st.error(f"Error processing video: {e}")
        st.write("Run `run.sh check` to verify all dependencies are installed.")
    finally:
        # Clean up temp file
        if tmp:
            try:
                import os
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass

# Display results if available in session state
if st.session_state.analysis_results is not None:
    res = st.session_state.analysis_results
    
    quality = res.get('quality', {})
    if quality:
        quality_rating = quality.get('quality_rating', 'unknown').upper()
        
        with st.expander(f"🎤 Transcription Quality: {quality_rating}", expanded=False):
                # Check if transcription failed
                transcript_text = res.get('transcript', '')
                if transcript_text == "(mock) transcribed text from audio":
                    st.error("❌ **Transcription failed** - Whisper model could not load. Using mock transcript.")
                    st.caption("This usually happens due to memory constraints or missing dependencies.")
                
                # Display model and device information
                whisper_model = res.get('whisper_model', 'unknown')
                device = res.get('device', 'unknown')
                device_display = "Apple Silicon GPU (MPS)" if device == "mps" else ("CPU" if device == "cpu" else device.upper())
                st.write(f"**Model:** Whisper {whisper_model} on {device_display}")
                
                # Display detected language
                language = res.get('language', 'unknown')
                if translate and language.lower() != 'en':
                    st.write(f"**Detected Language:** {language.upper()} → 🌐 Translated to English")
                    st.caption("Audio was translated to English by Whisper during transcription")
                else:
                    st.write(f"**Detected Language:** {language.upper()}")
                    st.caption("Language automatically detected by Whisper during transcription")
                
                warnings = quality.get('warnings', [])
                if warnings:
                    st.warning("⚠️ **Quality Warnings:**")
                    for warning in warnings:
                        st.write(f"  - {warning}")
                
                st.write(f"**Confidence:** {quality.get('avg_confidence', 0):.1f}%")
                st.caption("How certain Whisper is about the transcription accuracy")
                
                st.write(f"**Speech Detection:** {quality.get('speech_percentage', 0):.1f}%")
                st.caption("Percentage of audio detected as speech vs. silence/noise")
                
                st.write(f"**Compression Ratio:** {quality.get('avg_compression_ratio', 0):.2f}")
                st.caption("Text length vs. audio duration; 1.5-2.5 is typical for normal speech")
                
                details = quality.get('details', {})
                st.write(f"**Average Log Probability:** {details.get('avg_logprob', 0):.3f}")
                st.caption("Model confidence score; values closer to 0 indicate higher confidence")
                
                st.write(f"**Segments Analyzed:** {details.get('num_segments', 0)}")
                st.caption("Number of speech segments identified in the audio")

        # Visual Analysis (if enabled) - placed right after transcription quality
        if res.get('visual_analysis'):
            visual_text = res.get('visual_analysis', '')
            # Determine if mismatches were detected
            visual_lower = visual_text.lower()
            
            # If text contains "no mismatch" or "no clear mismatch", it's clean
            # Otherwise look for problem indicators
            if 'no mismatch' in visual_lower or 'no clear mismatch' in visual_lower:
                has_mismatch = False
            else:
                # Look for actual problem indicators
                has_mismatch = any(phrase in visual_lower for phrase in [
                    'mismatch detected',
                    'does not match',
                    'not visible',
                    'inconsistent',
                    'contradiction',
                    'discrepancy'
                ])
            
            status_message = "Mismatches detected" if has_mismatch else "No mismatches detected"
            
            with st.expander(f"👁️ Visual Analysis: {status_message}", expanded=False):
                st.text(visual_text)

        # Display evaluation results prominently
        st.subheader('📊 Evaluation Results')
        evaluation = res.get('evaluation', {})
        overall = evaluation.get('overall', {})
        
        # Check if using new rubric format (has categories)
        is_new_format = 'categories' in evaluation
        
        col1, col2 = st.columns(2)
        with col1:
            if is_new_format:
                total_points = overall.get('total_points', 0)
                max_points = overall.get('max_points', 50)
                percentage = overall.get('percentage', 0)
                st.metric("Overall Score", f"{total_points}/{max_points} ({percentage:.1f}%)")
            else:
                score = overall.get('weighted_score', 0)
                st.metric("Overall Score", f"{score:.1f}/10")
        with col2:
            status = overall.get('pass_status', 'unknown').upper()
            status_color = "🟢" if status == "PASS" else ("🟡" if status == "REVISE" else "🔴")
            st.metric("Status", f"{status_color} {status}")
        
        # Display category scores for new format
        if is_new_format and 'categories' in evaluation:
            # Load the rubric to get proper labels
            rubric_filename = rubric_options[selected_rubric_name]
            rubric_path = Path(__file__).parent.parent / "rubrics" / f"{rubric_filename}.json"
            rubric_data = {}
            try:
                with open(rubric_path, 'r') as f:
                    rubric_data = json.load(f)
            except:
                pass
            
            # Create category label mapping
            category_labels = {}
            category_weights = {}
            if rubric_data and "categories" in rubric_data:
                for category in rubric_data["categories"]:
                    category_labels[category["category_id"]] = category["label"]
                    category_weights[category["category_id"]] = category.get("weight", 0)
            
            st.markdown("### 📂 Category Breakdown")
            categories = evaluation.get('categories', {})
            scores = evaluation.get('scores', {})
            
            # Check if any scores are fallback (heuristic) and show prominent warning
            fallback_criteria = []
            
            # Create criterion label mapping for fallback detection
            temp_criterion_labels = {}
            if rubric_data:
                if "categories" in rubric_data:
                    # New format
                    for category in rubric_data["categories"]:
                        for criterion in category["criteria"]:
                            temp_criterion_labels[criterion["criterion_id"]] = criterion["label"]
                else:
                    # Old format
                    for criterion in rubric_data["criteria"]:
                        temp_criterion_labels[criterion["id"]] = criterion["label"]
            
            for criterion_id, data in scores.items():
                note = data.get('note', '')
                if 'Auto-generated conservative score' in note:
                    fallback_criteria.append(temp_criterion_labels.get(criterion_id, criterion_id))
            
            if fallback_criteria:
                st.error("🚨 **AI Evaluation Failed** - Using Conservative Fallback Scores")
                st.warning("The AI API calls failed, so we're using automatic scoring instead of AI evaluation. This may not reflect the true quality of the video. Please check your API key credits and connection.")
                st.info(f"**Affected criteria:** {', '.join(fallback_criteria)}")
                st.markdown("---")
            
            # Create mapping of criteria to categories
            category_criteria = {}
            if rubric_data and "categories" in rubric_data:
                for category in rubric_data["categories"]:
                    category_criteria[category["category_id"]] = [
                        criterion["criterion_id"] for criterion in category["criteria"]
                    ]
            
            # Create table headers
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown("**Name**")
            with col2:
                st.markdown("**Score**")
            with col3:
                st.markdown("**Weight**")
            with col4:
                st.markdown("**Confidence**")
            
            for cat_id, cat_data in categories.items():
                cat_name = category_labels.get(cat_id, cat_id.replace('_', ' ').title())
                points = cat_data.get('points', 0)
                max_points = cat_data.get('max_points', 0)
                percentage = cat_data.get('percentage', 0)
                weight = category_weights.get(cat_id, 0)
                
                # Calculate average confidence for this category
                category_confidences = []
                if cat_id in category_criteria:
                    for criterion_id in category_criteria[cat_id]:
                        if criterion_id in scores:
                            confidence = scores[criterion_id].get('confidence')
                            if isinstance(confidence, int):
                                category_confidences.append(confidence)
                
                avg_confidence = None
                if category_confidences:
                    avg_confidence = sum(category_confidences) / len(category_confidences)
                
                # Determine confidence text label (High/Medium/Low)
                if avg_confidence is not None:
                    if avg_confidence >= 8:
                        confidence_display = f"High ({avg_confidence:.1f}/10)"
                    elif avg_confidence >= 6:
                        confidence_display = f"Medium ({avg_confidence:.1f}/10)"
                    else:
                        confidence_display = f"Low ({avg_confidence:.1f}/10)"
                else:
                    confidence_display = "N/A"
                
                # Determine score stoplight based on percentage
                if percentage >= 80:
                    score_icon = "🟢"
                elif percentage >= 60:
                    score_icon = "🟡"
                else:
                    score_icon = "🔴"
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{cat_name}**")
                with col2:
                    st.markdown(f"{score_icon} **{points}/{max_points}** ({percentage:.1f}%)")
                with col3:
                    st.markdown(f"**{weight:.1f}**")
                with col4:
                    st.markdown(confidence_display)
        
        # Display qualitative feedback
        feedback = res.get('feedback')
        if feedback:
            tone = feedback.get('tone', 'supportive')
            tone_emoji = "🎉" if tone == 'congratulatory' else "🤝"
            
            st.subheader(f'{tone_emoji} Feedback for Submitter')
            
            # Check if feedback is fallback-generated
            is_fallback_feedback = False
            strengths = feedback.get('strengths', [])
            improvements = feedback.get('improvements', [])
            
            # Check for generic fallback patterns in feedback
            for item in strengths + improvements:
                desc = item.get('description', '')
                if 'You scored' in desc and ('Good performance in this area.' in desc or 'Consider focusing on improving this aspect.' in desc):
                    is_fallback_feedback = True
                    break
            
            if is_fallback_feedback:
                st.warning("🤖 **AI Feedback Generation Failed** - Using generic feedback based on scores")
                st.caption("The AI couldn't generate personalized feedback, so we're showing basic feedback derived from the scores.")
            
            # Strengths
            st.markdown("### ✓ Strengths")
            for i, strength in enumerate(strengths, 1):
                with st.expander(f"**{strength.get('title', 'Strength')}**", expanded=True):
                    st.write(strength.get('description', ''))
            
            # Areas for improvement
            st.markdown("### → Areas for Improvement")
            for i, improvement in enumerate(improvements, 1):
                with st.expander(f"**{improvement.get('title', 'Area for improvement')}**", expanded=True):
                    st.write(improvement.get('description', ''))

        # Display detailed scores table
        scores = evaluation.get('scores', {})
        if scores:
            # Load the rubric to get proper labels
            rubric_filename = rubric_options[selected_rubric_name]
            rubric_path = Path(__file__).parent.parent / "rubrics" / f"{rubric_filename}.json"
            rubric_data = {}
            try:
                with open(rubric_path, 'r') as f:
                    rubric_data = json.load(f)
            except:
                pass
            
            # Create criterion label mapping
            criterion_labels = {}
            if rubric_data:
                if "categories" in rubric_data:
                    # New format
                    for category in rubric_data["categories"]:
                        for criterion in category["criteria"]:
                            criterion_labels[criterion["criterion_id"]] = criterion["label"]
                else:
                    # Old format
                    for criterion in rubric_data["criteria"]:
                        criterion_labels[criterion["id"]] = criterion["label"]
            
            with st.expander("### 📋 Detailed Criteria Scores", expanded=False):
                # Create table headers
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
                with col1:
                    st.markdown("**Criterion**")
                with col2:
                    st.markdown("**Score**")
                with col3:
                    st.markdown("**Confidence**")
                with col4:
                    st.markdown("**Notes**")
                
                st.markdown("---")  # Divider line
                
                # Display each criterion in table format
                for criterion_id, data in scores.items():
                    criterion_name = criterion_labels.get(criterion_id, criterion_id.replace('_', ' ').title())
                    original_score = data.get('score', 'N/A')
                    
                    # Check for override
                    override_key = f"override_{criterion_id}"
                    if override_key in st.session_state.score_overrides and st.session_state.score_overrides[override_key]['enabled']:
                        score = st.session_state.score_overrides[override_key]['score']
                        score_display_base = f"{score}"
                        if not is_new_format:
                            score_display_base += "/10"
                        score_display = f"**{score_display_base}** ⚠️ (Overridden from {original_score})"
                    else:
                        score = original_score
                        # Determine max score based on rubric format
                        if is_new_format:
                            score_display = f"**{score}**"
                        else:
                            score_display = f"**{score}/10**"
                    
                    confidence = data.get('confidence', 'N/A')
                    note = data.get('note', '')
                    
                    # Determine confidence level and color
                    if isinstance(confidence, int):
                        if confidence >= 8:
                            confidence_display = f"🟢 {confidence}/10"
                        elif confidence >= 6:
                            confidence_display = f"🟡 {confidence}/10"
                        else:
                            confidence_display = f"🔴 {confidence}/10"
                    else:
                        confidence_display = "N/A"
                    
                    # Use columns for table-like display
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
                    with col1:
                        st.markdown(f"**{criterion_name}**")
                    with col2:
                        st.markdown(score_display)
                    with col3:
                        st.markdown(confidence_display)
                    with col4:
                        st.caption(note if note else "—")

        st.subheader('Transcript')
        with st.expander("**View Full Transcript**", expanded=False):
            st.text(res.get('transcript', ''))

        with st.expander("**View Full JSON Results**", expanded=False):
            st.json(res)
        
        # Save results to file with new naming format
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"{first_name.strip()}_{last_name.strip()}_{partner_name.strip()}_{timestamp}"
        saved_json_path = save_results(res, result_filename, output_format='json')
        
        # Show success message and provide download button
        st.success(f"💾 Results saved to `results/` folder")
        
        # Create centered download button for JSON version
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            json_content = json.dumps(res, indent=2)
            st.download_button(
                label="📄 Download JSON Report",
                data=json_content,
                file_name=f"{result_filename}_results.json",
                mime="application/json",
                use_container_width=True
            )

    # Reset analyzing state after successful completion
    st.session_state.analyzing = False

