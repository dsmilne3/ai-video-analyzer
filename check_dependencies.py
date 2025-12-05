#!/usr/bin/env python3
"""
Dependency checker for the demo video analyzer.
Run this before using the application to verify all dependencies are installed.

Usage:
    python check_dependencies.py
"""
import sys
import subprocess
import importlib.util
from pathlib import Path


class DependencyChecker:
    """Check system and Python dependencies."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        
    def check_python_version(self):
        """Check Python version is 3.9+"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            self.errors.append(
                f"❌ Python 3.9+ required (found {version.major}.{version.minor}.{version.micro})"
            )
            return False
        else:
            self.info.append(
                f"✓ Python version: {version.major}.{version.minor}.{version.micro}"
            )
            return True
    
    def check_system_command(self, command, required=True):
        """Check if a system command exists."""
        # Common paths to check (in order of preference)
        common_paths = [
            None,  # Use 'which' first
            f"/opt/homebrew/bin/{command}",  # Homebrew on Apple Silicon
            f"/usr/local/bin/{command}",     # Homebrew on Intel Mac / Linux
            f"/usr/bin/{command}",           # System binaries
        ]
        
        found_path = None
        
        # Try 'which' first
        try:
            result = subprocess.run(
                ['which', command],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                found_path = result.stdout.strip()
        except:
            pass
        
        # If 'which' didn't find it, check common paths
        if not found_path:
            for path in common_paths[1:]:  # Skip None
                if Path(path).exists():
                    found_path = path
                    break
        
        if found_path:
            # Get version if possible
            try:
                version_result = subprocess.run(
                    [found_path, '-version'],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=2
                )
                version_line = version_result.stdout.split('\n')[0] if version_result.stdout else ''
                self.info.append(f"✓ {command}: {found_path}")
                if version_line:
                    self.info.append(f"  Version: {version_line[:80]}")
            except:
                self.info.append(f"✓ {command}: {found_path}")
            return True
        else:
            if required:
                self.errors.append(
                    f"❌ {command} not found - required for video/audio processing"
                )
                self.errors.append(f"   Install with: brew install {command}")
                self.errors.append(f"   After installing, restart your terminal or run: source ~/.zshrc")
            else:
                self.warnings.append(
                    f"⚠️  {command} not found (optional but recommended)"
                )
            return False
    
    def check_python_package(self, package_name, import_name=None, required=True):
        """Check if a Python package is installed."""
        if import_name is None:
            import_name = package_name
        
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            if required:
                self.errors.append(
                    f"❌ Python package '{package_name}' not installed"
                )
            else:
                self.warnings.append(
                    f"⚠️  Python package '{package_name}' not installed (optional)"
                )
            return False
        else:
            # Try to get version
            try:
                module = importlib.import_module(import_name)
                version = getattr(module, '__version__', 'unknown')
                self.info.append(f"✓ {package_name}: {version}")
                
                # Special check for torch MPS stability
                if package_name == 'torch':
                    try:
                        import torch
                        if torch.backends.mps.is_available():
                            # Test MPS stability
                            test_tensor = torch.randn(1, 10, device='mps')
                            test_result = torch.softmax(test_tensor, dim=-1)
                            if torch.isnan(test_result).any():
                                self.warnings.append(
                                    "⚠️  MPS (Apple Silicon GPU) test failed - may cause NaN errors during Whisper inference"
                                )
                                self.warnings.append(
                                    "   The application will automatically fall back to CPU if MPS issues occur"
                                )
                            else:
                                self.info.append("✓ MPS (Apple Silicon GPU) stability test passed")
                        else:
                            self.info.append("  MPS not available (expected on Intel Macs)")
                    except Exception as e:
                        self.warnings.append(
                            f"⚠️  Could not test MPS stability: {e}"
                        )
                        
            except:
                self.info.append(f"✓ {package_name}: installed")
            return True
    
    def check_file_exists(self, filepath, description):
        """Check if a required file exists."""
        path = Path(filepath)
        if not path.exists():
            self.warnings.append(
                f"⚠️  {description} not found: {filepath}"
            )
            return False
        else:
            self.info.append(f"✓ {description}: {filepath}")
            return True
    
    def run_all_checks(self):
        """Run all dependency checks."""
        print("=" * 70)
        print("DEMO VIDEO ANALYZER - DEPENDENCY CHECK")
        print("=" * 70)
        print()
        
        # Python version
        self.check_python_version()
        print()
        
        # System dependencies
        print("Checking system dependencies...")
        self.check_system_command('ffmpeg', required=True)
        print()
        
        # Core Python packages
        print("Checking core Python packages...")
        core_packages = [
            ('openai-whisper', 'whisper'),
            ('torch', 'torch'),
            ('torchaudio', 'torchaudio'),
            ('numpy', 'numpy'),
            ('opencv-python', 'cv2'),
        ]
        for pkg_name, import_name in core_packages:
            self.check_python_package(pkg_name, import_name, required=True)
        print()
        
        # Optional Python packages
        print("Checking optional Python packages...")
        optional_packages = [
            ('openai', 'openai'),
            ('anthropic', 'anthropic'),
            ('streamlit', 'streamlit'),
            ('pytest', 'pytest'),
        ]
        for pkg_name, import_name in optional_packages:
            self.check_python_package(pkg_name, import_name, required=False)
        print()
        
        # Supporting Python packages
        print("Checking supporting Python packages...")
        support_packages = [
            ('tiktoken', 'tiktoken'),
            ('numba', 'numba'),
            ('more-itertools', 'more_itertools'),
            ('ffmpeg-python', 'ffmpeg'),
        ]
        for pkg_name, import_name in support_packages:
            self.check_python_package(pkg_name, import_name, required=True)
        print()
        
        # Project structure
        print("Checking project structure...")
        self.check_file_exists('src/video_evaluator.py', 'Core evaluator')
        self.check_file_exists('Home.py', 'Streamlit app (main)')
        self.check_file_exists('pages/2_Analyze_Video.py', 'Streamlit app (analyze page)')
        self.check_file_exists('requirements.txt', 'Requirements file')
        print()
        
        # Print results
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print()
        
        if self.info:
            print("✓ Installed components:")
            for msg in self.info:
                print(f"  {msg}")
            print()
        
        if self.warnings:
            print("⚠️  Warnings:")
            for msg in self.warnings:
                print(f"  {msg}")
            print()
        
        if self.errors:
            print("❌ ERRORS - Cannot run application:")
            for msg in self.errors:
                print(f"  {msg}")
            print()
            print("Fix the errors above and run this check again.")
            print()
            return False
        elif self.warnings:
            print("⚠️  Some optional dependencies are missing.")
            print("The application will run but some features may not be available.")
            print()
            print("To install all dependencies:")
            print("  1. Install system dependencies: brew install ffmpeg")
            print("  2. Install Python packages: pip install -r requirements.txt")
            print()
            return True
        else:
            print("✅ ALL CHECKS PASSED")
            print()
            print("The application is ready to use!")
            print()
            print("Quick start:")
            print("  streamlit run Home.py")
            print("  python test_data/run_end_to_end_demo.py")
            print()
            return True


def main():
    """Run dependency checks."""
    checker = DependencyChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
