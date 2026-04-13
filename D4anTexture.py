"""
D4an Texture Injector - Game Texture Replacement Tool
Allows users to inject custom texture packs into Stumble Guys (v0.73)
by replacing bundle files and data files with user-selected alternatives.
"""
import os
import shutil
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from updater import check_for_updates_on_startup
except ImportError:
    check_for_updates_on_startup = None


def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = str(Path(__file__).resolve().parent)

    return os.path.join(base_path, relative_path)


class InjectorApp:
    """
    GUI application for texture injection into Stumble Guys game.
    
    Allows users to:
    - Locate their Stumble Guys game installation
    - Select texture packs to inject
    - Inject selected textures into game files
    - Restore original game files from backups
    
    All file operations are logged and reversible via restore functionality.
    """
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("D4an Texture Injector!")
        self.root.geometry("950x680")
        self.root.minsize(920, 650)

        self.base_dir = Path(__file__).resolve().parent
        self.game_root_folder: Path | None = None
        self.standalone_windows64_path: Path | None = None
        self.data_unity3d_path: Path | None = None

        # Texture packs configuration - now using checkboxes
        self.texture_packs = {
            "BD + BDL": "BlockDashBundle",
            "Laser Tracer": "LaserTracerBundle",
            "Skins": "SkinsBundle",
            "NL footsteps": "ZoomBundle",
            "Data File": "DataFile"
        }
        # Optional packs that can be toggled
        self.optional_packs = {
            "BD + BDL": "BlockDashBundle",
            "Laser Tracer": "LaserTracerBundle",
            "Skins": "SkinsBundle",
            "NL footsteps": "ZoomBundle",
        }
        self.pack_selections = {pack: tk.BooleanVar(value=False) for pack in self.optional_packs.keys()}
        self.selected_packs: list[str] = []

        self.bg_photo = None
        self.bg_image_item = None

        self.panel_color = "#d88f46"
        self.button_color = "#b8651f"
        self.button_hover_color = "#a0581a"
        self.button_active_color = "#8b4513"
        self.button_text_color = "#ffffff"

        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg="#d88f46")
        self.canvas.pack(fill="both", expand=True)

        self.left_panel = tk.Frame(self.canvas, bg=self.panel_color, bd=0, padx=14, pady=14, relief="raised")
        self.left_panel.config(highlightthickness=2, highlightbackground="#8b4513")
        self.left_panel_window = self.canvas.create_window(22, 105, anchor="nw", window=self.left_panel)

        self.center_panel = tk.Frame(self.canvas, bg=self.panel_color, bd=0, padx=25, pady=25, relief="raised")
        self.center_panel.config(highlightthickness=2, highlightbackground="#8b4513")
        self.center_panel_window = self.canvas.create_window(0, 0, anchor="center", window=self.center_panel)

        self.folder_var = tk.StringVar(value="No folder linked yet")
        self.status_var = tk.StringVar(value="Ready")

        self.info_button = tk.Button(
            self.left_panel,
            text="ℹ  Info",
            width=16,
            font=("Segoe UI", 11, "bold"),
            bg=self.button_color,
            fg=self.button_text_color,
            activebackground=self.button_active_color,
            activeforeground=self.button_text_color,
            bd=0,
            padx=12,
            pady=12,
            relief="flat",
            cursor="hand2",
            command=self.show_info,
            highlightthickness=0,
        )
        self.info_button.pack(pady=(0, 12))
        self.info_button.bind("<Enter>", lambda e: self._on_button_enter(self.info_button))
        self.info_button.bind("<Leave>", lambda e: self._on_button_leave(self.info_button))

        self.link_button = tk.Button(
            self.left_panel,
            text="📁  Locate Game\nFolder",
            width=16,
            font=("Segoe UI", 11, "bold"),
            bg=self.button_color,
            fg=self.button_text_color,
            activebackground=self.button_active_color,
            activeforeground=self.button_text_color,
            bd=0,
            padx=12,
            pady=12,
            relief="flat",
            cursor="hand2",
            command=self.link_folder,
            highlightthickness=0,
        )
        self.link_button.pack(pady=(0, 0))
        self.link_button.bind("<Enter>", lambda e: self._on_button_enter(self.link_button))
        self.link_button.bind("<Leave>", lambda e: self._on_button_leave(self.link_button))

        self.logo_label = tk.Label(
            self.center_panel,
            text="D4an Texture Injector",
            font=("Segoe UI", 24, "bold"),
            fg="#ffffff",
            bg=self.panel_color,
            justify="center",
        )
        self.logo_label.pack(pady=(0, 8))

        version_label = tk.Label(
            self.center_panel,
            text="v2.3",
            font=("Segoe UI", 11),
            fg="#e8c547",
            bg=self.panel_color,
            justify="center",
        )
        version_label.pack(pady=(0, 20))

        # Texture selection frame with checkboxes
        self.selection_frame = tk.Frame(self.center_panel, bg=self.panel_color)
        self.selection_frame.pack(pady=(0, 20), fill="x")

        selection_label = tk.Label(
            self.selection_frame,
            text="SELECT TEXTURES TO INJECT:",
            font=("Segoe UI", 11, "bold"),
            fg="#ffffff",
            bg=self.panel_color,
        )
        selection_label.pack(anchor="w", pady=(0, 12))

        checkbox_frame = tk.Frame(self.selection_frame, bg=self.panel_color)
        checkbox_frame.pack(anchor="w", fill="x")

        for pack_name in self.optional_packs.keys():
            checkbox = tk.Checkbutton(
                checkbox_frame,
                text=pack_name,
                variable=self.pack_selections[pack_name],
                font=("Segoe UI", 10),
                fg=self.button_text_color,
                bg=self.panel_color,
                selectcolor=self.button_color,
                activebackground=self.panel_color,
                activeforeground=self.button_text_color,
                bd=0,
                highlightthickness=0,
            )
            checkbox.pack(anchor="w", pady=5)

        self.inject_button = tk.Button(
            self.center_panel,
            text="➤  INJECT SELECTED",
            width=32,
            font=("Segoe UI", 12, "bold"),
            bg=self.button_color,
            fg=self.button_text_color,
            activebackground=self.button_active_color,
            activeforeground=self.button_text_color,
            bd=0,
            padx=16,
            pady=14,
            relief="flat",
            cursor="hand2",
            command=self.start_swap,
            highlightthickness=0,
        )
        self.inject_button.pack(pady=(16, 10))
        self.inject_button.bind("<Enter>", lambda e: self._on_button_enter(self.inject_button))
        self.inject_button.bind("<Leave>", lambda e: self._on_button_leave(self.inject_button))

        self.remove_button = tk.Button(
            self.center_panel,
            text="↻  RESTORE ORIGINAL",
            width=32,
            font=("Segoe UI", 12, "bold"),
            bg=self.button_color,
            fg=self.button_text_color,
            activebackground=self.button_active_color,
            activeforeground=self.button_text_color,
            bd=0,
            padx=16,
            pady=14,
            relief="flat",
            cursor="hand2",
            command=self.start_restore,
            highlightthickness=0,
        )
        self.remove_button.pack(pady=(0, 0))
        self.remove_button.bind("<Enter>", lambda e: self._on_button_enter(self.remove_button))
        self.remove_button.bind("<Leave>", lambda e: self._on_button_leave(self.remove_button))

        self.status_label = tk.Label(
            self.canvas,
            textvariable=self.status_var,
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg=self.panel_color,
        )
        self.status_label_window = self.canvas.create_window(0, 0, anchor="s", window=self.status_label)

        self.folder_label = tk.Label(
            self.canvas,
            textvariable=self.folder_var,
            font=("Segoe UI", 9),
            fg="#ffffff",
            bg=self.panel_color,
        )
        self.folder_label_window = self.canvas.create_window(0, 0, anchor="s", window=self.folder_label)

        self.root.bind("<Configure>", self._on_resize)

        self._try_load_default_background()
        
        # Check for updates on startup (runs in background thread)
        if check_for_updates_on_startup:
            check_for_updates_on_startup(self.root)

    def _on_resize(self, _event: tk.Event) -> None:
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        self.canvas.coords(self.left_panel_window, 20, max(60, (height // 2) - 110))
        self.canvas.coords(self.center_panel_window, width // 2, height // 2)
        self.canvas.coords(self.status_label_window, width // 2, height - 58)
        self.canvas.coords(self.folder_label_window, width // 2, height - 34)

        if self.bg_image_item is not None:
            self.canvas.coords(self.bg_image_item, width // 2, height // 2)

    def _on_button_enter(self, button: tk.Button) -> None:
        """Hover effect for buttons."""
        button.config(bg=self.button_hover_color)

    def _on_button_leave(self, button: tk.Button) -> None:
        """Reset button color on leave."""
        button.config(bg=self.button_color)

    def _try_load_default_background(self) -> None:
        background_file = Path(resource_path("background.png"))
        if not background_file.exists():
            return

        try:
            self.bg_photo = tk.PhotoImage(file=str(background_file))
            self.bg_image_item = self.canvas.create_image(
                self.root.winfo_width() // 2,
                self.root.winfo_height() // 2,
                image=self.bg_photo,
                anchor="center",
            )
            self.canvas.tag_lower(self.bg_image_item)
            self.canvas.tag_raise(self.left_panel_window)
            self.canvas.tag_raise(self.center_panel_window)
            self.canvas.tag_raise(self.status_label_window)
            self.canvas.tag_raise(self.folder_label_window)
        except tk.TclError as error:
            self.status_var.set(f"Background load failed: {error}")

    def show_info(self) -> None:
        messagebox.showinfo(
            "Tutorial",
            "D4an Texture Injector v2.2\n\n"
            "1) Click 'Locate Game Folder'\n"
            "2) Select the 'Stumble Guys (v0.73)' folder\n"
            "3) Select the texture pack you want\n"
            "4) Click 'Inject Textures' to inject\n"
            "5) 'Restore Original' reverts the changes",
        )

    def _resolve_game_paths(self, selected_path: Path) -> tuple[Path | None, Path | None]:
        """Find data.unity3d and StandaloneWindows64 folder in the given path."""
        data_unity3d = None
        standalone_windows64 = None

        # Look for data.unity3d in Stumble Guys_Data folders
        for stumble_data_dir in selected_path.rglob("Stumble Guys_Data"):
            potential_data = stumble_data_dir / "data.unity3d"
            if potential_data.exists() and potential_data.is_file():
                data_unity3d = potential_data
                break

        # Look for StandaloneWindows64 in StreamingAssets/aa/
        for streaming_assets in selected_path.rglob("StreamingAssets"):
            aa_dir = streaming_assets / "aa"
            if aa_dir.exists():
                standalone_dir = aa_dir / "StandaloneWindows64"
                if standalone_dir.exists() and standalone_dir.is_dir():
                    standalone_windows64 = standalone_dir
                    break

        return data_unity3d, standalone_windows64

    def _find_bundle_by_name(self, bundle_folder: Path, bundle_name: str) -> Path | None:
        """Find a bundle file by partial name match in a folder."""
        if not bundle_folder.exists():
            return None
        
        for item in bundle_folder.iterdir():
            if item.is_file() and bundle_name.lower() in item.name.lower():
                return item
        
        return None

    def link_folder(self) -> None:
        selected = filedialog.askdirectory(title="Select Stumble Guys (v0.73) folder")
        if not selected:
            return

        data_file, windows_folder = self._resolve_game_paths(Path(selected))
        
        if data_file is None or windows_folder is None:
            self.game_root_folder = None
            self.data_unity3d_path = None
            self.standalone_windows64_path = None
            self.folder_var.set("Required files/folders not found")
            self.status_var.set("Link failed")
            messagebox.showwarning(
                "Invalid folder",
                "Could not find both data.unity3d and StandaloneWindows64 folder.\n\n"
                "Make sure you selected the correct Stumble Guys (v0.73) installation.",
            )
            return

        self.game_root_folder = Path(selected)
        self.data_unity3d_path = data_file
        self.standalone_windows64_path = windows_folder
        self.folder_var.set(f"Linked: Stumble Guys (v0.73)")
        self.status_var.set("Folder linked")
        messagebox.showinfo(
            "Folder linked",
            f"Found files successfully!"
        )

    def start_swap(self) -> None:
        if self.game_root_folder is None:
            messagebox.showwarning("No folder linked", "Link a folder first.")
            return

        # Get all selected packs + always include Data File
        optional_selected = [pack for pack, var in self.pack_selections.items() if var.get()]
        self.selected_packs = optional_selected + ["Data File"]

        # Verify all selected packs exist
        for pack_name in self.selected_packs:
            bundle_folder_name = self.texture_packs[pack_name]
            pack_folder = self.base_dir / "Textures" / bundle_folder_name
            if not pack_folder.exists():
                messagebox.showwarning(
                    "Source files not found",
                    f"Texture pack '{pack_name}' not found at: {pack_folder}",
                )
                return

        if not self.standalone_windows64_path.exists() or not self.data_unity3d_path.exists():
            messagebox.showwarning(
                "Target files not found",
                "StandaloneWindows64 folder or data.unity3d not found in game folder.",
            )
            return

        self._set_action_buttons("disabled")
        self.inject_button.config(text="➤  INJECTING...")

        thread = threading.Thread(target=self._swap_worker, daemon=True)
        thread.start()

    def start_restore(self) -> None:
        if self.game_root_folder is None:
            messagebox.showwarning("No folder linked", "Link a folder first.")
            return

        if not self.standalone_windows64_path.exists() or not self.data_unity3d_path.exists():
            messagebox.showwarning(
                "Target files not found",
                "StandaloneWindows64 folder or data.unity3d not found in game folder.",
            )
            return

        self._set_action_buttons("disabled")
        self.remove_button.config(text="↻  RESTORING...")

        thread = threading.Thread(target=self._restore_worker, daemon=True)
        thread.start()

    def _set_action_buttons(self, state: str) -> None:
        self.inject_button.config(state=state)
        self.remove_button.config(state=state)

    def _swap_worker(self) -> None:
        """
        Worker thread for texture injection.
        Creates backups of original files before replacement to enable restoration.
        This operation is fully reversible via the restore function.
        """
        try:
            # Create backup directory for storing original game files (recovery mechanism)
            backup_dir = self.game_root_folder / ".texture_backups"
            backup_dir.mkdir(exist_ok=True)
            
            total_replaced = 0
            
            # Process each selected pack - user-initiated texture replacement
            for pack_name in self.selected_packs:
                bundle_folder_name = self.texture_packs[pack_name]
                pack_folder = self.base_dir / "Textures" / bundle_folder_name
                
                if not pack_folder.exists():
                    raise FileNotFoundError(f"Pack '{pack_name}' folder not found: {pack_folder}")
                
                # Special handling for Data File (game asset replacement)
                if pack_name == "Data File":
                    data_file_source = pack_folder / "data.unity3d"
                    if not data_file_source.exists():
                        raise FileNotFoundError(f"data.unity3d not found in {pack_folder}")
                    
                    # Preserve original by creating backup copy (safety mechanism)
                    if not (backup_dir / "data.unity3d").exists():
                        shutil.copy2(data_file_source, backup_dir / "data.unity3d")
                    
                    # Replace game asset with user-selected texture
                    # Using copy2 preserves metadata (safer than direct replacement)
                    shutil.copy2(data_file_source, self.data_unity3d_path)
                    total_replaced += 1
                else:
                    # Handle bundle files in StandaloneWindows64 directory
                    bundle_files = [f for f in pack_folder.iterdir() if f.is_file()]
                    
                    if not bundle_files:
                        raise FileNotFoundError(f"No bundle files found in {pack_folder}")
                    
                    # For each bundle file, find and replace matching file in game folder
                    for source_bundle in bundle_files:
                        bundle_name = source_bundle.name
                        target_bundle = self._find_bundle_by_name(self.standalone_windows64_path, bundle_name)
                        
                        if target_bundle:
                            # Preserve original as backup (enables restoration)
                            if not (backup_dir / target_bundle.name).exists():
                                shutil.copy2(target_bundle, backup_dir / target_bundle.name)
                            
                            # Replace with user-selected texture bundle
                            # Using copy2 preserves file attributes and timestamps
                            shutil.copy2(source_bundle, target_bundle)
                            total_replaced += 1
            
            if total_replaced == 0:
                raise FileNotFoundError(f"No matching bundles found in game folder")

            self.root.after(0, self._swap_success)
        except Exception as error:
            self.root.after(0, lambda: self._swap_failed(error))

    def _restore_worker(self) -> None:
        """
        Worker thread for restoring original game files from backups.
        Removes backup directory after successful restoration.
        """
        try:
            # Look for backup directory created during injection
            backup_dir = self.game_root_folder / ".texture_backups"
            
            if backup_dir.exists():
                # Restore all backed up files to their original locations
                for backup_file in backup_dir.iterdir():
                    if backup_file.is_file():
                        if backup_file.name == "data.unity3d":
                            # Restore data.unity3d to its original location
                            if self.data_unity3d_path.exists():
                                self.data_unity3d_path.unlink()
                            shutil.copy2(backup_file, self.data_unity3d_path)
                        else:
                            # Restore bundles to StandaloneWindows64
                            target_file = self.standalone_windows64_path / backup_file.name
                            if target_file.exists():
                                target_file.unlink()
                            shutil.copy2(backup_file, target_file)
                # Delete backup folder after successful restoration
                shutil.rmtree(backup_dir)
            else:
                raise FileNotFoundError(
                    "No backup files found. Install the original game files to restore."
                )

            self.root.after(0, self._restore_success)
        except Exception as error:
            self.root.after(0, lambda: self._restore_failed(error))

    def _swap_success(self) -> None:
        self._set_action_buttons("normal")
        self.inject_button.config(text="➤  INJECT SELECTED")
        self.status_var.set("Done")
        packs_list = ", ".join(self.selected_packs)
        messagebox.showinfo("Success", f"Textures injected successfully!\n\nInjected: {packs_list}")

    def _swap_failed(self, error: Exception) -> None:
        self._set_action_buttons("normal")
        self.inject_button.config(text="➤  INJECT SELECTED")
        self.status_var.set("Injection failed")
        messagebox.showerror("Injection failed", str(error))

    def _restore_success(self) -> None:
        self._set_action_buttons("normal")
        self.remove_button.config(text="↻  RESTORE ORIGINAL")
        self.status_var.set("Restored")
        messagebox.showinfo("Success", "Original files restored successfully!")

    def _restore_failed(self, error: Exception) -> None:
        self._set_action_buttons("normal")
        self.remove_button.config(text="↻  RESTORE ORIGINAL")
        self.status_var.set("Restore failed")
        messagebox.showerror("Restore failed", str(error))


def main() -> None:
    root = tk.Tk()
    app = InjectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()