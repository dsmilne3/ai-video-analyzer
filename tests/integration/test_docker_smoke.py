"""Docker Smoke Tests: Validate Docker deployment option.

Tests basic Docker functionality without duplicating full E2E coverage:
- Image builds successfully
- Container starts and serves Streamlit
- Volume mounts work for results
- Environment variables pass through
"""
import os
import time
import socket
import subprocess
import pytest
from pathlib import Path

pytestmark = [pytest.mark.integration, pytest.mark.docker]

PROJECT_ROOT = Path(__file__).parent.parent.parent
STREAMLIT_PORT = 8501


def _is_docker_available() -> bool:
    """Check if Docker daemon is running."""
    try:
        subprocess.run(['docker', 'info'], capture_output=True, check=True, timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _is_port_open(port: int, host: str = '127.0.0.1', timeout: float = 0.5) -> bool:
    """Check if a port is open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False


def _find_free_port(start: int = 8503, end: int = 8600) -> int:
    """Find an available port in the given range."""
    for port in range(start, end):
        if not _is_port_open(port):
            return port
    raise RuntimeError(f"No free ports found in range {start}-{end}")


@pytest.fixture(scope="module")
def docker_available():
    """Skip tests if Docker is not available."""
    if not _is_docker_available():
        pytest.skip("Docker daemon not running or docker command not found")


def test_docker_build(docker_available):
    """Test that Docker image builds successfully from Dockerfile."""
    cmd = ['docker', 'build', '-t', 'ai-video-analyzer-test', '.']
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=300  # 5 min timeout for build
    )
    
    assert result.returncode == 0, f"Docker build failed:\n{result.stderr}"
    # Docker BuildKit sends output to stderr; check both stdout and stderr
    combined_output = result.stdout + result.stderr
    assert 'Successfully built' in combined_output or 'Successfully tagged' in combined_output or 'naming to' in combined_output


def test_docker_compose_build(docker_available):
    """Test that docker-compose builds successfully."""
    # Determine compose command (docker compose vs docker-compose)
    compose_cmd = None
    try:
        subprocess.run(['docker', 'compose', 'version'], capture_output=True, check=True, timeout=5)
        compose_cmd = ['docker', 'compose']
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(['docker-compose', '--version'], capture_output=True, check=True, timeout=5)
            compose_cmd = ['docker-compose']
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Neither 'docker compose' nor 'docker-compose' available")
    
    result = subprocess.run(
        compose_cmd + ['build'],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=300
    )
    
    assert result.returncode == 0, f"Docker compose build failed:\n{result.stderr}"


def test_docker_container_starts_and_serves(docker_available):
    """Test that container starts and Streamlit serves on expected port."""
    container_name = 'ai-video-analyzer-smoke-test'
    test_port = _find_free_port()  # Dynamically find free port
    
    # Clean up any existing container
    subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True)
    
    # Start container
    cmd = [
        'docker', 'run', '-d',
        '--name', container_name,
        '-p', f'{test_port}:{STREAMLIT_PORT}',  # Map host:container
        'ai-video-analyzer-test'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    try:
        assert result.returncode == 0, f"Failed to start container:\n{result.stderr}"
        
        # Wait for Streamlit to be ready (max 60s)
        deadline = time.time() + 60
        while time.time() < deadline:
            if _is_port_open(test_port):
                break
            time.sleep(1)
        else:
            # Get container logs for debugging
            logs = subprocess.run(
                ['docker', 'logs', container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            pytest.fail(f"Container did not start serving within 60s. Logs:\n{logs.stdout}\n{logs.stderr}")
        
        # Verify port is accessible
        assert _is_port_open(test_port), "Streamlit port not accessible"
        
    finally:
        # Cleanup
        subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True)


def test_docker_volume_mount(docker_available):
    """Test that volume mounts work correctly for results directory."""
    container_name = 'ai-video-analyzer-volume-test'
    
    # Clean up
    subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True)
    
    # Create temp directory for results
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Start container with volume mount
        cmd = [
            'docker', 'run', '-d',
            '--name', container_name,
            '-v', f'{tmpdir}:/app/results',
            'ai-video-analyzer-test'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        try:
            assert result.returncode == 0, f"Failed to start container with volume:\n{result.stderr}"
            
            # Wait a bit for container to initialize
            time.sleep(5)
            
            # Create a test file in the container's results directory
            exec_cmd = [
                'docker', 'exec', container_name,
                'touch', '/app/results/test_mount.txt'
            ]
            exec_result = subprocess.run(exec_cmd, capture_output=True, timeout=10)
            assert exec_result.returncode == 0, "Failed to create test file in container"
            
            # Verify file exists in host tmpdir
            test_file = Path(tmpdir) / 'test_mount.txt'
            assert test_file.exists(), "Volume mount not working: file not visible on host"
            
        finally:
            subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True)


def test_docker_env_variables_pass_through(docker_available):
    """Test that environment variables are passed to container correctly."""
    container_name = 'ai-video-analyzer-env-test'
    
    # Clean up
    subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True)
    
    test_key = 'TEST_API_KEY_12345'
    
    cmd = [
        'docker', 'run', '-d',
        '--name', container_name,
        '-e', f'OPENAI_API_KEY={test_key}',
        'ai-video-analyzer-test'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    try:
        assert result.returncode == 0, f"Failed to start container:\n{result.stderr}"
        
        # Check environment variable inside container
        exec_cmd = ['docker', 'exec', container_name, 'printenv', 'OPENAI_API_KEY']
        env_result = subprocess.run(exec_cmd, capture_output=True, text=True, timeout=10)
        
        assert env_result.returncode == 0, "Failed to read environment variable"
        assert test_key in env_result.stdout, "Environment variable not set correctly"
        
    finally:
        subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True)
