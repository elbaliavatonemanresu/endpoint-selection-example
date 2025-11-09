"""
CTTI Endpoint Selection Facilitator App
Entry point for launching the Streamlit application.
"""
import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Streamlit app."""
    app_path = Path(__file__).parent / "src" / "app.py"

    if not app_path.exists():
        print(f"Error: Application file not found at {app_path}")
        sys.exit(1)

    print("Launching CTTI Endpoint Selection Facilitator App...")
    print(f"Running: streamlit run {app_path}")

    # Launch Streamlit with the app.py file
    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(app_path)],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error launching Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down CTTI app...")
        sys.exit(0)


if __name__ == "__main__":
    main()
