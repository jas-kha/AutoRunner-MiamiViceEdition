import os
import sys
import subprocess

def run():
    os.system("python auto_runner.py")

def build():
    subprocess.call(f"pyinstaller --windowed --onefile --icon=icon.ico auto_runner.py", shell=True)

def clean():
    for folder in ["build", "dist", "__pycache__"]:
        if os.path.exists(folder):
            subprocess.call(f"rmdir /S /Q {folder}", shell=True)
    if os.path.exists("auto_runner.spec"):
        os.remove("auto_runner.spec")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Commands: run | build | clean")
        sys.exit()

    cmd = sys.argv[1].lower()

    if cmd == "run":
        run()
    elif cmd == "build":
        build()
    elif cmd == "clean":
        clean()
    else:
        print("Unknown command:", cmd)
