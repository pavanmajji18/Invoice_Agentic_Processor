"""
Quick start script for the Invoice Processor
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

# Load local .env file
load_dotenv()

def check_env():
    """Check if Euri API key is set"""
    api_key = os.getenv("EURI_API_KEY")
    if not api_key:
        print("[WARNING] EURI_API_KEY not found in environment variables or .env file")
        print("   Please set it using:")
        print("   - Windows: set EURI_API_KEY=your_key")
        print("   - Linux/Mac: export EURI_API_KEY=your_key")
        print("   - Or create a .env file with: EURI_API_KEY=your_key")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print("[OK] EURI_API_KEY found")

def main():
    """Run the Streamlit app"""
    print("Starting Agentic Invoice Processor...")
    print()
    check_env()
    print()
    print("Opening Streamlit app in your browser...")
    print("   Press Ctrl+C to stop the server")
    print()
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "main.py"])
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()
