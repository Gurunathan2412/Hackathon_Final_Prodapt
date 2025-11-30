# Main entry point to run the Streamlit app
import sys
from pathlib import Path
import streamlit as st  # type: ignore

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Import the Streamlit UI main function
try:
    from ui.streamlit_app import main as run_ui  # type: ignore
except Exception:  # pragma: no cover
    def run_ui():  # fallback
        st.error("UI module not available. Check installation and imports.")


def bootstrap():
    """Perform any startup initialization before launching UI."""
    # Placeholder for future initialization (e.g., loading models, warm caches)
    pass


try:
    from loguru import logger  # type: ignore
    logger.remove()
    logger.add(sys.stderr, level="INFO")
except Exception:
    pass

if __name__ == "__main__":  # Correct main guard
    bootstrap()
    if 'logger' in globals() and logger:
        logger.info('Telecom Assistant app finished startup.')
    run_ui()
