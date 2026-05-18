import os
import sys
import subprocess
from pathlib import Path
import shutil

# Path to the source image (will be passed or hardcoded based on artifact location)
# The agent needs to copy the artifact to the project dir first or access it via absolute path.

# Define dynamic project directory path
WHATSAPP_BOT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = WHATSAPP_BOT_DIR.parent

# The original ARTIFACT_PATH was Windows specific. 
# On Linux, we should look for it in the project root or local folder if available.
# As a fallback, we use a relative path if it exists.
ARTIFACT_PATH = PROJECT_DIR / "neoauto_crm_robot_icon.png"
ICON_PATH = WHATSAPP_BOT_DIR / "crm_neoauto.ico"
SHORTCUT_PATH = Path(os.path.expanduser("~/Desktop")) / "CRM Neoauto.lnk"
TARGET_PATH = WHATSAPP_BOT_DIR / "menu_crm.sh"

def convert_to_ico(source, dest):
    print(f"Converting {source} to {dest}...")
    try:
        from PIL import Image
        img = Image.open(source)
        img.save(dest, format='ICO', sizes=[(256, 256)])
        print("Conversion successful.")
        return True
    except ImportError:
        print("PIL (Pillow) not installed. Trying to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
            from PIL import Image
            img = Image.open(source)
            img.save(dest, format='ICO', sizes=[(256, 256)])
            print("Conversion successful after install.")
            return True
        except Exception as e:
            print(f"Failed to convert icon: {e}")
            return False
    except Exception as e:
        print(f"Error converting icon: {e}")
        return False

def create_shortcut_powershell(target, unused_shortcut_path, icon_path):
    # We ignore the passed shortcut_path and ask PS for the real Desktop
    print(f"Creating shortcut on the REAL Desktop...")
    
    ps_script = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $DesktopPath "CRM Neoauto.lnk"
    
    Write-Host "Detected Desktop Path: $DesktopPath"
    
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "{target}"
    $Shortcut.WorkingDirectory = "{target.parent}"
    $Shortcut.IconLocation = "{icon_path}"
    $Shortcut.Description = "CRM Neoauto Automation"
    $Shortcut.Save()
    Write-Host "Shortcut saved to: $ShortcutPath"
    """
    
    # Write temp PS script
    ps_file = PROJECT_DIR / "create_lnk.ps1"
    with open(ps_file, "w") as f:
        f.write(ps_script)
        
    try:
        result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_file)], check=True, capture_output=True, text=True)
        print("PowerShell Output:")
        print(result.stdout)
        os.remove(ps_file)
        return True
    except Exception as e:
        print(f"Error creating shortcut: {e}")
        return False

def main():
    if not os.path.exists(ARTIFACT_PATH):
        print(f"Error: Artifact image not found at {ARTIFACT_PATH}")
        # Fallback to standard icon if image missing? No, we want the generated one.
        return

    # Convert to ICO
    if not convert_to_ico(ARTIFACT_PATH, ICON_PATH):
        print("Using standard shell icon as fallback.")
        icon_path_arg = "shell32.dll,0"
    else:
        icon_path_arg = str(ICON_PATH)

    # Create Shortcut
    if create_shortcut_powershell(TARGET_PATH, SHORTCUT_PATH, icon_path_arg):
        print("\nDONE! Shortcut created on Desktop.")
        print("To pin to Taskbar: Right-click the shortcut -> 'Pin to Taskbar'.")

if __name__ == "__main__":
    main()
