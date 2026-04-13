"""
Update checker and installer module for D4an Texture Injector.
Checks GitHub Releases for updates and handles downloading/installing them.
"""
import os
import sys
import json
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError
from typing import Optional


class UpdateChecker:
    """Handles checking and downloading updates from GitHub Releases."""
    
    # GitHub repository information - UPDATE THESE WITH YOUR REPO DETAILS
    GITHUB_OWNER = "d4anw"  # Replace with your GitHub username
    GITHUB_REPO = "D4anTextureInjector"  # Replace with your repository name
    
    # Current version - should match the version in your app
    CURRENT_VERSION = "2.4"
    
    def __init__(self, app_root: tk.Tk, on_update_callback=None):
        """
        Initialize the update checker.
        
        Args:
            app_root: The root tkinter window
            on_update_callback: Optional callback to execute after update
        """
        self.app_root = app_root
        self.on_update_callback = on_update_callback
        self.latest_version = None
        self.update_url = None
        self.exe_path = self._get_exe_path()
        
    @staticmethod
    def _get_exe_path() -> Path:
        """Get path to the current executable."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable (PyInstaller)
            return Path(sys.executable)
        else:
            # Running as script - look for compiled exe in dist folder
            dist_exe = Path(__file__).parent / "dist" / "D4anTexture.exe"
            if dist_exe.exists():
                return dist_exe
            return Path(sys.executable)
    
    def check_for_updates(self) -> bool:
        """
        Check if an update is available on GitHub.
        
        Returns:
            True if update available, False otherwise
        """
        try:
            api_url = f"https://api.github.com/repos/{self.GITHUB_OWNER}/{self.GITHUB_REPO}/releases/latest"
            
            request = Request(api_url, headers={"User-Agent": "D4anTextureUpdater"})
            with urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode())
                
            latest_version = data.get("tag_name", "").lstrip("v")
            if not latest_version:
                return False
            
            self.latest_version = latest_version
            
            # Check if newer version exists
            if self._is_newer_version(latest_version, self.CURRENT_VERSION):
                # Find the .exe download URL
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".exe"):
                        self.update_url = asset["browser_download_url"]
                        return True
            
            return False
        except (URLError, json.JSONDecodeError, KeyError, Exception) as e:
            print(f"Update check failed: {e}")
            return False
    
    @staticmethod
    def _is_newer_version(new_version: str, current_version: str) -> bool:
        """
        Compare two version strings.
        
        Args:
            new_version: Version string to check (e.g., "0.74")
            current_version: Current version string
            
        Returns:
            True if new_version > current_version
        """
        try:
            new_parts = [int(x) for x in new_version.split(".")]
            current_parts = [int(x) for x in current_version.split(".")]
            
            # Pad shorter version with zeros
            while len(new_parts) < len(current_parts):
                new_parts.append(0)
            while len(current_parts) < len(new_parts):
                current_parts.append(0)
            
            return new_parts > current_parts
        except (ValueError, AttributeError):
            return False
    
    def show_update_dialog(self) -> bool:
        """
        Show a dialog asking user if they want to update.
        
        Returns:
            True if user clicks yes, False otherwise
        """
        from tkinter import messagebox
        
        result = messagebox.askyesno(
            "Update Available",
            f"A new version ({self.latest_version}) is available!\n\n"
            f"Current version: {self.CURRENT_VERSION}\n\n"
            "Download and install the update?\n\n"
            "(The application will restart after installing.)",
        )
        return result
    
    def download_and_install_update(self) -> None:
        """
        Download the update in a background thread and install it.
        """
        if not self.update_url:
            return
        
        # Run download/install in background thread to avoid freezing UI
        thread = threading.Thread(target=self._download_and_install_thread, daemon=True)
        thread.start()
    
    def _download_and_install_thread(self) -> None:
        """Background thread for downloading and installing update."""
        try:
            from tkinter import messagebox
            
            # Download the update
            temp_exe = self.exe_path.parent / "D4anTexture_new.exe"
            backup_exe = self.exe_path.parent / "D4anTexture_old.exe"
            
            # Show downloading message
            print(f"Downloading update from {self.update_url}...")
            self._download_file(self.update_url, str(temp_exe))
            
            # Create a batch script to replace the exe and restart
            # The script will wait for the current process to exit before replacing
            batch_script = self.exe_path.parent / "update_install.bat"
            batch_content = f"""@echo off
REM Wait for the current process to exit
timeout /t 3 /nobreak
REM Backup old exe
if exist "{self.exe_path}" (
    move /Y "{self.exe_path}" "{backup_exe}"
)
REM Move new exe to proper location
move /Y "{temp_exe}" "{self.exe_path}"
REM Start the updated app
start "" "{self.exe_path}"
REM Clean up batch file
(goto) 2>nul & del "%~f0"
"""
            batch_script.write_text(batch_content)
            
            # Execute batch script (detached from current process)
            subprocess.Popen(
                f'cmd.exe /c "{batch_script}"',
                creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Exit current application (batch script will run after this exits)
            self.app_root.quit()
            sys.exit(0)
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror(
                "Update Failed",
                f"Failed to download and install update:\n{str(e)}\n\nPlease try again later."
            )
    
    @staticmethod
    def _download_file(url: str, destination: str) -> None:
        """
        Download a file from URL to destination.
        
        Args:
            url: URL to download from
            destination: Local file path to save to
        """
        request = Request(url, headers={"User-Agent": "D4anTextureUpdater"})
        with urlopen(request, timeout=30) as response:
            with open(destination, 'wb') as out_file:
                out_file.write(response.read())


def check_for_updates_on_startup(app_root: tk.Tk) -> None:
    """
    Check for updates silently on app startup.
    Should be called from the main app's __init__.
    
    Args:
        app_root: The root tkinter window
    """
    def _check_thread():
        checker = UpdateChecker(app_root)
        if checker.check_for_updates():
            if checker.show_update_dialog():
                checker.download_and_install_update()
    
    # Run check in background thread to avoid blocking UI
    thread = threading.Thread(target=_check_thread, daemon=True)
    thread.start()
