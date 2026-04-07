import os
import sys
import subprocess

def _create_shortcut(target, shortcut_path, icon=None, working_dir=None):
    # Use PowerShell COM WScript.Shell to create .lnk shortcut
    ps = []
    ps.append('$WshShell = New-Object -ComObject WScript.Shell')
    ps.append(f"$Shortcut = $WshShell.CreateShortcut('{shortcut_path}')")
    ps.append(f"$Shortcut.TargetPath = '{target}'")
    if working_dir:
        ps.append(f"$Shortcut.WorkingDirectory = '{working_dir}'")
    if icon:
        ps.append(f"$Shortcut.IconLocation = '{icon}'")
    ps.append('$Shortcut.Save()')
    cmd = '; '.join(ps)
    try:
        subprocess.run(['powershell', '-NoProfile', '-Command', cmd], check=False)
    except Exception:
        pass


def run():
    # Only create shortcuts for frozen/executable builds
    if not getattr(sys, 'frozen', False):
        return

    try:
        user_profile = os.environ.get('USERPROFILE')
        appdata = os.environ.get('APPDATA')
        if not user_profile or not appdata:
            return

        exe_path = sys.executable
        exe_dir = os.path.dirname(exe_path)

        # Icon included in datas under 'data/images'
        icon_path = os.path.join(exe_dir, 'data', 'images', 'icone_ayanna_erp.ico')
        if not os.path.exists(icon_path):
            icon_path = exe_path  # fallback to exe as icon source

        # Desktop shortcut
        desktop = os.path.join(user_profile, 'Desktop')
        desktop_shortcut = os.path.join(desktop, 'AyannaErp.lnk')
        if not os.path.exists(desktop_shortcut):
            _create_shortcut(exe_path, desktop_shortcut, icon=icon_path, working_dir=exe_dir)

        # Start Menu (Programs)
        start_menu = os.path.join(appdata, 'Microsoft', 'Windows', 'Start Menu', 'Programs')
        start_shortcut = os.path.join(start_menu, 'AyannaErp.lnk')
        if not os.path.exists(start_shortcut):
            _create_shortcut(exe_path, start_shortcut, icon=icon_path, working_dir=exe_dir)

    except Exception:
        pass


run()
