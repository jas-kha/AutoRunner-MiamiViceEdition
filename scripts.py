import os
import sys
import subprocess

APP_NAME = "AutoRunner"
APP_PUBLISHER = "JK Software"
ENTRY_FILE = "main.py"
ICON_FILE = "icon.ico"

INNO_COMPILER = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
ISS_FILE = "installer.iss"


def run():
    os.system(f"python {ENTRY_FILE}")


def build():
    cmd = (
        f'pyinstaller '
        f'--onefile '
        f'--windowed '
        f'--icon={ICON_FILE} '
        f'--name {APP_NAME} '
        f'--add-data "assets/fonts;assets/fonts" '
        f'--add-data "assets/icons;assets/icons" '
        f'{ENTRY_FILE}'
    )
    subprocess.check_call(cmd, shell=True)


def setup():
    if not os.path.exists(INNO_COMPILER):
        print("ERROR: Inno Setup compiler not found")
        print("Please install Inno Setup from https://jrsoftware.org/isinfo.php")
        sys.exit(1)

    if not os.path.exists(ISS_FILE):
        print("ERROR: installer.iss not found")
        print("Please make sure installer.iss is in the current directory")
        sys.exit(1)

    cmd = f'"{INNO_COMPILER}" "{ISS_FILE}"'
    subprocess.check_call(cmd, shell=True)


def clean():
    targets = ["build", "dist", "installer", "__pycache__"]
    for item in targets:
        if os.path.exists(item):
            if os.path.isdir(item):
                subprocess.call(f'rmdir /S /Q "{item}"', shell=True)
            else:
                os.remove(item)

    for file in os.listdir("."):
        if file.endswith(".spec"):
            os.remove(file)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n Commands: run | build | setup | clean")
        # All information about commands
        print("\n run   - Run the application \n build - Build the application into an executable \n setup - Create an installer for the application \n clean - Remove build artifacts")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "run":
        run()
    elif cmd == "build":
        build()
    elif cmd == "setup":
        setup()
    elif cmd == "clean":
        clean()
    else:
        print("Unknown command:", cmd)
        sys.exit(1)
