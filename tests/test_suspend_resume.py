"""
Test that measures sandbox suspend and resume latency under a representative agent workload.
"""
import textwrap
from tests.test_utils import create_test_config
from tests.test_sandbox_utils import get_sandbox_utils

def test_suspend_resume():
    """
    Measures the latency of suspending (stopping) and resuming (starting) a sandbox
    loaded with a representative coding agent workload (git repository, 50 python modules, 
    and a virtual environment containing dependencies like pydantic, fastapi, pytest).
    
    This test is specific to sandbox environments that support dynamic suspension/resumption 
    (such as Daytona, E2B, and Modal). For other providers, these metrics will be reported as N/A.
    """
    
    # Custom setup script that initializes the workload inside the sandbox before suspend
    setup_script = textwrap.dedent("""
        import os
        import subprocess
        import sys
        import textwrap

        def setup_workload():
            workspace_dir = "/tmp/representative_workspace"
            print(f"Setting up representative workload at {workspace_dir}...")
            os.makedirs(workspace_dir, exist_ok=True)
            os.chdir(workspace_dir)
            
            # Init git repo
            subprocess.run(["git", "init"], check=True)
            
            # Create directories
            for d in ["src", "tests", "docs", "config"]:
                os.makedirs(d, exist_ok=True)
                
            # Create 50 mock python modules representing agent codebase
            for i in range(1, 51):
                filename = f"src/module_{i}.py"
                with open(filename, "w") as f:
                    f.write(textwrap.dedent(f'''\
                        # Python Agent Module {i}
                        from typing import Dict, Any, List, Optional
                        import pydantic

                        class AgentComponent{i}(pydantic.BaseModel):
                            name: str
                            config: Dict[str, Any] = {{}}
                            
                            def process(self, data: List[str]) -> Optional[str]:
                                if not data:
                                    return None
                                return f"Component {i} processed {{len(data)}} items for {{self.name}}"
                    '''))
                    
            # Create some mock tests
            for i in range(1, 11):
                filename = f"tests/test_module_{i}.py"
                with open(filename, "w") as f:
                    f.write(textwrap.dedent(f'''\
                        from src.module_{i} import AgentComponent{i}
                        def test_component_{i}():
                            comp = AgentComponent{i}(name="test_agent")
                            assert comp.process(["item1", "item2"]) == "Component {i} processed 2 items for test_agent"
                    '''))
                    
            # Create a large documentation markdown file
            with open("docs/agent_architecture.md", "w") as f:
                f.write("# Representative Agent Architecture\\n\\n" + "This is a representative agent documentation line to simulate a real codebase scale. " * 10000)
                
            # Git add all
            subprocess.run(["git", "add", "."], check=True)
            
            # Set up virtual environment
            print("Creating virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
            
            # Install dependencies inside virtual environment
            print("Installing packages in virtual environment...")
            subprocess.run([".venv/bin/pip", "install", "pydantic", "fastapi", "requests", "jinja2", "pytest"], check=True)
            
            print("Representative workload setup successfully completed!")

        try:
            setup_workload()
        except Exception as e:
            print(f"Error setting up representative workload: {e}")
            sys.exit(1)
    """)

    # Define test configuration
    config = create_test_config(
        env_vars=[],  # No env vars needed
        single_run=False,  # Run multiple times to calculate statistical averages
    )
    
    # Enable lifecycle measurement and pass the custom setup script
    config["measure_lifecycle"] = True
    config["setup_script"] = setup_script
    
    # Get the sandbox utilities code
    utils_code = get_sandbox_utils(
        include_timer=True,
        include_results=True,
        include_packages=False
    )
    
    # Define the test-specific code to execute inside the sandbox after resume
    test_code = """
import os
import subprocess
import sys

@benchmark_timer
def run_test():
    filepath = '/tmp/suspend_resume_verify.txt'
    # If the file wasn't written, it means suspend/resume was not triggered (or not supported)
    if not os.path.exists(filepath):
        return "Sandbox execution successful (lifecycle verification skipped: provider does not support suspend/resume)"
        
    with open(filepath, 'r') as f:
        content = f.read().strip()
        
    if content != "Stateful Sandbox Persistence Test OK":
        return f"Failure: File content mismatch: '{content}'"
        
    # Verify the representative workload
    workspace_dir = "/tmp/representative_workspace"
    if not os.path.exists(workspace_dir):
        return "Failure: Representative workspace directory not found after resume!"
        
    os.chdir(workspace_dir)
    
    # 1. Verify files exist
    src_files = os.listdir("src")
    if len(src_files) != 50:
        return f"Failure: Found {len(src_files)} files in src/, expected 50."
        
    # 2. Verify git is initialized and status works
    git_status = subprocess.run(["git", "status"], capture_output=True, text=True)
    if git_status.returncode != 0:
        return f"Failure: Git command failed in resumed workspace: {git_status.stderr}"
        
    # 3. Verify virtual environment packages can be run
    pytest_version = subprocess.run([".venv/bin/pytest", "--version"], capture_output=True, text=True)
    if pytest_version.returncode != 0:
        return f"Failure: Pytest failed to run from virtual environment: {pytest_version.stderr}"
        
    # Clean up the verification file
    try:
        os.remove(filepath)
    except Exception:
        pass
        
    return "Sandbox lifecycle execution successful: filesystem, virtualenv, and git state are fully preserved!"

# Execute the test and get results with timing
test_result = run_test()

# Print the results using the utility function
print_benchmark_results(test_result)
"""

    # Combine the utilities and test code
    full_code = f"{utils_code}\n\n{test_code}"

    # Return the test configuration and code
    return {
        "config": config,
        "code": full_code
    }
