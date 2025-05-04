from pathlib import Path
from typing import Callable, Optional
from ..models.workflow import workflow_state

def safe_execute(func: Callable, 
                error_msg: str, 
                step_name: Optional[str] = None,
                max_retries: int = 2):
    """Safely execute a function with retry logic and error handling"""
    for retry in range(max_retries + 1):
        try:
            result = func()
            workflow_state.consecutive_errors = 0
            return result
        except Exception as e:
            workflow_state.error_count += 1
            workflow_state.consecutive_errors += 1
            if retry >= max_retries:
                raise RuntimeError(f"{error_msg}: {str(e)}")
    return None