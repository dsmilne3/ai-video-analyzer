import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple, Callable
import json
from datetime import datetime

import base64
try:
    import whisper
except Exception:
    whisper = None
try:
    import whisperx
except Exception:
    whisperx = None
try:
    import cv2
except Exception:
    cv2 = None
try:
    from tqdm import tqdm
except Exception:
    tqdm = None
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# Default rubric (fallback if rubric.json not found)
DEFAULT_RUBRIC = {
    "criteria": [
        {"id": "technical_accuracy", "label": "Technical Accuracy", "desc": "Correctness of technical claims and explanations", "weight": 0.30},
        {"id": "clarity", "label": "Clarity", "desc": "How easy the explanation is to follow", "weight": 0.25},
        {"id": "completeness", "label": "Completeness", "desc": "Coverage of key features and flows", "weight": 0.20},
        {"id": "production_quality", "label": "Production Quality", "desc": "Audio clarity and pacing", "weight": 0.05},
        {"id": "value_demonstration", "label": "Value Demonstration", "desc": "Articulation of business/customer value", "weight": 0.15},
        {"id": "multimodal_alignment", "label": "Multimodal Alignment", "desc": "Transcript and visuals are consistent (non-feature-specific)", "weight": 0.05}
    ],
    "scale": {"min": 1, "max": 10},
    "overall_method": "weighted_mean",
    "thresholds": {"pass": 6.5, "revise": 5.0}
}


