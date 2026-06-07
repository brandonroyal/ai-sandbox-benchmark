"""
Test that measures sandbox suspend and resume latency.
"""
from tests.test_utils import create_test_config
from tests.test_sandbox_utils import get_sandbox_utils

def test_suspend_resume():
    """
    Measures the latency of suspending (stopping) and resuming (starting) a sandbox.
    
    This test is specific to sandbox environments that support dynamic suspension/resumption 
    (such as Daytona). For other providers, these metrics will be reported as N/A.
    """
    # Define test configuration
    config = create_test_config(
        env_vars=[],  # No env vars needed
        single_run=False,  # Run multiple times to calculate statistical averages
    )
    # Enable lifecycle measurement flag for providers
    config["measure_lifecycle"] = True
    
    # Get the sandbox utilities code
    utils_code = get_sandbox_utils(
        include_timer=True,
        include_results=True,
        include_packages=False
    )
    
    # Define the test-specific code to execute inside the sandbox
    test_code = """
import os

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
        
    # Clean up the verification file
    try:
        os.remove(filepath)
    except Exception:
        pass
        
    return "Sandbox lifecycle execution successful: filesystem state is preserved!"

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
