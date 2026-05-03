import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
GET_MACRO_SCRIPT = PROJECT_ROOT / "get_macro_index.py"


def run_command(cmd, cwd=None):
    print(f"\n>>> {' '.join(str(x) for x in cmd)}")
    subprocess.check_call(cmd, cwd=cwd)


def check_required_files():
    missing = []

    if not REQUIREMENTS_FILE.exists():
        missing.append("requirements.txt")

    if not GET_MACRO_SCRIPT.exists():
        missing.append("get_macro_index.py")

    if missing:
        raise FileNotFoundError(
            "Missing required file(s): " + ", ".join(missing)
        )


def create_venv():
    if VENV_DIR.exists():
        print(f"Virtual environment already exists: {VENV_DIR}")
    else:
        print("Creating virtual environment...")
        run_command([sys.executable, "-m", "venv", str(VENV_DIR)], cwd=PROJECT_ROOT)


def get_venv_python():
    if os.name == "nt":
        python_path = VENV_DIR / "Scripts" / "python.exe"
    else:
        python_path = VENV_DIR / "bin" / "python"

    if not python_path.exists():
        raise FileNotFoundError(f"Venv Python not found: {python_path}")
    return python_path


def install_requirements(venv_python):
    print("Upgrading pip...")
    run_command([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], cwd=PROJECT_ROOT)

    print("Installing requirements...")
    run_command([str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)], cwd=PROJECT_ROOT)


def first_data_download(venv_python):
    print("Running first market data download...")
    run_command([str(venv_python), str(GET_MACRO_SCRIPT)], cwd=PROJECT_ROOT)


def main():
    check_required_files()
    create_venv()
    venv_python = get_venv_python()
    install_requirements(venv_python)
    first_data_download(venv_python)

    print("\nInstallation completed successfully.")
    print("You can now run the analysis with:")
    if os.name == "nt":
        print(r".venv\Scripts\python.exe analyze_portfolio.py")
    else:
        print("./.venv/bin/python analyze_portfolio.py")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    finally:
        if os.name == "nt":
            input("\nPress Enter to exit...")