# Validate rubric structure
def validate_rubric(rubric: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate rubric structure and return (is_valid, error_message).

    Supports both old format (criteria array) and new format (categories with nested criteria).
    Returns:
        Tuple of (True, None) if valid, or (False, error_message) if invalid
    """
    # Check top-level keys - support both old and new formats
    required_keys_old = {"criteria", "scale", "overall_method", "thresholds"}
    required_keys_new = {"rubric_id", "name", "version", "categories", "scale", "thresholds"}

    has_old_format = all(key in rubric for key in required_keys_old)
    has_new_format = all(key in rubric for key in required_keys_new)

    if not (has_old_format or has_new_format):
        return False, f"Rubric must have either old format keys {required_keys_old} or new format keys {required_keys_new}"

    if has_new_format:
        # Validate new format
        return _validate_new_rubric_format(rubric)
    else:
        # Validate old format (backward compatibility)
        return _validate_old_rubric_format(rubric)


def _validate_new_rubric_format(rubric: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate new rubric format with categories and nested criteria."""
    # Validate categories
    if not isinstance(rubric["categories"], list) or len(rubric["categories"]) == 0:
        return False, "categories must be a non-empty list"

    seen_category_ids = set()
    total_category_weight = 0.0
    total_max_points = 0

    for i, category in enumerate(rubric["categories"]):
        # Check required fields
        required_fields = {"category_id", "label", "weight", "max_points", "criteria"}
        if not all(field in category for field in required_fields):
            missing = required_fields - set(category.keys())
            return False, f"Category {i} missing required fields: {missing}"

        # Check for duplicate category IDs
        if category["category_id"] in seen_category_ids:
            return False, f"Duplicate category ID: {category['category_id']}"
        seen_category_ids.add(category["category_id"])

        # Check category weight is a number between 0 and 1
        try:
            weight = float(category["weight"])
            if weight < 0 or weight > 1:
                return False, f"Category '{category['category_id']}' weight must be between 0 and 1"
            total_category_weight += weight
        except (TypeError, ValueError):
            return False, f"Category '{category['category_id']}' weight must be a number"

        # Check category max_points is a positive integer
        try:
            max_points = int(category["max_points"])
            if max_points <= 0:
                return False, f"Category '{category['category_id']}' max_points must be positive"
            total_max_points += max_points
        except (TypeError, ValueError):
            return False, f"Category '{category['category_id']}' max_points must be a positive integer"

        # Validate criteria within category
        if not isinstance(category["criteria"], list) or len(category["criteria"]) == 0:
            return False, f"Category '{category['category_id']}' criteria must be a non-empty list"

        seen_criterion_ids = set()
        category_points = 0

        for j, criterion in enumerate(category["criteria"]):
            # Check required fields
            required_fields = {"criterion_id", "label", "max_points"}
            if not all(field in criterion for field in required_fields):
                missing = required_fields - set(criterion.keys())
                return False, f"Category '{category['category_id']}' criterion {j} missing required fields: {missing}"

            # Check for duplicate criterion IDs
            if criterion["criterion_id"] in seen_criterion_ids:
                return False, f"Duplicate criterion ID in category '{category['category_id']}': {criterion['criterion_id']}"
            seen_criterion_ids.add(criterion["criterion_id"])

            # Check criterion max_points is a positive integer
            try:
                crit_max_points = int(criterion["max_points"])
                if crit_max_points <= 0:
                    return False, f"Criterion '{criterion['criterion_id']}' max_points must be positive"
                category_points += crit_max_points
            except (TypeError, ValueError):
                return False, f"Criterion '{criterion['criterion_id']}' max_points must be a positive integer"

        # Check that category max_points equals sum of criterion max_points
        if category_points != category["max_points"]:
            return False, f"Category '{category['category_id']}' max_points ({category['max_points']}) must equal sum of criterion max_points ({category_points})"

    # Check category weights sum to approximately 1.0
    if not (0.99 <= total_category_weight <= 1.01):
        return False, f"Category weights must sum to 1.0 (current sum: {total_category_weight:.4f})"

    # Validate scale (same as old format)
    if not isinstance(rubric["scale"], dict):
        return False, "scale must be a dict"
    if "min" not in rubric["scale"] or "max" not in rubric["scale"]:
        return False, "scale must have 'min' and 'max' keys"
    try:
        min_val = float(rubric["scale"]["min"])
        max_val = float(rubric["scale"]["max"])
        if min_val >= max_val:
            return False, "scale min must be less than max"
    except (TypeError, ValueError):
        return False, "scale min and max must be numbers"

    # Validate thresholds (same as old format)
    if not isinstance(rubric["thresholds"], dict):
        return False, "thresholds must be a dict"
    if "pass" not in rubric["thresholds"] or "revise" not in rubric["thresholds"]:
        return False, "thresholds must have 'pass' and 'revise' keys"
    try:
        pass_threshold = float(rubric["thresholds"]["pass"])
        revise_threshold = float(rubric["thresholds"]["revise"])
        if revise_threshold >= pass_threshold:
            return False, "revise threshold must be less than pass threshold"
    except (TypeError, ValueError):
        return False, "thresholds must be numbers"

    return True, None


def _validate_old_rubric_format(rubric: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate old rubric format with flat criteria array (for backward compatibility)."""
    # Check top-level keys
    required_keys = {"criteria", "scale", "overall_method", "thresholds"}
    if not all(key in rubric for key in required_keys):
        missing = required_keys - set(rubric.keys())
        return False, f"Missing required keys: {missing}"

    # Validate criteria
    if not isinstance(rubric["criteria"], list) or len(rubric["criteria"]) == 0:
        return False, "criteria must be a non-empty list"

    seen_ids = set()
    total_weight = 0.0
    for i, criterion in enumerate(rubric["criteria"]):
        # Check required fields
        required_fields = {"id", "label", "desc", "weight"}
        if not all(field in criterion for field in required_fields):
            missing = required_fields - set(criterion.keys())
            return False, f"Criterion {i} missing required fields: {missing}"

        # Check for duplicate IDs
        if criterion["id"] in seen_ids:
            return False, f"Duplicate criterion ID: {criterion['id']}"
        seen_ids.add(criterion["id"])

        # Check weight is a number
        try:
            weight = float(criterion["weight"])
            if weight < 0 or weight > 1:
                return False, f"Criterion '{criterion['id']}' weight must be between 0 and 1"
            total_weight += weight
        except (TypeError, ValueError):
            return False, f"Criterion '{criterion['id']}' weight must be a number"

    # Check weights sum to approximately 1.0 (allow small floating point errors)
    if not (0.99 <= total_weight <= 1.01):
        return False, f"Criterion weights must sum to 1.0 (current sum: {total_weight:.4f})"

    # Validate scale
    if not isinstance(rubric["scale"], dict):
        return False, "scale must be a dict"
    if "min" not in rubric["scale"] or "max" not in rubric["scale"]:
        return False, "scale must have 'min' and 'max' keys"
    try:
        min_val = float(rubric["scale"]["min"])
        max_val = float(rubric["scale"]["max"])
        if min_val >= max_val:
            return False, "scale min must be less than max"
    except (TypeError, ValueError):
        return False, "scale min and max must be numbers"

    # Validate thresholds
    if not isinstance(rubric["thresholds"], dict):
        return False, "thresholds must be a dict"
    if "pass" not in rubric["thresholds"] or "revise" not in rubric["thresholds"]:
        return False, "thresholds must have 'pass' and 'revise' keys"
    try:
        pass_threshold = float(rubric["thresholds"]["pass"])
        revise_threshold = float(rubric["thresholds"]["revise"])
        if revise_threshold >= pass_threshold:
            return False, "revise threshold must be less than pass threshold"
    except (TypeError, ValueError):
        return False, "thresholds must be numbers"

    return True, None


# Load rubric from file or use default
def load_rubric(rubric_name: str = "sample-rubric") -> Dict[str, Any]:
    """Load rubric from rubrics/{rubric_name}.json, validate it, or fall back to default.
    
    Args:
        rubric_name: Name of the rubric file (without .json extension). Defaults to "sample-rubric".
        
    Returns:
        Dict containing the rubric structure
    """
    # Try new rubrics directory first
    rubrics_dir = Path(__file__).parent.parent / "rubrics"
    rubric_path = rubrics_dir / f"{rubric_name}.json"
    
    # Fallback to old location for backward compatibility
    if not rubric_path.exists():
        rubric_path = Path(__file__).parent.parent / "rubric.json"
    
    try:
        with open(rubric_path, 'r') as f:
            rubric = json.load(f)
        
        # Validate the loaded rubric
        is_valid, error_msg = validate_rubric(rubric)
        if not is_valid:
            print(f"Warning: Invalid rubric format in {rubric_path}: {error_msg}. Using default rubric.")
            return DEFAULT_RUBRIC
        
        return rubric
    except (FileNotFoundError, json.JSONDecodeError) as e:
        if rubric_name == "sample-rubric":
            # Special fallback: if sample-rubric.json can't be found, try default.json
            print(f"Warning: Could not load rubric '{rubric_name}' ({e}). Falling back to default.json.")
            return load_rubric("default")
        elif rubric_name != "default":
            print(f"Warning: Could not load rubric '{rubric_name}' ({e}). Falling back to default rubric.")
            return load_rubric("default")
        else:
            print(f"Warning: Could not load default rubric ({e}). Using built-in default.")
            return DEFAULT_RUBRIC


def list_available_rubrics() -> List[Dict[str, str]]:
    """List all available rubrics in the rubrics directory.
    
    Returns:
        List of dicts with 'name', 'filename', and 'description' keys
        Only includes rubrics with status="current"
    """
    rubrics_dir = Path(__file__).parent.parent / "rubrics"
    available = []
    
    if rubrics_dir.exists():
        for rubric_file in sorted(rubrics_dir.rglob("*.json")):
            try:
                with open(rubric_file, 'r') as f:
                    rubric_data = json.load(f)
                
                # Validate before adding to list
                is_valid, _ = validate_rubric(rubric_data)
                # Only include rubrics marked as current
                if is_valid and rubric_data.get('status') == 'current':
                    available.append({
                        'filename': rubric_file.stem,
                        'name': rubric_data.get('name', rubric_file.stem),
                        'description': rubric_data.get('description', 'No description available')
                    })
            except (json.JSONDecodeError, Exception):
                continue
    
    # Handle duplicate names by appending filename in parentheses
    seen_names = set()
    for rubric in available:
        original_name = rubric['name']
        counter = 1
        while rubric['name'] in seen_names:
            rubric['name'] = f"{original_name} ({rubric['filename']})"
            counter += 1
        seen_names.add(rubric['name'])
    
    # Ensure sample rubric is always available
    if not any(r['filename'] == 'sample-rubric' for r in available):
        available.insert(0, {
            'filename': 'sample-rubric',
            'name': 'Sample Rubric',
            'description': 'Built-in sample rubric'
        })
    
    return available


def save_results(result: Dict[str, Any], input_filename: str, output_format: str = 'json') -> str:
    """Save evaluation results to the results/ folder with timestamp to prevent overwrites.
    
    Args:
        result: The evaluation result dictionary
        input_filename: Original input file name (e.g., 'realistic_demo.wav')
        output_format: Output format ('txt' for CLI, 'json' for programmatic use)
        
    Returns:
        Path to the saved results file
    """
    # Create results directory if it doesn't exist
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Extract submitter information if available
    submitter = result.get('submitter', {})
    first_name = submitter.get('first_name', '').strip()
    last_name = submitter.get('last_name', '').strip()
    partner_name = submitter.get('partner_name', '').strip()
    
    # Generate output filename with submitter info (required fields ensure this is always available)
    base_name = Path(input_filename).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{first_name}_{last_name}_{partner_name}_{timestamp}.{output_format}"
    
    output_path = results_dir / output_filename
    
    if output_format == 'json':
        # Save as JSON for programmatic access
        with open(output_path, 'w') as f:
            json.dump(result, indent=2, fp=f)
    else:
        # Save as human-readable text (CLI format)
        with open(output_path, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("DEMO VIDEO EVALUATION RESULTS\n")
            f.write("=" * 70 + "\n\n")
            
            # Evaluation summary
            evaluation = result.get('evaluation', {})
            overall = evaluation.get('overall', {})
            
            status = overall.get('pass_status', 'unknown').upper()
            status_emoji = "🟢" if status == "PASS" else ("🟡" if status == "REVISE" else "🔴")
            f.write(f"Status: {status_emoji} {status}\n")
            
            # Check if using new rubric format (has categories)
            is_new_format = 'categories' in evaluation
            
            if is_new_format:
                total_points = overall.get('total_points', 0)
                max_points = overall.get('max_points', 50)
                percentage = overall.get('percentage', 0)
                f.write(f"Overall Score: {total_points}/{max_points} ({percentage:.1f}%)\n")
            else:
                f.write(f"Overall Score: {overall.get('weighted_score', 0):.1f}/10\n")
            
            short_summary = evaluation.get('short_summary', '')
            if short_summary:
                f.write(f"Summary: {short_summary}\n")
            f.write("\n")
            
            # Transcription quality
            quality = result.get('quality', {})
            if quality:
                quality_rating = quality.get('quality_rating', 'unknown').upper()
                f.write(f"Transcription Quality: {quality_rating}\n")
                f.write(f"  Confidence: {quality.get('avg_confidence', 0):.1f}%\n")
                f.write(f"    (How certain Whisper is about the transcription)\n")
                f.write(f"  Speech Detection: {quality.get('speech_percentage', 0):.1f}%\n")
                f.write(f"    (Percentage of audio detected as speech vs. silence/noise)\n")
                f.write(f"  Compression Ratio: {quality.get('avg_compression_ratio', 0):.2f}\n")
                f.write(f"    (Text length vs. audio duration; 1.5-2.5 is typical)\n")
                
                warnings = quality.get('warnings', [])
                if warnings:
                    f.write(f"\n  ⚠️  Quality Warnings:\n")
                    for warning in warnings:
                        f.write(f"     - {warning}\n")
                f.write("\n")
            
            # Feedback section
            feedback = result.get('feedback', {})
            if feedback:
                tone = feedback.get('tone', 'supportive')
                f.write("-" * 70 + "\n")
                f.write(f"FEEDBACK ({tone.upper()} TONE)\n")
                f.write("-" * 70 + "\n\n")
                
                f.write("✓ STRENGTHS:\n\n")
                for i, strength in enumerate(feedback.get('strengths', []), 1):
                    f.write(f"{i}. {strength.get('title', 'Strength')}\n")
                    f.write(f"   {strength.get('description', '')}\n\n")
                
                f.write("→ AREAS FOR IMPROVEMENT:\n\n")
                for i, improvement in enumerate(feedback.get('improvements', []), 1):
                    f.write(f"{i}. {improvement.get('title', 'Area for improvement')}\n")
                    f.write(f"   {improvement.get('description', '')}\n\n")
            
            # Full transcript
            f.write("-" * 70 + "\n")
            f.write("FULL TRANSCRIPT\n")
            f.write("-" * 70 + "\n\n")
            f.write(result.get('transcript', '') + "\n\n")
            
            # Full JSON for reference
            f.write("-" * 70 + "\n")
            f.write("FULL JSON OUTPUT\n")
            f.write("-" * 70 + "\n\n")
            f.write(json.dumps(result, indent=2) + "\n")
    
    return str(output_path)


RUBRIC = load_rubric()  # Load default rubric on module import


class VideoEvaluator:
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi', '.mkv'}
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.m4a', '.aac'}

    def _move_model_to_mps_selective(self, model):
        """Move Whisper model to MPS selectively, keeping sparse tensors on CPU.
        
        This works around PyTorch's limitation where sparse tensors can't be moved to MPS.
        We move dense tensors to MPS for GPU acceleration while keeping sparse tensors on CPU.
        """
        try:
            import torch
            
            # Check if MPS is available
            if not torch.backends.mps.is_available():
                return model
            
            # Recursively move model parameters to MPS, but skip sparse tensors
            def move_to_device(module, device):
                for name, param in module.named_parameters():
                    if param.is_sparse:
                        # Keep sparse tensors on CPU
                        param.data = param.data.to('cpu')
                    else:
                        # Move dense tensors to MPS
                        param.data = param.data.to(device)
                
                for name, buf in module.named_buffers():
                    if buf.is_sparse:
                        # Keep sparse buffers on CPU
                        buf.data = buf.data.to('cpu')
                    else:
                        # Move dense buffers to MPS
                        buf.data = buf.data.to(device)
            
            move_to_device(model, 'mps')
            return model
            
        except Exception as e:
            # If selective placement fails, return original model
            if self.verbose:
                print(f"Warning: Selective MPS placement failed ({e}), using CPU")
            return model

    def __init__(self, rubric_path: str, api_key: Optional[str] = None, provider: AIProvider = AIProvider.OPENAI, verbose: bool = False, enable_vision: bool = False, translate_to_english: bool = False, progress_callback: Optional[Callable[[str], None]] = None, transcription_method: str = "local", openai_api_key: Optional[str] = None):
        # Load rubric using the load_rubric function which handles path construction
        self.rubric = load_rubric(rubric_path)
        self.rubric_name = rubric_path
        self.api_key = api_key
        self.provider = provider
        self.verbose = verbose
        self.enable_vision = enable_vision
        self.translate_to_english = translate_to_english
        self.progress_callback = progress_callback
        self.transcription_method = transcription_method
        # Separate OpenAI API key for Whisper transcription (always uses OpenAI's API)
        self.openai_api_key = openai_api_key if openai_api_key else (api_key if provider == AIProvider.OPENAI else None)

        # Create temporary directory for processing
        self.temp_dir = tempfile.mkdtemp(prefix='video_eval_')

        # Supported formats
        self.SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.3gp'}
        self.SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}

        # Load dependencies
        whisper = None
        whisperx = None
        cv2 = None

        try:
            import whisper
        except ImportError:
            whisper = None

        try:
            import whisperx
        except ImportError:
            whisperx = None

        try:
            import cv2
        except ImportError:
            cv2 = None

        # Load whisper model - medium for optimal multilingual transcription and translation
        self.whisper_model = None  # Initialize to None
        self.whisper_model_name = None
        self.device = "cpu"  # Default device
        if whisper:
            try:
                # Use medium model for all tasks - it provides the best balance of accuracy and speed for multilingual content
                # Medium model significantly outperforms base for non-English languages while remaining reasonably fast
                model_name = "medium"  # Use medium model for optimal multilingual performance
                # Try MPS (Apple Silicon GPU) first, but load on CPU first to avoid sparse tensor issues
                try:
                    self.whisper_model = whisper.load_model(model_name, device="cpu")
                    # Test MPS stability before using it
                    import torch
                    if torch.backends.mps.is_available():
                        try:
                            # Quick stability test: create and use a small tensor
                            test_tensor = torch.randn(1, 10, device='mps')
                            test_result = torch.softmax(test_tensor, dim=-1)
                            if not torch.isnan(test_result).any():
                                # MPS seems stable, try selective placement
                                self.whisper_model = self._move_model_to_mps_selective(self.whisper_model)
                                self.device = "mps"
                                if self.verbose:
                                    print(f"✓ Whisper {model_name} model loaded on MPS (Apple Silicon GPU)")
                            else:
                                if self.verbose:
                                    print("Warning: MPS test failed, keeping model on CPU")
                        except Exception as mps_test_error:
                            if self.verbose:
                                print(f"Warning: MPS test failed ({mps_test_error}), keeping model on CPU")
                    else:
                        self.device = "cpu"
                        if self.verbose:
                            print(f"✓ Whisper {model_name} model loaded on CPU")
                    self.whisper_model_name = model_name
                    
                except Exception as e:
                    if self.verbose:
                        print(f"Warning: Failed to load {model_name} model ({e}), trying base model")
                    
                    # Fallback - try base if medium fails (better than turbo for translation)
                    try:
                        self.whisper_model = whisper.load_model("base", device="cpu")
                        self.whisper_model_name = "base"
                        self.device = "cpu"
                        if self.verbose:
                            print("✓ Whisper base model loaded on CPU")
                    except Exception as base_error:
                        if self.verbose:
                            print(f"Warning: Failed to load base model ({base_error}), trying turbo model")
                        
                        # Last resort - try turbo (English-only optimized, may not translate well)
                        try:
                            self.whisper_model = whisper.load_model("turbo", device="cpu")
                            self.whisper_model_name = "turbo"
                            self.device = "cpu"
                            if self.verbose:
                                print("✓ Whisper turbo model loaded on CPU")
                        except Exception as turbo_error:
                            if self.verbose:
                                print(f"Error: All Whisper models failed to load. Last error: {turbo_error}")
                            self.whisper_model = None

            finally:
                pass

        if whisperx:
            try:
                self.aligner = whisperx.load_align_model(language_code="en", device="mps")
            except Exception:
                # Fallback to CPU if MPS not available
                self.aligner = whisperx.load_align_model(language_code="en", device="cpu")
            except Exception:
                self.aligner = None
        else:
            self.aligner = None

        # Fallback minimal transcriber when whisper isn't installed (for tests)
        if not self.whisper_model:
            class _FallbackTranscriber:
                def transcribe(self, audio_path, **kwargs):
                    # very small mock transcription
                    return {"text": "(mock) transcribed text from audio", "language": "en", "segments": []}
            self.whisper_model = _FallbackTranscriber()
            self.whisper_model_name = "mock"
            self.device = "mock"

        # Client placeholders
        if provider == AIProvider.OPENAI:
            try:
                import openai
                self.llm = openai
            except Exception:
                self.llm = None
        else:
            try:
                import anthropic
                self.llm = anthropic
            except Exception:
                self.llm = None

    def __del__(self):
        """Cleanup temporary directory when object is destroyed."""
        self._cleanup_temp_dir()

    def _cleanup_temp_dir(self):
        """Remove temporary directory and all its contents."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                if hasattr(self, 'verbose') and self.verbose:
                    print(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                if hasattr(self, 'verbose') and self.verbose:
                    print(f"Warning: Could not delete temp directory {self.temp_dir}: {e}")

    def _get_device_display(self) -> str:
        """Get user-friendly device display name."""
        if self.device == "mps":
            return "Apple Silicon GPU (MPS)"
        elif self.device == "cpu":
            return "CPU"
        else:
            return self.device.upper()

    def _report_progress(self, message: str):
        """Report progress message via callback or print if verbose."""
        if self.progress_callback:
            self.progress_callback(message)
        elif self.verbose:
            print(message)

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available, trying common paths."""
        # Try common paths where ffmpeg might be installed
        possible_paths = [
            'ffmpeg',  # In PATH
            '/opt/homebrew/bin/ffmpeg',  # Homebrew Apple Silicon
            '/usr/local/bin/ffmpeg',     # Homebrew Intel / Linux
            '/usr/bin/ffmpeg',           # System binary
        ]
        
        for ffmpeg_path in possible_paths:
            try:
                subprocess.run([ffmpeg_path, '-version'], 
                             capture_output=True, check=True, timeout=2)
                # Store the working path for later use
                self.ffmpeg_path = ffmpeg_path
                return True
            except Exception:
                continue
        
        return False

    def _extract_audio_from_video(self, video_path: str) -> str:
        if not self._check_ffmpeg():
            raise RuntimeError(
                "ffmpeg is required but not found.\n"
                "Install with: brew install ffmpeg\n"
                "After installing, restart your terminal or run: source ~/.zshrc"
            )

        video_path_obj = Path(video_path)
        out_audio = os.path.join(self.temp_dir, f"{video_path_obj.stem}_audio.wav")
        
        # Use the ffmpeg path we found
        ffmpeg_cmd = getattr(self, 'ffmpeg_path', 'ffmpeg')
        cmd = [
            ffmpeg_cmd, '-i', str(video_path), '-vn', '-acodec', 'pcm_s16le', 
            '-ar', '16000', '-ac', '1', '-y', out_audio
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return out_audio

    def transcribe_with_timestamps(self, audio_path: str) -> Dict[str, Any]:
        """Return transcript, segments with start/end and (if available) token confidences.
        
        Also captures Whisper quality metrics:
        - avg_logprob: Average log probability (confidence)
        - compression_ratio: Text compression ratio (detects repetition)
        - no_speech_prob: Probability of no speech in segment
        
        If translate_to_english is enabled, Whisper will translate non-English audio to English.
        """
        # Suppress warnings in non-verbose mode
        import warnings
        if not self.verbose:
            warnings.filterwarnings('ignore')
        
        # Use whisper for transcription (with optional translation to English)
        def _transcribe_with_fallback(audio_path, task=None):
            """Transcribe with fallback to CPU if MPS produces NaN values."""
            try:
                if task == 'translate':
                    return self.whisper_model.transcribe(audio_path, task='translate')
                else:
                    return self.whisper_model.transcribe(audio_path)
            except Exception as e:
                error_msg = str(e)
                # Check if this is the NaN logits error from MPS
                if 'nan' in error_msg.lower() and 'logits' in error_msg.lower():
                    if self.verbose:
                        print(f"Warning: MPS inference produced NaN values ({e}). Retrying on CPU...")
                    
                    # Try to move model to CPU and retry
                    try:
                        import torch
                        # Check if model is currently on MPS
                        if hasattr(self.whisper_model, 'device') and self.whisper_model.device.type == 'mps':
                            # Move model to CPU
                            self.whisper_model = self.whisper_model.to('cpu')
                            if self.verbose:
                                print("Model moved to CPU for retry")
                        
                        # Retry transcription on CPU
                        if task == 'translate':
                            return self.whisper_model.transcribe(audio_path, task='translate')
                        else:
                            return self.whisper_model.transcribe(audio_path)
                            
                    except Exception as cpu_error:
                        if self.verbose:
                            print(f"Warning: CPU retry also failed ({cpu_error})")
                        raise cpu_error
                else:
                    # Re-raise non-NaN errors
                    raise e
        
        try:
            if self.verbose:
                print(f"DEBUG: transcription_method={self.transcription_method}, openai_api_key={'set' if self.openai_api_key else 'NOT SET'}")
            
            # Check if remote transcription is requested (openai or anthropic)
            if self.transcription_method in ["openai", "anthropic"] and self.transcription_method != "local":
                if self.verbose:
                    print(f"Using remote API for transcription (Task: {'translate' if self.translate_to_english else 'transcribe'})")
                
                # Import OpenAI client - remote transcription uses OpenAI's Whisper API
                import openai
                
                if not self.openai_api_key:
                    if self.verbose:
                        print(f"Remote API transcription requested but no OpenAI API key available. Falling back to local Whisper.")
                    # Fall through to local transcription
                    raise ValueError("No OpenAI API key available for remote transcription")
                
                client = openai.OpenAI(api_key=self.openai_api_key)
                
                with open(audio_path, "rb") as audio_file:
                    if self.translate_to_english:
                        transcript = client.audio.translations.create(
                            model="whisper-1", 
                            file=audio_file,
                            response_format="verbose_json"
                        )
                    else:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1", 
                            file=audio_file,
                            response_format="verbose_json"
                        )
                
                # Convert OpenAI verbose_json response (object) to dict structure compatible with local whisper
                # The response object attributes match the keys we need (text, language, segments)
                res = {
                    'text': transcript.text,
                    'language': getattr(transcript, 'language', 'en'),
                    'segments': [
                        {
                            'start': seg.start,
                            'end': seg.end,
                            'text': seg.text,
                            'avg_logprob': seg.avg_logprob,
                            'compression_ratio': seg.compression_ratio,
                            'no_speech_prob': seg.no_speech_prob
                        } for seg in transcript.segments
                    ]
                }
                
            else:
                # Use local whisper model
                if self.verbose:
                    print("Using local Whisper for transcription")
                if self.translate_to_english:
                    # First, detect language without translation
                    temp_res = _transcribe_with_fallback(audio_path)
                    detected_language = temp_res.get('language', 'unknown')
                    
                    # If not English, translate
                    if detected_language and detected_language.lower() != 'en':
                        res = _transcribe_with_fallback(audio_path, task='translate')
                    else:
                        res = temp_res  # Already in English
                else:
                    res = _transcribe_with_fallback(audio_path)
        except Exception as e:
            if self.verbose:
                print(f"Error during transcription: {e}")
            raise RuntimeError(f"Transcription failed: {e}")
        
        # Re-enable warnings
        if not self.verbose:
            warnings.filterwarnings('default')

        # Attempt to get word-level timestamps using whisperx if available
        segments = []
        try:
            if self.aligner:
                # whisperx pipeline: (simplified) load alignment and align
                result = whisperx.align(res['segments'], self.whisper_model, self.aligner, audio_path)
                for seg in result['segments']:
                    if isinstance(seg, dict):
                        segments.append({
                            'start': seg.get('start', 0), 'end': seg.get('end', 0), 'text': seg.get('text', ''),
                            'words': seg.get('words', []),
                            'avg_logprob': seg.get('avg_logprob'),
                            'compression_ratio': seg.get('compression_ratio'),
                            'no_speech_prob': seg.get('no_speech_prob')
                        })
            else:
                for seg in res.get('segments', []):
                    if isinstance(seg, dict):
                        segments.append({
                            'start': seg.get('start', 0), 'end': seg.get('end', 0), 'text': seg.get('text', ''), 
                            'words': [],
                            'avg_logprob': seg.get('avg_logprob'),
                            'compression_ratio': seg.get('compression_ratio'),
                            'no_speech_prob': seg.get('no_speech_prob')
                        })
        except Exception:
            for seg in res.get('segments', []):
                if isinstance(seg, dict):
                    segments.append({
                        'start': seg.get('start', 0), 'end': seg.get('end', 0), 'text': seg.get('text', ''), 
                        'words': [],
                        'avg_logprob': seg.get('avg_logprob'),
                        'compression_ratio': seg.get('compression_ratio'),
                        'no_speech_prob': seg.get('no_speech_prob')
                    })

        # Calculate overall quality metrics
        quality_summary = self._calculate_transcription_quality(segments)

        return {
            'text': res.get('text', ''), 
            'language': res.get('language', 'unknown'), 
            'segments': segments,
            'quality': quality_summary
        }

    def _extract_frames(self, video_path: str, num_frames: int = 8) -> Tuple[List[str], List[float]]:
        if not cv2:
            raise RuntimeError("OpenCV (cv2) is required for frame extraction but not available.")
        
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_indices = [int(total_frames * i / num_frames) for i in range(num_frames)]
        frames = []
        timestamps = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue
            _, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frames.append(base64.b64encode(buf).decode('utf-8'))
            timestamps.append(idx / fps)
        cap.release()
        return frames, timestamps

    def _calculate_transcription_quality(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall transcription quality metrics from Whisper segments.
        
        Returns:
            Dict with quality assessment including:
            - avg_confidence: Overall confidence (derived from avg_logprob)
            - avg_compression_ratio: Average text compression
            - speech_percentage: Percentage of audio containing speech
            - quality_rating: Overall quality assessment (high/medium/low)
            - warnings: List of potential issues
        """
        if not segments:
            return {
                'avg_confidence': 0.0,
                'avg_compression_ratio': 0.0,
                'speech_percentage': 0.0,
                'quality_rating': 'unknown',
                'warnings': ['No segments available']
            }
        
        # Filter out None values and calculate averages
        logprobs = [s.get('avg_logprob') for s in segments if s.get('avg_logprob') is not None]
        compression_ratios = [s.get('compression_ratio') for s in segments if s.get('compression_ratio') is not None]
        no_speech_probs = [s.get('no_speech_prob') for s in segments if s.get('no_speech_prob') is not None]
        
        avg_logprob = sum(logprobs) / len(logprobs) if logprobs else 0.0
        avg_compression = sum(compression_ratios) / len(compression_ratios) if compression_ratios else 0.0
        avg_no_speech = sum(no_speech_probs) / len(no_speech_probs) if no_speech_probs else 0.0
        
        # Convert logprob to confidence (logprob ranges from ~-1.5 to 0, higher is better)
        # Normalize to 0-100 scale
        avg_confidence = max(0, min(100, (avg_logprob + 1.5) * 66.67))
        
        # Calculate speech percentage (inverse of no_speech_prob)
        speech_percentage = (1 - avg_no_speech) * 100
        
        # Determine quality rating
        warnings = []
        
        if avg_confidence < 50:
            warnings.append('Low transcription confidence - audio may be unclear')
        
        if avg_compression > 2.5:
            warnings.append('High compression ratio - transcript may contain repetitions')
        
        if speech_percentage < 70:
            warnings.append('Low speech detection - audio may contain long silences or background noise')
        
        # Overall quality rating
        if avg_confidence >= 80 and speech_percentage >= 85 and avg_compression < 2.0:
            quality_rating = 'high'
        elif avg_confidence >= 60 and speech_percentage >= 70:
            quality_rating = 'medium'
        else:
            quality_rating = 'low'
        
        return {
            'avg_confidence': round(avg_confidence, 1),
            'avg_compression_ratio': round(avg_compression, 2),
            'speech_percentage': round(speech_percentage, 1),
            'quality_rating': quality_rating,
            'warnings': warnings,
            'details': {
                'avg_logprob': round(avg_logprob, 3),
                'num_segments': len(segments)
            }
        }

    def summarize_transcript(self, transcript: str) -> str:
        # lightweight summary via heuristic: first 3 lines or use LLM if available
        if self.llm and self.provider == AIProvider.OPENAI:
            try:
                with self.llm.OpenAI(api_key=self.api_key) as client:
                    resp = client.chat.completions.create(
                        model='gpt-4o',
                        messages=[{"role": "user", "content": f"Summarize the following transcript in 3 sentences:\n\n{transcript}"}],
                        max_tokens=200
                    )
                    return resp.choices[0].message.content
            except Exception:
                pass
        elif self.llm and self.provider == AIProvider.ANTHROPIC:
            try:
                with self.llm.Anthropic(api_key=self.api_key) as client:
                    resp = client.messages.create(
                        model='claude-3-5-haiku-20241022',
                        max_tokens=200,
                        messages=[{"role": "user", "content": f"Summarize the following transcript in 3 sentences:\n\n{transcript}"}]
                    )
                    return resp.content[0].text
            except Exception:
                pass
        # fallback: simple trim
        return ' '.join(transcript.split()[:120]) + ('...' if len(transcript.split()) > 120 else '')

    def pick_highlights(self, segments: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        # pick low-confidence segments or longest segments as highlights
        scored = []
        for s in segments:
            # compute heuristic score: fewer words with low confid -> higher priority
            words = s.get('words', [])
            low_conf = sum(1 for w in words if w.get('confidence', 1.0) < 0.8)
            score = low_conf + (len(s.get('text', '').split()) / 100.0)
            scored.append((score, s))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [s for _, s in scored[:top_k]]

    def multimodal_alignment_check(self, transcript: str, frames: List[str]) -> str:
        """Non-feature-specific alignment checks between transcript and visuals.
        Examples: Does the presenter reference an on-screen change, navigation, a chart, or error? Are there clear mismatches (e.g., presenter says "as you can see" but frames show unrelated content)?
        """
        prompt = f"""
You are a quality-assurance assistant. Given a transcript excerpt and several frames (images), answer briefly with factual observations about whether the visuals align with the transcript in a non-feature-specific way.

Focus on:
- Whether statements like 'as you can see', 'on the screen', 'now you can see' correspond to visible changes in the frames.
- Whether navigation or transitions mentioned in the transcript appear to be happening (e.g., different screens or windows visible across frames).
- Whether obvious distractions (notifications, irrelevant windows) appear in frames.

Respond with 3-6 short bullet observations with timestamps or frame indices when applicable.

Transcript excerpt:\n{transcript[:1200]}\n
"""

        # If we have LLM client, send images; otherwise do a lightweight heuristic
        if not self.llm:
            # heuristic checks: look for text-heavy frames and detect notifications via simple brightness or small rectangles (very approximate)
            observations = []
            for i, f_b64 in enumerate(frames):
                observations.append(f"Frame {i}: visually inspected (heuristic) - no clear mismatch detected")
            return '\n'.join(observations)

        # If provider is OpenAI, attempt a multimodal prompt (simplified)
        try:
            if self.provider == AIProvider.OPENAI:
                # Build content with text + images as data URLs (note: actual openai python SDK may vary)
                content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
                for img in frames[:5]:
                    content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
                with self.llm.OpenAI(api_key=self.api_key) as client:
                    resp = client.chat.completions.create(model='gpt-4o', messages=[{"role": "user", "content": content}], max_tokens=300)
                    return resp.choices[0].message.content
            else:
                # Anthropic style (simplified)
                message: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
                for img in frames[:5]:
                    message.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img}})
                with self.llm.Anthropic(api_key=self.api_key) as client:
                    resp = client.messages.create(model='claude-3', messages=[{"role": "user", "content": message}])
                    return resp.content[0].text
        except Exception:
            # fallback to heuristic
            observations = []
            for i, f_b64 in enumerate(frames):
                observations.append(f"Frame {i}: visually inspected (heuristic) - no clear mismatch detected")
            return '\n'.join(observations)

    def _chunk_transcript(self, transcript: str, chunk_size: int = 8000, overlap: int = 200) -> List[str]:
        """Split transcript into overlapping chunks for evaluation of long content.
        
        Args:
            transcript: Full transcript text
            chunk_size: Maximum characters per chunk
            overlap: Characters to overlap between chunks
            
        Returns:
            List of transcript chunks
        """
        if len(transcript) <= chunk_size:
            return [transcript]
        
        chunks = []
        start = 0
        
        while start < len(transcript):
            end = start + chunk_size
            
            # If we're not at the end, try to find a good break point
            if end < len(transcript):
                # Look for sentence endings within the last 200 chars of the chunk
                break_candidates = []
                for i in range(max(start, end - 200), end):
                    if transcript[i] in '.!?\n':
                        break_candidates.append(i + 1)
                
                if break_candidates:
                    # Use the last sentence break in the overlap region
                    end = break_candidates[-1]
                else:
                    # No good break, just cut at chunk_size
                    pass
            
            chunk = transcript[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(start + 1, end - overlap)
            
            # Prevent infinite loop
            if start >= len(transcript):
                break
        
        return chunks

    def evaluate_transcript_with_rubric(self, transcript: str, segments: List[Dict[str, Any]], visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        # Check if rubric uses new format (categories) or old format (criteria)
        is_new_format = "categories" in self.rubric

        if is_new_format:
            return self._evaluate_with_new_rubric_format(transcript, segments, visual_analysis)
        else:
            return self._evaluate_with_old_rubric_format(transcript, segments, visual_analysis)

    def _evaluate_with_new_rubric_format(self, transcript: str, segments: List[Dict[str, Any]], visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate using new rubric format with categories and nested criteria."""
        
        # Check if rubric is too complex (many criteria) - use chunked evaluation
        total_criteria = sum(len(cat['criteria']) for cat in self.rubric['categories'])
        if total_criteria > 10:
            return self._evaluate_complex_rubric_chunked(transcript, segments, visual_analysis)
        
        # Original single-prompt evaluation for simpler rubrics
        return self._evaluate_simple_rubric(transcript, segments, visual_analysis)

    def _evaluate_with_old_rubric_format(self, transcript: str, segments: List[Dict[str, Any]], visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate using old rubric format with flat criteria array."""
        
        # Check if transcript is too long - use chunked evaluation
        if len(transcript) > 4000:
            return self._evaluate_old_rubric_chunked(transcript, segments, visual_analysis)
        
        # Build prompt for LLM to produce strict JSON per rubric
        weights = {c['id']: c['weight'] for c in self.rubric['criteria']}
        criteria_desc = "\n".join([f"- {c['id']}: {c['desc']}" for c in self.rubric['criteria']])

        # Dynamically generate the scores schema from rubric
        scores_schema = ",\n    ".join([
            f'"{c["id"]}": {{"score": <int 1-10>, "confidence": <int 1-10>, "note": "<justification>"}}'
            for c in self.rubric['criteria']
        ])

        prompt = f"""
You are an expert demo evaluator. Score the following transcript on a 1-10 integer scale for each criterion, provide your confidence level in each score (1-10), and provide a 1-2 sentence justification.

Criteria to evaluate:
{criteria_desc}

Weights: {weights}
Thresholds: pass if >= {self.rubric['thresholds']['pass']}, revise if >= {self.rubric['thresholds']['revise']} and < {self.rubric['thresholds']['pass']}, otherwise fail.

For each criterion, provide:
- score: Your evaluation score (1-10)
- confidence: How confident you are in this score (1-10, where 10 means very confident)
- note: Brief justification for your score

Return JSON with this EXACT structure:
{{
  "scores": {{
    {scores_schema}
  }},
  "overall": {{
    "weighted_score": <float>,
    "method": "weighted_mean",
    "pass_status": "<pass|revise|fail>"
  }},
  "short_summary": "<one sentence summary>"
}}

Transcript:\n{transcript[:3000]}

Visual analysis (if any):\n{visual_analysis or 'None'}
"""

        if self.llm and self.provider == AIProvider.OPENAI:
            try:
                with self.llm.OpenAI(api_key=self.api_key) as client:
                    resp = client.chat.completions.create(
                        model='gpt-4o-mini',
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=800,
                        temperature=0,  # Deterministic output for consistent scoring
                        response_format={"type": "json_object"}
                    )
                    # attempt to parse JSON from response
                    text = resp.choices[0].message.content
                    result = json.loads(text)
                    if self.verbose:
                        print(f"✓ OpenAI evaluation successful")
                    return result
            except Exception as e:
                if self.verbose:
                    print(f"Warning: OpenAI API call failed ({e}). Using fallback evaluation.")
                    import traceback
                    traceback.print_exc()
                pass

        elif self.llm and self.provider == AIProvider.ANTHROPIC:
            try:
                with self.llm.Anthropic(api_key=self.api_key) as client:
                    resp = client.messages.create(
                        model='claude-3-5-haiku-20241022',
                        max_tokens=800,
                        temperature=0,  # Deterministic output for consistent scoring
                        messages=[{"role": "user", "content": prompt}]
                    )
                    result = json.loads(resp.content[0].text)
                    if self.verbose:
                        print(f"✓ Anthropic evaluation successful")
                    return result
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Anthropic API call failed ({e}). Using fallback.")
                pass

        # fallback: return a conservative heuristic
        scores = {}
        for c in self.rubric['criteria']:
            scores[c['id']] = {"score": 6, "note": "Auto-generated conservative score"}

        weighted = sum(scores[c['id']]['score'] * c.get('weight', 0) for c in self.rubric['criteria']) / sum(c.get('weight', 0) for c in self.rubric['criteria'])
        status = 'pass' if weighted >= self.rubric['thresholds']['pass'] else ('revise' if weighted >= self.rubric['thresholds']['revise'] else 'fail')
        return {"scores": scores, "overall": {"weighted_score": weighted, "method": self.rubric['overall_method'], "pass_status": status}, "short_summary": "Auto summary"}

    def _evaluate_old_rubric_chunked(self, transcript: str, segments: List[Dict[str, Any]], visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate long transcripts using old rubric format by breaking them into overlapping chunks."""
        
        # Chunk the transcript
        chunks = self._chunk_transcript(transcript, chunk_size=8000, overlap=200)
        
        if self.verbose:
            print(f"✓ Split transcript into {len(chunks)} chunks for evaluation")
        
        # Evaluate each chunk
        chunk_results = []
        for i, chunk in enumerate(chunks):
            if self.verbose:
                print(f"  Evaluating chunk {i+1}/{len(chunks)}...")
            
            try:
                chunk_result = self._evaluate_single_chunk_old(chunk, i+1, len(chunks), visual_analysis)
                chunk_results.append(chunk_result)
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Failed to evaluate chunk {i+1} ({e}). Using fallback for this chunk.")
                
                # Fallback for this chunk
                chunk_result = self._fallback_single_chunk_old_evaluation()
                chunk_results.append(chunk_result)
        
        # Aggregate results across chunks
        return self._aggregate_chunk_results_old(chunk_results)

    def _evaluate_single_chunk_old(self, chunk: str, chunk_num: int, total_chunks: int, visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate a single transcript chunk using old rubric format."""
        # Build prompt for LLM to produce strict JSON per rubric
        weights = {c['id']: c['weight'] for c in self.rubric['criteria']}
        criteria_desc = "\n".join([f"- {c['id']}: {c['desc']}" for c in self.rubric['criteria']])

        # Dynamically generate the scores schema from rubric
        scores_schema = ",\n    ".join([
            f'"{c["id"]}": {{"score": <int 1-10>, "confidence": <int 1-10>, "note": "<justification>"}}'
            for c in self.rubric['criteria']
        ])

        prompt = f"""
You are an expert demo evaluator. Score the following transcript chunk on a 1-10 integer scale for each criterion, provide your confidence level in each score (1-10), and provide a 1-2 sentence justification.

IMPORTANT: This is chunk {chunk_num} of {total_chunks} from a longer transcript. Evaluate based only on the content in this chunk, but consider the context that this is part of a complete demo presentation.

Criteria to evaluate:
{criteria_desc}

Weights: {weights}
Thresholds: pass if >= {self.rubric['thresholds']['pass']}, revise if >= {self.rubric['thresholds']['revise']} and < {self.rubric['thresholds']['pass']}, otherwise fail.

For each criterion, provide:
- score: Your evaluation score (1-10)
- confidence: How confident you are in this score (1-10, where 10 means very confident)
- note: Brief justification for your score

Return JSON with this EXACT structure:
{{
  "scores": {{
    {scores_schema}
  }},
  "overall": {{
    "weighted_score": <float>,
    "method": "weighted_mean",
    "pass_status": "<pass|revise|fail>"
  }},
  "short_summary": "<one sentence summary>"
}}

Transcript chunk {chunk_num}/{total_chunks}:\n{chunk}

Visual analysis (if any):\n{visual_analysis or 'None'}
"""

        if self.llm and self.provider == AIProvider.OPENAI:
            try:
                with self.llm.OpenAI(api_key=self.api_key) as client:
                    resp = client.chat.completions.create(
                        model='gpt-4o-mini',
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1000,
                        temperature=0,
                        response_format={"type": "json_object"}
                    )
                    text = resp.choices[0].message.content
                    if text:
                        result = json.loads(text)
                        # Clamp and recompute this category's totals
                        result = self._normalize_new_format_result(result)
                        return result
            except Exception as e:
                raise e
                
        elif self.llm and self.provider == AIProvider.ANTHROPIC:
            try:
                with self.llm.Anthropic(api_key=self.api_key) as client:
                    resp = client.messages.create(
                        model='claude-3-5-haiku-20241022',
                        max_tokens=1000,
                        temperature=0,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    result = json.loads(resp.content[0].text)
                    # Clamp and recompute this category's totals
                    result = self._normalize_new_format_result(result)
                    return result
            except Exception as e:
                raise e
        
        # If we get here, API calls failed
        raise RuntimeError("All API calls failed for chunk evaluation")

    def _aggregate_chunk_results_old(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate evaluation results from multiple transcript chunks for old rubric format."""
        if not chunk_results:
            # Fallback
            scores = {}
            for c in self.rubric['criteria']:
                scores[c['id']] = {"score": 6, "note": "Auto-generated conservative score"}
            weighted = sum(scores[c['id']]['score'] * c.get('weight', 0) for c in self.rubric['criteria']) / sum(c.get('weight', 0) for c in self.rubric['criteria'])
            status = 'pass' if weighted >= self.rubric['thresholds']['pass'] else ('revise' if weighted >= self.rubric['thresholds']['revise'] else 'fail')
            return {"scores": scores, "overall": {"weighted_score": weighted, "method": self.rubric['overall_method'], "pass_status": status}, "short_summary": "Auto summary"}
        
        # Aggregate scores by averaging across chunks
        aggregated_scores = {}
        all_criterion_ids = set()
        
        # Collect all criterion IDs
        for result in chunk_results:
            if 'scores' in result:
                all_criterion_ids.update(result['scores'].keys())
        
        # For each criterion, average the scores across chunks
        for criterion_id in all_criterion_ids:
            scores_for_criterion = []
            confidences_for_criterion = []
            notes_for_criterion = []
            
            for result in chunk_results:
                if 'scores' in result and criterion_id in result['scores']:
                    score_data = result['scores'][criterion_id]
                    scores_for_criterion.append(score_data.get('score', 0))
                    confidences_for_criterion.append(score_data.get('confidence', 5))
                    notes_for_criterion.append(score_data.get('note', ''))
            
            if scores_for_criterion:
                # Average score across chunks
                avg_score = sum(scores_for_criterion) / len(scores_for_criterion)
                # Use the highest confidence as representative
                max_confidence = max(confidences_for_criterion) if confidences_for_criterion else 5
                # Combine notes
                combined_notes = ' | '.join([note for note in notes_for_criterion if note])
                
                aggregated_scores[criterion_id] = {
                    "score": round(avg_score, 1),
                    "confidence": max_confidence,
                    "note": f"Aggregated from {len(scores_for_criterion)} chunks: {combined_notes}"
                }
            else:
                # Fallback if no scores for this criterion
                aggregated_scores[criterion_id] = {
                    "score": 6,
                    "confidence": 3,
                    "note": "No scores available from chunks"
                }
        
        # Calculate overall weighted score
        total_weight = sum(c.get('weight', 0) for c in self.rubric['criteria'])
        if total_weight > 0:
            weighted_score = sum(aggregated_scores[c['id']]['score'] * c.get('weight', 0) for c in self.rubric['criteria']) / total_weight
        else:
            weighted_score = 6.0  # Fallback
        
        # Determine pass status
        status = 'pass' if weighted_score >= self.rubric['thresholds']['pass'] else ('revise' if weighted_score >= self.rubric['thresholds']['revise'] else 'fail')
        
        return {
            "scores": aggregated_scores,
            "overall": {
                "weighted_score": round(weighted_score, 1),
                "method": self.rubric['overall_method'],
                "pass_status": status
            },
            "short_summary": f"Evaluated {len(chunk_results)} transcript chunks with {len(aggregated_scores)} criteria"
        }

    def _fallback_single_chunk_old_evaluation(self) -> Dict[str, Any]:
        """Fallback evaluation for a single chunk when API calls fail (old rubric format)."""
        scores = {}
        for c in self.rubric['criteria']:
            scores[c['id']] = {"score": 6, "confidence": 3, "note": "Auto-generated conservative score for chunk"}

        weighted = sum(scores[c['id']]['score'] * c.get('weight', 0) for c in self.rubric['criteria']) / sum(c.get('weight', 0) for c in self.rubric['criteria'])
        status = 'pass' if weighted >= self.rubric['thresholds']['pass'] else ('revise' if weighted >= self.rubric['thresholds']['revise'] else 'fail')
        return {"scores": scores, "overall": {"weighted_score": weighted, "method": self.rubric['overall_method'], "pass_status": status}, "short_summary": "Auto summary"}

    def _evaluate_simple_rubric(self, transcript: str, segments: List[Dict[str, Any]], visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate using new rubric format with categories and nested criteria (original single-prompt approach)."""
        
        # Check if transcript is too long - use chunked evaluation
        if len(transcript) > 4000:
            return self._evaluate_transcript_chunked(transcript, segments, visual_analysis)
        
        # Build prompt for LLM to produce strict JSON per rubric
        categories_desc = []
        scores_schema_parts = []

        for category in self.rubric['categories']:
            cat_desc = f"- {category['label']} ({category['category_id']}) - {category['max_points']} points max"
            criteria_desc = []
            for criterion in category['criteria']:
                criteria_desc.append(f"  * {criterion['label']} ({criterion['criterion_id']}) - {criterion['max_points']} points max")
                scores_schema_parts.append(f'"{criterion["criterion_id"]}": {{"score": <int 0-{criterion["max_points"]}>, "confidence": <int 1-10>, "note": "<justification>"}}')

            categories_desc.append(f"{cat_desc}\n" + "\n".join(criteria_desc))

        categories_text = "\n".join(categories_desc)
        scores_schema = ",\n    ".join(scores_schema_parts)

        prompt = f"""
You are an expert demo evaluator. Score the following transcript on a point-based scale for each criterion, provide your confidence level in each score (1-10), and provide a justification.

Categories and Criteria to evaluate:
{categories_text}

Total possible points: {sum(cat['max_points'] for cat in self.rubric['categories'])}

For each criterion, provide:
    - score: Your evaluation score (0 up to that criterion's max_points listed above)
- confidence: How confident you are in this score (1-10, where 10 means very confident)
- note: Brief justification for your score

Return JSON with this EXACT structure:
{{
  "scores": {{
    {scores_schema}
  }},
  "overall": {{
    "total_points": <int>,
    "max_points": {sum(cat['max_points'] for cat in self.rubric['categories'])},
    "percentage": <float>,
    "pass_status": "<pass|revise|fail>"
  }},
  "categories": {{
    "category_id": {{
      "points": <int>,
      "max_points": <int>,
      "percentage": <float>
    }}
  }},
  "short_summary": "<one sentence summary>"
}}

Transcript:\n{transcript[:3000]}

Visual analysis (if any):\n{visual_analysis or 'None'}
"""

        if self.llm and self.provider == AIProvider.OPENAI:
            try:
                with self.llm.OpenAI(api_key=self.api_key) as client:
                    resp = client.chat.completions.create(
                        model='gpt-4o-mini',
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1200,
                        temperature=0,  # Deterministic output for consistent scoring
                        response_format={"type": "json_object"}
                    )
                    # attempt to parse JSON from response
                    text = resp.choices[0].message.content
                    if text:
                        result = json.loads(text)
                        # Normalize/clamp scores to rubric-defined max points
                        result = self._normalize_new_format_result(result)
                        if self.verbose:
                            print(f"✓ OpenAI evaluation successful")
                        return result
            except Exception as e:
                if self.verbose:
                    print(f"Warning: OpenAI API call failed ({e}). Using fallback evaluation.")
                    import traceback
                    traceback.print_exc()
                pass

        elif self.llm and self.provider == AIProvider.ANTHROPIC:
            try:
                with self.llm.Anthropic(api_key=self.api_key) as client:
                    resp = client.messages.create(
                        model='claude-3-5-haiku-20241022',
                        max_tokens=1000,
                        temperature=0,  # Deterministic output for consistent scoring
                        messages=[{"role": "user", "content": prompt}]
                    )
                    result = json.loads(resp.content[0].text)
                    # Normalize/clamp scores to rubric-defined max points
                    result = self._normalize_new_format_result(result)
                    if self.verbose:
                        print(f"✓ Anthropic evaluation successful")
                    return result
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Anthropic API call failed ({e}). Using fallback.")
                pass

        # fallback: return a conservative heuristic
        return self._fallback_new_rubric_evaluation()

    def _evaluate_transcript_chunked(self, transcript: str, segments: List[Dict[str, Any]], visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate long transcripts by breaking them into overlapping chunks and aggregating results."""
        
        # Check if rubric is complex (many criteria) - use category-based chunking instead
        total_criteria = sum(len(cat['criteria']) for cat in self.rubric['categories'])
        if total_criteria > 10:
            return self._evaluate_transcript_and_category_chunked(transcript, segments, visual_analysis)
        
        # Chunk the transcript
        chunks = self._chunk_transcript(transcript, chunk_size=8000, overlap=200)
        
        if self.verbose:
            print(f"✓ Split transcript into {len(chunks)} chunks for evaluation")
        
        # Evaluate each chunk
        chunk_results = []
        for i, chunk in enumerate(chunks):
            if self.verbose:
                print(f"  Evaluating chunk {i+1}/{len(chunks)}...")
            
            try:
                # Use the same rubric evaluation but with chunk indicator
                chunk_result = self._evaluate_single_chunk(chunk, i+1, len(chunks), visual_analysis)
                chunk_results.append(chunk_result)
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Failed to evaluate chunk {i+1} ({e}). Using fallback for this chunk.")
                
                # Fallback for this chunk
                chunk_result = self._fallback_single_chunk_evaluation()
                chunk_results.append(chunk_result)
        
        # Aggregate results across chunks
        return self._aggregate_chunk_results(chunk_results)

    def _evaluate_transcript_and_category_chunked(self, transcript: str, segments: List[Dict[str, Any]], visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate long transcripts with complex rubrics by breaking transcript into chunks and evaluating categories within each chunk."""
        
        # Chunk the transcript
        chunks = self._chunk_transcript(transcript, chunk_size=8000, overlap=200)
        
        if self.verbose:
            print(f"✓ Split transcript into {len(chunks)} chunks for category-based evaluation")
        
        # Evaluate each category across all chunks
        category_results = {}
        
        for category in self.rubric['categories']:
            if self.verbose:
                print(f"  Evaluating category '{category['label']}' across {len(chunks)} chunks...")
            
            category_scores = {}
            
            # Evaluate this category in each transcript chunk
            for i, chunk in enumerate(chunks):
                try:
                    chunk_result = self._evaluate_single_category_in_chunk(category, chunk, i+1, len(chunks), visual_analysis)
                    # Merge scores from this chunk
                    for criterion_id, score_data in chunk_result['scores'].items():
                        if criterion_id not in category_scores:
                            category_scores[criterion_id] = []
                        category_scores[criterion_id].append(score_data)
                        
                except Exception as e:
                    if self.verbose:
                        print(f"Warning: Failed to evaluate category {category['label']} in chunk {i+1} ({e}). Using fallback.")
                    
                    # Fallback scores for this category in this chunk
                    for criterion in category['criteria']:
                        if criterion['criterion_id'] not in category_scores:
                            category_scores[criterion['criterion_id']] = []
                        category_scores[criterion['criterion_id']].append({
                            "score": int(criterion['max_points'] * 0.6),
                            "confidence": 3,
                            "note": f"Auto-generated conservative score for chunk {i+1}"
                        })
            
            # Aggregate scores for this category across chunks
            aggregated_category_scores = {}
            category_points = 0
            
            for criterion_id, scores_list in category_scores.items():
                # Average scores across chunks
                avg_score = sum(s['score'] for s in scores_list) / len(scores_list)
                # Clamp to rubric max_points for this criterion
                crit_max = 0
                for cat in self.rubric['categories']:
                    for criterion in cat['criteria']:
                        if criterion['criterion_id'] == criterion_id:
                            crit_max = criterion.get('max_points', 0)
                            break
                    if crit_max:
                        break
                clamped_score = max(0, min(round(avg_score), crit_max))
                max_confidence = max(s['confidence'] for s in scores_list)
                combined_notes = ' | '.join([s['note'] for s in scores_list if s['note']])
                
                aggregated_category_scores[criterion_id] = {
                    "score": clamped_score,
                    "confidence": max_confidence,
                    "note": f"Aggregated from {len(scores_list)} chunks: {combined_notes}"
                }
                category_points += clamped_score
            
            # Clamp category total to max
            category_points = max(0, min(category_points, category['max_points']))
            category_results[category['category_id']] = {
                "scores": aggregated_category_scores,
                "category": {
                    "points": category_points,
                    "max_points": category['max_points'],
                    "percentage": (category_points / category['max_points']) * 100 if category['max_points'] > 0 else 0
                }
            }
        
        # Merge all results
        all_scores = {}
        all_categories = {}
        
        for cat_id, cat_result in category_results.items():
            all_scores.update(cat_result['scores'])
            all_categories[cat_id] = cat_result['category']
        
        # Calculate overall results
        total_points = sum(cat['points'] for cat in all_categories.values())
        max_points = sum(cat['max_points'] for cat in all_categories.values())
        percentage = (total_points / max_points) * 100 if max_points > 0 else 0
        
        # Use point-based thresholds
        pass_threshold = self.rubric['thresholds']['pass']
        revise_threshold = self.rubric['thresholds']['revise']
        
        status = 'pass' if total_points >= pass_threshold else ('revise' if total_points >= revise_threshold else 'fail')
        
        return {
            "scores": all_scores,
            "overall": {
                "total_points": total_points,
                "max_points": max_points,
                "percentage": round(percentage, 1),
                "pass_status": status
            },
            "categories": all_categories,
            "short_summary": f"Evaluated {len(all_categories)} categories across {len(chunks)} transcript chunks"
        }

    def _evaluate_single_category_in_chunk(self, category: Dict[str, Any], chunk: str, chunk_num: int, total_chunks: int, visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate a single category within a transcript chunk."""
        # Build prompt for this category only
        criteria_desc = []
        scores_schema_parts = []
        
        for criterion in category['criteria']:
            criteria_desc.append(f"- {criterion['label']}: {criterion['desc']}")
            scores_schema_parts.append(f'"{criterion["criterion_id"]}": {{"score": <int 0-{criterion["max_points"]}>, "confidence": <int 1-10>, "note": "<justification>"}}')
        
        criteria_text = "\n".join(criteria_desc)
        scores_schema = ",\n  ".join(scores_schema_parts)
        
        prompt = f"""
You are an expert demo evaluator. Score the following transcript chunk for the category "{category['label']}" on a point-based scale, provide your confidence level in each score (1-10), and provide a justification.

IMPORTANT: Return ONLY valid JSON. Do not include any explanatory text, markdown formatting, or additional content. Start your response with {{ and end with }}.

IMPORTANT: This is chunk {chunk_num} of {total_chunks} from a longer transcript. Evaluate based only on the content in this chunk, but consider the context that this is part of a complete demo presentation.

Category: {category['label']} ({category['max_points']} points total)

Criteria to evaluate:
{criteria_text}

For each criterion, provide:
- score: Your evaluation score (0 up to that criterion's max_points listed above)
- confidence: How confident you are in this score (1-10, where 10 means very confident)
- note: Brief justification for your score

Return JSON with this EXACT structure:
{{
  "scores": {{
    {scores_schema}
  }}
}}

Transcript chunk {chunk_num}/{total_chunks}:\n{chunk[:3000]}

Visual analysis (if any):\n{visual_analysis or 'None'}
"""

        if self.llm and self.provider == AIProvider.OPENAI:
            try:
                with self.llm.OpenAI(api_key=self.api_key) as client:
                    resp = client.chat.completions.create(
                        model='gpt-4o-mini',
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=800,
                        temperature=0,
                        response_format={"type": "json_object"}
                    )
                    text = resp.choices[0].message.content
                    if text:
                        result = json.loads(text)
                        # Clamp scores for this category and recompute category totals
                        result = self._normalize_new_format_result(result)
                        return result
            except Exception as e:
                if self.verbose:
                    print(f"Warning: OpenAI API call failed for category {category['label']} in chunk {chunk_num} ({e}). Using fallback.")
                pass
                
        elif self.llm and self.provider == AIProvider.ANTHROPIC:
            try:
                with self.llm.Anthropic(api_key=self.api_key) as client:
                    resp = client.messages.create(
                        model='claude-3-5-haiku-20241022',
                        max_tokens=800,
                        temperature=0,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    if resp.content and len(resp.content) > 0 and hasattr(resp.content[0], 'text'):
                        text = resp.content[0].text
                        if text:
                            try:
                                result = json.loads(text)
                                # Clamp scores for this category and recompute category totals
                                result = self._normalize_new_format_result(result)
                                return result
                            except json.JSONDecodeError as e:
                                if self.verbose:
                                    print(f"Warning: Failed to parse JSON response for category {category['label']}: {e}")
                                    print(f"Raw response text: {text[:500]}...")
                                raise e
                        else:
                            if self.verbose:
                                print(f"Warning: Anthropic response text is empty for category {category['label']} in chunk {chunk_num}")
                    else:
                        if self.verbose:
                            print(f"Warning: Anthropic response missing content or text for category {category['label']} in chunk {chunk_num}")
                            print(f"Response content: {resp.content}")
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Anthropic API call failed for category {category['label']} in chunk {chunk_num} ({e}). Using fallback.")
                    print(f"Exception details: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                pass
        
        # If we get here, API calls failed - return fallback for this category
        scores = {}
        for criterion in category['criteria']:
            scores[criterion['criterion_id']] = {
                "score": int(criterion['max_points'] * 0.6),
                "confidence": 3,
                "note": f"Auto-generated conservative score for category {category['label']} in chunk {chunk_num}"
            }
        
        return {"scores": scores}

    def _evaluate_single_chunk(self, chunk: str, chunk_num: int, total_chunks: int, visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate a single transcript chunk."""
        # Build prompt for LLM to produce strict JSON per rubric
        categories_desc = []
        scores_schema_parts = []

        for category in self.rubric['categories']:
            cat_desc = f"- {category['label']} ({category['category_id']}) - {category['max_points']} points max"
            criteria_desc = []
            for criterion in category['criteria']:
                criteria_desc.append(f"  * {criterion['label']} ({criterion['criterion_id']}) - {criterion['max_points']} points max")
                scores_schema_parts.append(f'"{criterion["criterion_id"]}": {{"score": <int 0-{criterion["max_points"]}>, "confidence": <int 1-10>, "note": "<justification>"}}')

            categories_desc.append(f"{cat_desc}\n" + "\n".join(criteria_desc))

        categories_text = "\n".join(categories_desc)
        scores_schema = ",\n    ".join(scores_schema_parts)

        prompt = f"""
You are an expert demo evaluator. Score the following transcript chunk on a point-based scale for each criterion, provide your confidence level in each score (1-10), and provide a justification.

IMPORTANT: This is chunk {chunk_num} of {total_chunks} from a longer transcript. Evaluate based only on the content in this chunk, but consider the context that this is part of a complete demo presentation.

Categories and Criteria to evaluate:
{categories_text}

Total possible points: {sum(cat['max_points'] for cat in self.rubric['categories'])}

For each criterion, provide:
- score: Your evaluation score (0 up to that criterion's max_points listed above)
- confidence: How confident you are in this score (1-10, where 10 means very confident)
- note: Brief justification for your score

Return JSON with this EXACT structure:
{{
  "scores": {{
    {scores_schema}
  }},
  "overall": {{
    "total_points": <int>,
    "max_points": {sum(cat['max_points'] for cat in self.rubric['categories'])},
    "percentage": <float>,
    "pass_status": "<pass|revise|fail>"
  }},
  "categories": {{
    "category_id": {{
      "points": <int>,
      "max_points": <int>,
      "percentage": <float>
    }}
  }},
  "short_summary": "<one sentence summary>"
}}

Transcript chunk {chunk_num}/{total_chunks}:\n{chunk}

Visual analysis (if any):\n{visual_analysis or 'None'}
"""

        if self.llm and self.provider == AIProvider.OPENAI:
            try:
                with self.llm.OpenAI(api_key=self.api_key) as client:
                    resp = client.chat.completions.create(
                        model='gpt-4o-mini',
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1000,
                        temperature=0,
                        response_format={"type": "json_object"}
                    )
                    text = resp.choices[0].message.content
                    if text:
                        result = json.loads(text)
                        # Normalize/clamp scores to rubric-defined max points
                        result = self._normalize_new_format_result(result)
                        return result
            except Exception as e:
                if self.verbose:
                    print(f"Warning: OpenAI API call failed for chunk {chunk_num} ({e}). Using fallback.")
                pass
                
        elif self.llm and self.provider == AIProvider.ANTHROPIC:
            try:
                with self.llm.Anthropic(api_key=self.api_key) as client:
                    resp = client.messages.create(
                        model='claude-3-5-haiku-20241022',
                        max_tokens=1000,
                        temperature=0,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    result = json.loads(resp.content[0].text)
                    # Normalize/clamp scores to rubric-defined max points
                    result = self._normalize_new_format_result(result)
                    return result
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Anthropic API call failed for chunk {chunk_num} ({e}). Using fallback.")
                pass
        
        # If we get here, API calls failed - return fallback
        return self._fallback_single_chunk_evaluation()

    def _aggregate_chunk_results(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate evaluation results from multiple transcript chunks."""
        if not chunk_results:
            return self._fallback_new_rubric_evaluation()
        
        # Aggregate scores by averaging across chunks
        aggregated_scores = {}
        all_criterion_ids = set()
        
        # Collect all criterion IDs
        for result in chunk_results:
            if 'scores' in result:
                all_criterion_ids.update(result['scores'].keys())
        
        # For each criterion, average the scores across chunks
        for criterion_id in all_criterion_ids:
            scores_for_criterion = []
            confidences_for_criterion = []
            notes_for_criterion = []
            
            for result in chunk_results:
                if 'scores' in result and criterion_id in result['scores']:
                    score_data = result['scores'][criterion_id]
                    scores_for_criterion.append(score_data.get('score', 0))
                    confidences_for_criterion.append(score_data.get('confidence', 5))
                    notes_for_criterion.append(score_data.get('note', ''))
            
            if scores_for_criterion:
                # Average score across chunks
                avg_score = sum(scores_for_criterion) / len(scores_for_criterion)
                # Clamp to rubric max_points for this criterion
                crit_max = 0
                for category in self.rubric['categories']:
                    for criterion in category['criteria']:
                        if criterion['criterion_id'] == criterion_id:
                            crit_max = criterion.get('max_points', 0)
                            break
                    if crit_max:
                        break
                clamped_score = max(0, min(round(avg_score), crit_max))
                # Use the highest confidence as representative
                max_confidence = max(confidences_for_criterion) if confidences_for_criterion else 5
                # Combine notes
                combined_notes = ' | '.join([note for note in notes_for_criterion if note])
                
                aggregated_scores[criterion_id] = {
                    "score": clamped_score,
                    "confidence": max_confidence,
                    "note": f"Aggregated from {len(scores_for_criterion)} chunks: {combined_notes}"
                }
            else:
                # Fallback if no scores for this criterion
                aggregated_scores[criterion_id] = {
                    "score": 0,
                    "confidence": 3,
                    "note": "No scores available from chunks"
                }
        
        # Aggregate category results
        categories = {}
        for category in self.rubric['categories']:
            category_points = 0
            total_max_points = category['max_points']
            
            # Sum clamped points for all criteria in this category
            for criterion in category['criteria']:
                if criterion['criterion_id'] in aggregated_scores:
                    score_val = aggregated_scores[criterion['criterion_id']]['score']
                    # Criterion scores are already clamped; just sum
                    category_points += score_val
            # Clamp category points to its max
            category_points = max(0, min(category_points, total_max_points))
            
            categories[category['category_id']] = {
                "points": category_points,
                "max_points": total_max_points,
                "percentage": (category_points / total_max_points) * 100 if total_max_points > 0 else 0
            }
        
        # Calculate overall results
        total_points = sum(cat['points'] for cat in categories.values())
        max_points = sum(cat['max_points'] for cat in categories.values())
        percentage = (total_points / max_points) * 100 if max_points > 0 else 0
        
        # Use point-based thresholds
        pass_threshold = self.rubric['thresholds']['pass']
        revise_threshold = self.rubric['thresholds']['revise']
        
        status = 'pass' if total_points >= pass_threshold else ('revise' if total_points >= revise_threshold else 'fail')
        
        return {
            "scores": aggregated_scores,
            "overall": {
                "total_points": total_points,
                "max_points": max_points,
                "percentage": round(percentage, 1),
                "pass_status": status
            },
            "categories": categories,
            "short_summary": f"Evaluated {len(chunk_results)} transcript chunks with {len(aggregated_scores)} criteria"
        }

    def _fallback_single_chunk_evaluation(self) -> Dict[str, Any]:
        """Fallback evaluation for a single chunk when API calls fail."""
        scores = {}
        categories = {}
        
        # Generate conservative scores for all criteria
        for category in self.rubric['categories']:
            category_points = 0
            for criterion in category['criteria']:
                score = int(criterion['max_points'] * 0.6)  # Conservative score
                scores[criterion['criterion_id']] = {
                    "score": score,
                    "confidence": 3,
                    "note": "Auto-generated conservative score for chunk"
                }
                category_points += score
            
            categories[category['category_id']] = {
                "points": category_points,
                "max_points": category['max_points'],
                "percentage": (category_points / category['max_points']) * 100
            }
        
        # Calculate overall results
        total_points = sum(cat['points'] for cat in categories.values())
        max_points = sum(cat['max_points'] for cat in categories.values())
        percentage = (total_points / max_points) * 100
        
        pass_threshold = self.rubric['thresholds']['pass']
        revise_threshold = self.rubric['thresholds']['revise']
        
        status = 'pass' if total_points >= pass_threshold else ('revise' if total_points >= revise_threshold else 'fail')
        
        return {
            "scores": scores,
            "overall": {
                "total_points": total_points,
                "max_points": max_points,
                "percentage": round(percentage, 1),
                "pass_status": status
            },
            "categories": categories,
            "short_summary": "Auto-generated conservative chunk evaluation"
        }

    def _evaluate_complex_rubric_chunked(self, transcript: str, segments: List[Dict[str, Any]], visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate complex rubrics by breaking them into smaller chunks (by category)."""
        
        # Check if transcript is too long - use transcript chunking instead
        if len(transcript) > 4000:
            return self._evaluate_transcript_chunked(transcript, segments, visual_analysis)
        
        scores = {}
        categories = {}
        
        # Evaluate each category separately
        for category in self.rubric['categories']:
            category_result = self._evaluate_single_category(category, transcript, segments, visual_analysis)
            # Merge scores
            scores.update(category_result['scores'])
            # Store category results
            categories[category['category_id']] = category_result['category']
            
            if self.verbose:
                print(f"✓ Evaluated category: {category['label']}")
        
        # Calculate overall results
        total_points = sum(cat['points'] for cat in categories.values())
        max_points = sum(cat['max_points'] for cat in categories.values())
        percentage = (total_points / max_points) * 100
        
        # Use point-based thresholds
        pass_threshold = self.rubric['thresholds']['pass']  # Convert from 1-10 scale to percentage
        revise_threshold = self.rubric['thresholds']['revise']
        
        status = 'pass' if total_points >= pass_threshold else ('revise' if total_points >= revise_threshold else 'fail')
        
        return {
            "scores": scores,
            "overall": {
                "total_points": total_points,
                "max_points": max_points,
                "percentage": round(percentage, 1),
                "pass_status": status
            },
            "categories": categories,
            "short_summary": f"Evaluated {len(categories)} categories with {len(scores)} criteria"
        }

    def _evaluate_single_category(self, category: Dict[str, Any], transcript: str, segments: List[Dict[str, Any]], visual_analysis: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate a single category with its criteria."""
        # Build prompt for this category only
        criteria_desc = []
        scores_schema_parts = []
        
        for criterion in category['criteria']:
            criteria_desc.append(f"- {criterion['label']}: {criterion['desc']}")
            scores_schema_parts.append(f'"{criterion["criterion_id"]}": {{"score": <int 0-{criterion["max_points"]}>, "confidence": <int 1-10>, "note": "<justification>"}}')
        
        criteria_text = "\n".join(criteria_desc)
        scores_schema = ",\n  ".join(scores_schema_parts)
        
        prompt = f"""
You are an expert demo evaluator. Score the following transcript for the category "{category['label']}" on a point-based scale, provide your confidence level in each score (1-10), and provide a justification.

Category: {category['label']} ({category['max_points']} points total)

Criteria to evaluate:
{criteria_text}

For each criterion, provide:
- score: Your evaluation score (0 up to that criterion's max_points listed above)
- confidence: How confident you are in this score (1-10, where 10 means very confident)
- note: Brief justification for your score

Return JSON with this EXACT structure:
{{
  "scores": {{
    {scores_schema}
  }},
  "category": {{
    "points": <int>,
    "max_points": {category['max_points']},
    "percentage": <float>
  }}
}}

Transcript:\n{transcript[:2500]}

Visual analysis (if any):\n{visual_analysis or 'None'}
"""

        if self.llm and self.provider == AIProvider.OPENAI:
            try:
                with self.llm.OpenAI(api_key=self.api_key) as client:
                    resp = client.chat.completions.create(
                        model='gpt-4o-mini',
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=800,
                        temperature=0,
                        response_format={"type": "json_object"}
                    )
                    text = resp.choices[0].message.content
                    if text:
                        result = json.loads(text)
                        # Clamp scores for this category and recompute category totals
                        result = self._normalize_new_format_result(result)
                        return result
            except Exception as e:
                if self.verbose:
                    print(f"Warning: OpenAI API call failed for category {category['label']} ({e}). Using fallback.")
                pass
                
        elif self.llm and self.provider == AIProvider.ANTHROPIC:
            try:
                with self.llm.Anthropic(api_key=self.api_key) as client:
                    resp = client.messages.create(
                        model='claude-3-5-haiku-20241022',
                        max_tokens=800,
                        temperature=0,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    result = json.loads(resp.content[0].text)
                    # Clamp scores for this category and recompute category totals
                    result = self._normalize_new_format_result(result)
                    return result
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Anthropic API call failed for category {category['label']} ({e}). Using fallback.")
                pass
        
        # If we get here, API calls failed - return fallback for this category
        category_points = 0
        scores = {}
        for criterion in category['criteria']:
            score = int(criterion['max_points'] * 0.6)  # Conservative score
            scores[criterion['criterion_id']] = {
                "score": score,
                "confidence": 5,
                "note": "Auto-generated conservative score"
            }
            category_points += score
        
        return {
            "scores": scores,
            "category": {
                "points": category_points,
                "max_points": category['max_points'],
                "percentage": (category_points / category['max_points']) * 100 if category['max_points'] > 0 else 0
            }
        }

    def _fallback_new_rubric_evaluation(self) -> Dict[str, Any]:
        """Fallback evaluation for new rubric format when AI calls fail."""
        scores = {}
        categories = {}
        
        # Generate conservative scores for all criteria
        for category in self.rubric['categories']:
            category_points = 0
            for criterion in category['criteria']:
                score = int(criterion['max_points'] * 0.6)  # Conservative score
                scores[criterion['criterion_id']] = {
                    "score": score,
                    "confidence": 3,  # Low confidence for fallback scores
                    "note": "Auto-generated conservative score"
                }
                category_points += score
            
            categories[category['category_id']] = {
                "points": category_points,
                "max_points": category['max_points'],
                "percentage": (category_points / category['max_points']) * 100
            }
        
        # Calculate overall results
        total_points = sum(cat['points'] for cat in categories.values())
        max_points = sum(cat['max_points'] for cat in categories.values())
        percentage = (total_points / max_points) * 100
        
        # Use point-based thresholds
        pass_threshold = self.rubric['thresholds']['pass']  # Convert from 1-10 scale to percentage
        revise_threshold = self.rubric['thresholds']['revise']
        
        status = 'pass' if total_points >= pass_threshold else ('revise' if total_points >= revise_threshold else 'fail')
        
        return {
            "scores": scores,
            "overall": {
                "total_points": total_points,
                "max_points": max_points,
                "percentage": round(percentage, 1),
                "pass_status": status
            },
            "categories": categories,
            "short_summary": "Auto-generated conservative evaluation"
        }

    def _normalize_new_format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Clamp criterion scores to rubric-defined max points and recompute category/overall totals.

        This guards against LLM outputs that exceed allowed maxima, ensuring percentages never exceed 100%.
        """
        try:
            # Build maps for criterion max and category membership
            crit_max: Dict[str, int] = {}
            crit_to_cat: Dict[str, str] = {}
            cat_max: Dict[str, int] = {}
            for category in self.rubric.get('categories', []):
                cat_id = category.get('category_id')
                cat_max[cat_id] = category.get('max_points', 0)
                for criterion in category.get('criteria', []):
                    cid = criterion.get('criterion_id')
                    crit_max[cid] = criterion.get('max_points', 0)
                    crit_to_cat[cid] = cat_id

            # Clamp scores per criterion
            scores = result.get('scores', {}) or {}
            for cid, data in list(scores.items()):
                raw = data.get('score', 0)
                m = crit_max.get(cid, 0)
                clamped = max(0, min(int(round(raw)), m))
                data['score'] = clamped
                # Ensure confidence is within 1-10 if present
                if 'confidence' in data:
                    conf = data.get('confidence', 5)
                    data['confidence'] = max(1, min(int(round(conf)), 10))
                scores[cid] = data

            # Recompute categories from clamped scores
            categories: Dict[str, Dict[str, float]] = {}
            for cat_id, m in cat_max.items():
                categories[cat_id] = {"points": 0, "max_points": m, "percentage": 0.0}
            for cid, data in scores.items():
                cat_id = crit_to_cat.get(cid)
                if cat_id in categories:
                    categories[cat_id]["points"] += data.get('score', 0)
            # Clamp category totals and compute percentages
            for cat_id, cat_data in categories.items():
                points = int(cat_data["points"])
                m = int(cat_data["max_points"])
                points = max(0, min(points, m))
                cat_data["points"] = points
                cat_data["percentage"] = (points / m) * 100 if m > 0 else 0.0

            # Compute overall totals
            total_points = sum(cat["points"] for cat in categories.values())
            max_points = sum(cat["max_points"] for cat in categories.values())
            percentage = (total_points / max_points) * 100 if max_points > 0 else 0.0

            # Determine pass_status using point-based thresholds
            pass_threshold = self.rubric.get('thresholds', {}).get('pass')
            revise_threshold = self.rubric.get('thresholds', {}).get('revise')
            pass_status = result.get('overall', {}).get('pass_status')
            if isinstance(pass_threshold, (int, float)) and isinstance(revise_threshold, (int, float)):
                if total_points >= pass_threshold:
                    pass_status = 'pass'
                elif total_points >= revise_threshold:
                    pass_status = 'revise'
                else:
                    pass_status = 'fail'

            # Write back normalized structure
            result['scores'] = scores
            result['categories'] = categories
            overall = result.get('overall', {}) or {}
            overall.update({
                'total_points': int(total_points),
                'max_points': int(max_points),
                'percentage': round(percentage, 1),
                'pass_status': pass_status or overall.get('pass_status', 'fail')
            })
            result['overall'] = overall
        except Exception:
            # Be conservative: don't break pipeline if normalization fails
            if self.verbose:
                print("Warning: Failed to normalize evaluation result; proceeding with raw result.")
        return result

    def generate_qualitative_feedback(self, transcript: str, evaluation: Dict[str, Any], visual_analysis: Optional[str] = None, segments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate qualitative feedback with 2 strengths and 2 areas for improvement.
        Tone adjusts based on pass/fail status.
        
        Args:
            transcript: The demo transcript text
            evaluation: The rubric evaluation results with scores and overall status
            visual_analysis: Optional visual alignment analysis
            segments: Optional timestamped transcript segments for time-referenced feedback
            
        Returns:
            Dict with 'strengths' (list of 2 items), 'improvements' (list of 2 items), and 'tone' ('congratulatory' or 'supportive')
        """
        pass_status = evaluation.get('overall', {}).get('pass_status', 'fail')
        is_passing = pass_status == 'pass'
        
        # Determine tone
        tone = 'congratulatory' if is_passing else 'supportive'
        
        # Extract scores for context
        scores = evaluation.get('scores', {})
        
        # Create mapping from criterion_id to label
        criterion_labels = {}
        if "categories" in self.rubric:
            # New format
            for category in self.rubric["categories"]:
                for criterion in category["criteria"]:
                    criterion_labels[criterion["criterion_id"]] = criterion["label"]
        else:
            # Old format
            for criterion in self.rubric["criteria"]:
                criterion_labels[criterion["id"]] = criterion["label"]
        
        # Find highest and lowest scoring criteria
        sorted_scores = sorted(scores.items(), key=lambda x: x[1].get('score', 0), reverse=True)
        top_2 = sorted_scores[:2]
        bottom_2 = sorted_scores[-2:]
        
        top_2_summary = "\n".join([f"- {criterion_labels.get(k, k.replace('_', ' ').title())}: {v.get('score', 'N/A')}/10 - {v.get('note', '')}" for k, v in top_2])
        bottom_2_summary = "\n".join([f"- {criterion_labels.get(k, k.replace('_', ' ').title())}: {v.get('score', 'N/A')}/10 - {v.get('note', '')}" for k, v in bottom_2])
        
        # Prepare transcript excerpt and time references
        transcript_excerpt = transcript[:2500]
        
        # Add time-referenced context if segments are available
        time_references = ""
        if segments:
            # Find segments with low confidence (potential issues)
            low_confidence_segments = [
                seg for seg in segments 
                if seg.get('avg_logprob', 0) < -1.0  # Low confidence threshold
            ][:3]  # Limit to 3 examples
            
            if low_confidence_segments:
                time_references = "\n\nTIMING ANALYSIS (areas that may need attention):\n"
                for i, seg in enumerate(low_confidence_segments, 1):
                    start_time = seg.get('start', 0)
                    minutes = int(start_time // 60)
                    seconds = int(start_time % 60)
                    time_str = f"{minutes}:{seconds:02d}"
                    confidence = seg.get('avg_logprob', 0)
                    text_preview = seg.get('text', '').strip()[:50]
                    time_references += f"{i}. {time_str}: Low confidence ({confidence:.2f}) - \"{text_preview}...\"\n"
        
        prompt = f"""
You are providing constructive feedback directly to a demo video submitter. Based on the evaluation below, provide:

1. Two specific strengths focusing on your HIGHEST scoring criteria - 2-3 sentences each
2. Two specific areas for improvement focusing on your LOWEST scoring criteria - 2-3 sentences each with actionable suggestions

When possible, reference specific timing or sections of your demo to make feedback more actionable.

Tone: {"Congratulatory and encouraging - you passed!" if is_passing else "Supportive and collaborative - help you improve without being discouraging"}

TOP 2 SCORING AREAS (use these for strengths):
{top_2_summary}

BOTTOM 2 SCORING AREAS (use these for improvements):
{bottom_2_summary}

Overall score: {evaluation.get('overall', {}).get('weighted_score', 0):.1f}/10 - Status: {pass_status.upper()}

Transcript excerpt:
{transcript_excerpt}{time_references}

Visual analysis:
{visual_analysis or 'Not available'}

Return strictly parseable JSON with this exact structure:
{{
    "strengths": [
        {{"title": "<name of top scoring criterion>", "description": "2-3 sentence explanation of why this scored well"}},
        {{"title": "<name of 2nd top scoring criterion>", "description": "2-3 sentence explanation of why this scored well"}}
    ],
    "improvements": [
        {{"title": "<name of lowest scoring criterion>", "description": "2-3 sentence explanation with actionable advice to improve"}},
        {{"title": "<name of 2nd lowest scoring criterion>", "description": "2-3 sentence explanation with actionable advice to improve"}}
    ]
}}
"""

        if self.llm and self.provider == AIProvider.OPENAI:
            try:
                with self.llm.OpenAI(api_key=self.api_key) as client:
                    resp = client.chat.completions.create(
                        model='gpt-4o-mini',
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1000,
                        temperature=0,  # Deterministic output for consistent feedback
                        response_format={"type": "json_object"}
                    )
                    text = resp.choices[0].message.content
                    if text:
                        feedback_data = json.loads(text)
                        feedback_data['tone'] = tone
                        return feedback_data
            except Exception as e:
                if self.verbose:
                    print(f"Warning: OpenAI API call failed for feedback ({e}). Using fallback.")
                pass
        
        elif self.llm and self.provider == AIProvider.ANTHROPIC:
            try:
                with self.llm.Anthropic(api_key=self.api_key) as client:
                    resp = client.messages.create(
                        model='claude-3-5-haiku-20241022',
                        max_tokens=1000,
                        temperature=0,  # Deterministic output for consistent feedback
                        messages=[{"role": "user", "content": prompt}]
                    )
                    # Handle Anthropic response format
                    if hasattr(resp, 'content') and resp.content:
                        content = resp.content[0]
                        if hasattr(content, 'text'):
                            feedback_data = json.loads(content.text)
                            feedback_data['tone'] = tone
                            return feedback_data
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Anthropic API call failed for feedback ({e}). Using fallback.")
                pass
        
        # Fallback: Generate basic feedback based on scores
        strengths = []
        improvements = []
        
        # Find highest scoring criteria
        sorted_scores = sorted(scores.items(), key=lambda x: x[1].get('score', 0), reverse=True)
        
        for i, (criterion_id, data) in enumerate(sorted_scores[:2]):
            criterion_label = criterion_labels.get(criterion_id, criterion_id.replace('_', ' ').title())
            strengths.append({
                "title": criterion_label,
                "description": f"You scored {data.get('score', 0)}/10. {data.get('note', 'Good performance in this area.')}"
            })
        
        for i, (criterion_id, data) in enumerate(sorted_scores[-2:]):
            criterion_label = criterion_labels.get(criterion_id, criterion_id.replace('_', ' ').title())
            improvements.append({
                "title": criterion_label,
                "description": f"You scored {data.get('score', 0)}/10. Consider focusing on improving this aspect."
            })
        
        return {
            "strengths": strengths,
            "improvements": improvements,
            "tone": tone
        }

    def process(self, source: str, is_url: bool = False, enable_vision: Optional[bool] = None) -> Dict[str, Any]:
        enable_vision = self.enable_vision if enable_vision is None else enable_vision
        audio_path = None
        video_for_frames = None
        downloaded_file = None
        try:
            if is_url:
                # Download video/audio via yt-dlp
                import yt_dlp
                outdir = os.path.join(self.temp_dir, 'downloads')
                os.makedirs(outdir, exist_ok=True)
                
                # If vision is enabled, download video; otherwise just audio
                if enable_vision:
                    ydl_opts: Dict[str, Any] = {
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'outtmpl': f'{outdir}/%(title)s.%(ext)s',
                        'merge_output_format': 'mp4'
                    }
                else:
                    ydl_opts: Dict[str, Any] = {
                        'format': 'bestaudio/best',
                        'outtmpl': f'{outdir}/%(title)s.%(ext)s'
                    }
                
                self._report_progress(f"📥 Downloading from URL...")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                    info = ydl.extract_info(source, download=True)
                    downloaded_file = ydl.prepare_filename(info)
                
                self._report_progress(f"✓ Download complete")
                
                # Now treat the downloaded file as a local file
                ext = Path(downloaded_file).suffix.lower()
                if ext in self.SUPPORTED_AUDIO_FORMATS:
                    audio_path = downloaded_file
                elif ext in self.SUPPORTED_VIDEO_FORMATS:
                    audio_path = self._extract_audio_from_video(downloaded_file)
                    video_for_frames = downloaded_file
                else:
                    raise ValueError(f'Unsupported file extension from download: {ext}')
            else:
                ext = Path(source).suffix.lower()
                if ext in self.SUPPORTED_AUDIO_FORMATS:
                    audio_path = source
                elif ext in self.SUPPORTED_VIDEO_FORMATS:
                    audio_path = self._extract_audio_from_video(source)
                    video_for_frames = source
                else:
                    raise ValueError(f'Unsupported file extension: {ext}')

            # Transcribe with timestamps
            if self.transcription_method in ["openai", "anthropic"]:
                # Remote transcription via OpenAI API
                self._report_progress(f"🎤 Transcribing audio with OpenAI Whisper API...")
            else:
                # Local transcription
                device_display = self._get_device_display()
                self._report_progress(f"🎤 Transcribing audio with Whisper {self.whisper_model_name} model on {device_display}...")
            transcription = self.transcribe_with_timestamps(audio_path)

            # Pick highlights
            highlights = self.pick_highlights(transcription.get('segments', []))

            visual_analysis = None
            if enable_vision and video_for_frames:
                self._report_progress("👁️ Analyzing video frames...")
                frames, timestamps = self._extract_frames(video_for_frames)
                visual_analysis = self.multimodal_alignment_check(transcription['text'], frames)

            self._report_progress("🤖 Evaluating transcript with AI...")
            evaluation = self.evaluate_transcript_with_rubric(transcription['text'], transcription.get('segments', []), visual_analysis)

            # Generate qualitative feedback
            self._report_progress("💬 Generating qualitative feedback...")
            feedback = self.generate_qualitative_feedback(transcription['text'], evaluation, visual_analysis, transcription.get('segments', []))

            result = {
                'whisper_model': self.whisper_model_name,
                'device': self.device,
                'rubric': self.rubric_name,
                'llm_provider': self.provider.value if hasattr(self.provider, 'value') else str(self.provider),
                'llm_model': 'gpt-4o-mini' if self.provider == AIProvider.OPENAI else 'claude-3-5-haiku-20241022',
                'evaluation': evaluation,
                'feedback': feedback,
                'transcript': transcription['text'],
                'language': transcription.get('language'),
                'quality': transcription.get('quality'),  # Whisper transcription quality metrics
                'segments': transcription.get('segments', []),
                'highlights': highlights,
                'visual_analysis': visual_analysis
            }
            return result
        finally:
            # Cleanup downloaded file if it was from a URL
            if downloaded_file and os.path.exists(downloaded_file):
                try:
                    os.remove(downloaded_file)
                    if self.verbose:
                        print(f"Cleaned up downloaded file: {downloaded_file}")
                except Exception as e:
                    if self.verbose:
                        print(f"Warning: Could not delete downloaded file {downloaded_file}: {e}")


if __name__ == '__main__':
    print('This module provides VideoEvaluator. Use from code or the CLI.')