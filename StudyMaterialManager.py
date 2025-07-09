import customtkinter as ctk
import tkinter as tk
import sqlite3
import os
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox
from typing import List, Tuple, Optional
from tkinterdnd2 import TkinterDnD, DND_FILES
from drive_service import DriveService
import threading
from pathlib import Path

# === Theme Setup ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Custom colors
COLORS = {
    "primary": "#1a73e8",
    "primary_hover": "#1557b0",
    "success": "#34a853",
    "success_hover": "#2d9249",
    "warning": "#fbbc05",
    "warning_hover": "#e0a800",
    "danger": "#ea4335",
    "danger_hover": "#d33426",
    "info": "#4285f4",
    "info_hover": "#3367d6",
    "secondary": "#5f6368",
    "secondary_hover": "#4a4d50",
    "bg_dark": "#202124",
    "bg_light": "#292a2d",
    "text_primary": "#ffffff",
    "text_secondary": "#9aa0a6"
}

# === DB Setup ===
class DatabaseManager:
    def __init__(self, db_name: str = 'study_materials.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            tags TEXT,
            file_path TEXT,
            date_added TEXT,
            last_modified TEXT
        )
        ''')
        self.conn.commit()
    
    def add_material(self, title: str, content: str, tags: str, file_path: str) -> int:
        """Add new material to database and return its ID"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO materials (title, content, tags, file_path, date_added, last_modified) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, content, tags, file_path, now, now)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_material(self, material_id: int, title: str, content: str, tags: str, file_path: str):
        """Update existing material"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE materials SET title=?, content=?, tags=?, file_path=?, last_modified=? "
            "WHERE id=?",
            (title, content, tags, file_path, now, material_id)
        )
        self.conn.commit()
    
    def delete_material(self, material_id: int):
        """Delete material from database"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM materials WHERE id=?", (material_id,))
        self.conn.commit()
    
    def get_material(self, material_id: int) -> Optional[Tuple]:
        """Get single material by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM materials WHERE id=?", (material_id,))
        return cursor.fetchone()
    
    def search_materials(self, query: str = "") -> List[Tuple]:
        """Search materials by title or tags"""
        cursor = self.conn.cursor()
        if query:
            query = f"%{query.lower()}%"
            cursor.execute(
                "SELECT * FROM materials WHERE LOWER(title) LIKE ? OR LOWER(tags) LIKE ? "
                "ORDER BY last_modified DESC",
                (query, query)
            )
        else:
            cursor.execute("SELECT * FROM materials ORDER BY last_modified DESC")
        return cursor.fetchall()
    
    def close(self):
        """Close database connection"""
        self.conn.close()

# Initialize database
db = DatabaseManager()
drive_service: Optional[DriveService] = None

def connect_to_drive():
    def auth_flow():
        global drive_service
        try:
            drive_service = DriveService()
            status_var.set("Google Drive connected successfully.")
            drive_button.configure(text="Drive Connected", fg_color=COLORS["success"], hover_color=COLORS["success_hover"])
        except Exception as e:
            messagebox.showerror("Google Drive Error", f"Failed to connect to Google Drive: {e}")
            status_var.set("Google Drive connection failed.")
            drive_button.configure(text="Connect to Drive", fg_color=COLORS["info"], hover_color=COLORS["info_hover"])

    status_var.set("Connecting to Google Drive...")
    threading.Thread(target=auth_flow, daemon=True).start()

# === Functions ===
def add_material(material_id: int = None):
    """Add or edit material with a modal dialog"""
    is_edit = material_id is not None
    material = db.get_material(material_id) if is_edit else None
    
    def save():
        title = entry_title.get().strip()
        content = text_content.get("1.0", "end").strip()
        tags = entry_tags.get().strip()
        file_path = entry_file.get().strip()
        
        if not title:
            messagebox.showwarning("Missing", "Title is required.", parent=top)
            return
            
        try:
            if drive_service and file_path and os.path.exists(file_path):
                status_var.set(f"Uploading {os.path.basename(file_path)} to Google Drive...")
                file_id = drive_service.upload_file(file_path, os.path.basename(file_path))
                file_path = file_id
                status_var.set("File uploaded successfully.")

            if is_edit:
                db.update_material(material_id, title, content, tags, file_path)
                messagebox.showinfo("Success", "Material updated successfully!", parent=top)
            else:
                db.add_material(title, content, tags, file_path)
                messagebox.showinfo("Success", "Material added successfully!", parent=top)
            
            top.destroy()
            refresh_list()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}", parent=top)

    def choose_file():
        filepath = filedialog.askopenfilename(
            title="Select File",
            filetypes=[
                ("All Files", "*.* "),
                ("PDFs", "*.pdf"),
                ("Documents", "*.docx *.txt"),
                ("Images", "*.png *.jpg *.jpeg"),
                ("Videos", "*.mp4 *.avi *.mov")
            ]
        )
        if filepath:
            entry_file.delete(0, "end")
            entry_file.insert(0, filepath)
            update_file_preview(filepath)

    def clear_file():
        entry_file.delete(0, "end")
        file_preview.configure(text="No file selected", image=None)

    def update_file_preview(filepath: str):
        """Update the file preview with appropriate icon"""
        if not filepath:
            file_preview.configure(text="No file selected", image=None)
            return
            
        filename = os.path.basename(filepath)
        file_preview.configure(text=filename)
        
    def handle_drop(event):
        """Handle files dropped on the drop target"""
        filepath = event.data.strip()
        
        if filepath.startswith('{') and filepath.endswith('}'):
            filepath = filepath[1:-1]
        
        if '\n' in filepath:
            filepath = filepath.split('\n')[0]
        
        if os.path.isfile(filepath):
            entry_file.delete(0, "end")
            entry_file.insert(0, filepath)
            update_file_preview(filepath)
            status_var.set(f"File added: {os.path.basename(filepath)}")
        else:
            messagebox.showerror("Error", "Dropped item is not a valid file", parent=top)

    top = ctk.CTkToplevel(root)
    top.title("Edit Material" if is_edit else "Add Material")
    top.geometry("700x800")
    top.grab_set()
    top.configure(fg_color=COLORS["bg_dark"])

    # Main content frame
    content_frame = ctk.CTkFrame(top, fg_color=COLORS["bg_light"], corner_radius=10)
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Title
    ctk.CTkLabel(
        content_frame, 
        text="Title*:", 
        font=root.header_font,
        text_color=COLORS["text_primary"]
    ).pack(pady=(20, 5))
    
    entry_title = ctk.CTkEntry(
        content_frame, 
        width=600,
        height=35,
        font=root.text_font,
        corner_radius=8,
        fg_color=COLORS["bg_dark"],
        border_color=COLORS["primary"],
        text_color=COLORS["text_primary"]
    )
    entry_title.pack()
    if is_edit and material:
        entry_title.insert(0, material[1])

    # Tags
    ctk.CTkLabel(
        content_frame, 
        text="Tags (comma-separated):", 
        font=root.header_font,
        text_color=COLORS["text_primary"]
    ).pack(pady=(20, 5))
    
    entry_tags = ctk.CTkEntry(
        content_frame, 
        width=600,
        height=35,
        font=root.text_font,
        corner_radius=8,
        fg_color=COLORS["bg_dark"],
        border_color=COLORS["primary"],
        text_color=COLORS["text_primary"]
    )
    entry_tags.pack()
    if is_edit and material:
        entry_tags.insert(0, material[3] if material[3] else "")

    # Content
    ctk.CTkLabel(
        content_frame, 
        text="Content:", 
        font=root.header_font,
        text_color=COLORS["text_primary"]
    ).pack(pady=(20, 5))
    
    text_content = ctk.CTkTextbox(
        content_frame, 
        width=600, 
        height=200,
        font=root.text_font,
        corner_radius=8,
        fg_color=COLORS["bg_dark"],
        border_color=COLORS["primary"],
        text_color=COLORS["text_primary"]
    )
    text_content.pack()
    if is_edit and material:
        text_content.insert("1.0", material[2] if material[2] else "")

    # File Attachment Section
    ctk.CTkLabel(
        content_frame, 
        text="Attach File:", 
        font=root.header_font,
        text_color=COLORS["text_primary"]
    ).pack(pady=(20, 5))
    
    # Drop target frame
    drop_frame = ctk.CTkFrame(
        content_frame, 
        width=600, 
        height=100, 
        fg_color=COLORS["bg_dark"],
        corner_radius=8,
        border_width=2,
        border_color=COLORS["primary"]
    )
    drop_frame.pack(pady=(0, 10))
    
    # File preview label
    file_preview = ctk.CTkLabel(
        drop_frame,
        text="Drag & drop file here or click 'Browse'",
        font=root.text_font,
        text_color=COLORS["text_secondary"],
        compound="top",
        justify="center"
    )
    file_preview.pack(expand=True, fill="both", padx=10, pady=10)
    
    # Make the frame a drop target
    drop_frame.drop_target_register(DND_FILES)
    drop_frame.dnd_bind('<<Drop>>', handle_drop)
    
    # File entry and buttons
    file_control_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    file_control_frame.pack(fill="x", padx=10)
    
    entry_file = ctk.CTkEntry(
        file_control_frame, 
        width=450,
        height=35,
        font=root.text_font,
        corner_radius=8,
        fg_color=COLORS["bg_dark"],
        border_color=COLORS["primary"],
        text_color=COLORS["text_primary"]
    )
    entry_file.pack(side="left", padx=(0, 5))
    if is_edit and material and material[4]:
        entry_file.insert(0, material[4])
        update_file_preview(material[4])
    
    ctk.CTkButton(
        file_control_frame,
        text="Browse",
        width=100,
        height=35,
        font=root.text_font,
        corner_radius=8,
        fg_color=COLORS["info"],
        hover_color=COLORS["info_hover"],
        command=choose_file
    ).pack(side="left", padx=(0, 5))
    
    ctk.CTkButton(
        file_control_frame,
        text="Clear",
        width=100,
        height=35,
        font=root.text_font,
        corner_radius=8,
        fg_color=COLORS["secondary"],
        hover_color=COLORS["secondary_hover"],
        command=clear_file
    ).pack(side="left")

    # Buttons
    btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    btn_frame.pack(pady=20)
    
    ctk.CTkButton(
        btn_frame, 
        text="Save", 
        command=save,
        width=120,
        height=35,
        font=root.text_font,
        corner_radius=8,
        fg_color=COLORS["success"] if not is_edit else COLORS["primary"],
        hover_color=COLORS["success_hover"] if not is_edit else COLORS["primary_hover"]
    ).pack(side="left", padx=10)
    
    ctk.CTkButton(
        btn_frame, 
        text="Cancel", 
        command=top.destroy,
        width=120,
        height=35,
        font=root.text_font,
        corner_radius=8,
        fg_color=COLORS["secondary"],
        hover_color=COLORS["secondary_hover"]
    ).pack(side="left", padx=10)

def view_material():
    """View material details in a formatted dialog"""
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a material first.", parent=root)
        return
        
    material = materials[selected[0]]
    
    # Create detailed view window
    view_window = ctk.CTkToplevel(root)
    view_window.title(f"View: {material[1]}")
    view_window.geometry("800x700")
    view_window.configure(fg_color=COLORS["bg_dark"])
    
    # Main frame with scrollbar
    main_frame = ctk.CTkFrame(view_window, fg_color=COLORS["bg_light"], corner_radius=10)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Scrollable canvas
    canvas = tk.Canvas(main_frame, bg=COLORS["bg_light"], highlightthickness=0)
    scrollbar = ctk.CTkScrollbar(main_frame, orientation="vertical", command=canvas.yview, button_color=COLORS["primary"])
    scrollable_frame = ctk.CTkFrame(canvas, fg_color=COLORS["bg_light"])
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    scrollbar.pack(side="right", fill="y", pady=10)
    
    # Display material details
    details = [
        ("Title", material[1]),
        ("Tags", material[3] if material[3] else "None"),
        ("Date Added", material[5]),
        ("Last Modified", material[6] if material[6] else material[5]),
        ("Content", material[2] if material[2] else "No content")
    ]
    
    for label, value in details:
        frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            frame, 
            text=f"{label}:", 
            font=root.header_font,
            text_color=COLORS["text_primary"]
        ).pack(side="left", anchor="w")
        
        if label == "Content":
            content_text = ctk.CTkTextbox(
                frame, 
                width=700, 
                height=200, 
                wrap="word",
                font=root.text_font,
                corner_radius=8,
                fg_color=COLORS["bg_dark"],
                border_color=COLORS["primary"],
                text_color=COLORS["text_primary"]
            )
            content_text.pack(fill="x", pady=(10, 0))
            content_text.insert("1.0", value)
            content_text.configure(state="disabled")
        else:
            ctk.CTkLabel(
                frame, 
                text=value, 
                wraplength=700, 
                justify="left",
                font=root.text_font,
                text_color=COLORS["text_secondary"]
            ).pack(side="left", padx=10, anchor="w")
    
    # File attachment section
    if material[4]:
        file_frame = ctk.CTkFrame(scrollable_frame, fg_color=COLORS["bg_dark"], corner_radius=8)
        file_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            file_frame, 
            text="Attached File:", 
            font=root.header_font,
            text_color=COLORS["text_primary"]
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        file_name = "Loading..."
        if drive_service:
            try:
                file_name = drive_service.get_file_name(material[4])
            except Exception as e:
                file_name = "Error loading file name"
        else:
            file_name = os.path.basename(material[4])

        file_btn = ctk.CTkButton(
            file_frame,
            text=f"📄 {file_name}",
            command=lambda: open_attachment(material[4]),
            fg_color="transparent",
            hover_color=COLORS["bg_light"],
            anchor="w",
            text_color=COLORS["info"],
            font=root.text_font,
            height=35
        )
        file_btn.pack(fill="x", padx=15, pady=(0, 5))
        
        if not drive_service and not os.path.exists(material[4]):
            ctk.CTkLabel(
                file_frame, 
                text="⚠️ File not found at specified path", 
                text_color=COLORS["danger"],
                font=root.small_font
            ).pack(anchor="w", padx=15, pady=(0, 15))
    
    # Action buttons
    action_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
    action_frame.pack(fill="x", padx=20, pady=20)
    
    ctk.CTkButton(
        action_frame,
        text="Edit",
        command=lambda: [view_window.destroy(), add_material(material[0])],
        width=120,
        height=35,
        font=root.text_font,
        corner_radius=8,
        fg_color="#4a90e2",
        hover_color= "#357abd"
    ).pack(side="left", padx=5)
    
    ctk.CTkButton(
        action_frame,
        text="Delete",
        command=lambda: confirm_delete(material[0], view_window),
        width=120,
        height=35,
        font=root.text_font,
        corner_radius=8,
        fg_color=COLORS["danger"],
        hover_color=COLORS["danger_hover"]
    ).pack(side="left", padx=5)
    
    ctk.CTkButton(
        action_frame,
        text="Close",
        command=view_window.destroy,
        width=120,
        height=35,
        font=root.text_font,
        corner_radius=8,
        fg_color=COLORS["secondary"],
        hover_color=COLORS["secondary_hover"]
    ).pack(side="right", padx=5)

def open_attachment(file_path: str = None):
    """Open attached file with default application"""
    if file_path is None:
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a material first.", parent=root)
            return
        file_path = materials[selected[0]][4]
    
    if not file_path:
        messagebox.showwarning("No Attachment", "This material has no file attachment.", parent=root)
        return

    # Check if it's a local file path first
    if os.path.exists(file_path):
        try:
            webbrowser.open(file_path)
            return
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}", parent=root)
            return

    if drive_service:
        try:
            temp_dir = Path.home() / "StudyMaterialManager_Downloads"
            temp_dir.mkdir(exist_ok=True)
            file_name = drive_service.get_file_name(file_path)
            destination_path = temp_dir / file_name

            if destination_path.exists():
                webbrowser.open(str(destination_path))
            else:
                status_var.set(f"Downloading file from Google Drive...")
                drive_service.download_file(file_path, str(destination_path))
                webbrowser.open(str(destination_path))
                status_var.set("File downloaded and opened successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file from Google Drive: {str(e)}", parent=root)
            status_var.set("Error opening file from Google Drive.")
    else:
        messagebox.showwarning("File Not Found", 
                             f"The file was not found at:\n{file_path}\n\n"
                             "It may have been moved or deleted, or Google Drive is not connected.", 
                             parent=root)

def confirm_delete(material_id: int, parent_window=None):
    """Confirm before deleting material"""
    parent = parent_window if parent_window else root
    if messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete this material?\nThis action cannot be undone.",
        parent=parent
    ):
        db.delete_material(material_id)
        if parent_window:
            parent_window.destroy()
        refresh_list()
        messagebox.showinfo("Deleted", "Material deleted successfully.", parent=root)

def search_materials(event=None):
    """Search materials with optional event parameter for binding"""
    query = search_var.get().strip()
    refresh_list(query)

def refresh_list(query: str = ""):
    """Refresh the materials list with optional search query"""
    listbox.delete(0, "end")
    global materials
    materials = db.search_materials(query)
    
    if not materials:
        listbox.insert("end", "No materials found" if query else "No materials available")
        return
    
    for item in materials:
        # Format: Title — [Tags] (Modified Date)
        tags = f" — [{item[3]}]" if item[3] else ""
        modified = datetime.strptime(item[6] if item[6] else item[5], "%Y-%m-%d %H:%M")
        date_str = modified.strftime("(%m/%d/%Y)")
        listbox.insert("end", f"{item[1]}{tags} {date_str}")

def on_closing():
    """Handle window closing event"""
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        db.close()
        root.destroy()

# === GUI ===
class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)
        
        # Configure custom theme
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Configure fonts
        self.title_font = ("Segoe UI", 16, "bold")
        self.header_font = ("Segoe UI", 14, "bold")
        self.text_font = ("Segoe UI", 12)
        self.small_font = ("Segoe UI", 11)

# Use our custom class that inherits from both CTk and DnDWrapper
root = App()
root.title("📚 Study Material Manager")
root.geometry("1000x800")  # Slightly larger window

# Configure grid
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)

# Search Bar
search_frame = ctk.CTkFrame(root, height=60, fg_color=COLORS["bg_light"], corner_radius=10)
search_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
search_frame.grid_columnconfigure(1, weight=1)

ctk.CTkLabel(
    search_frame, 
    text="🔍 Search:", 
    font=root.header_font,
    text_color=COLORS["text_primary"]
).grid(row=0, column=0, padx=(15, 10), pady=15)

search_var = ctk.StringVar()
search_entry = ctk.CTkEntry(
    search_frame,
    textvariable=search_var,
    placeholder_text="Search by title or tags...",
    font=root.text_font,
    height=35,
    corner_radius=8,
    fg_color=COLORS["bg_dark"],
    border_color=COLORS["primary"],
    text_color=COLORS["text_primary"]
)
search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 15), pady=15)
search_entry.bind("<KeyRelease>", lambda e: search_materials())

# Main content area
main_frame = ctk.CTkFrame(root, fg_color=COLORS["bg_light"], corner_radius=10)
main_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_rowconfigure(0, weight=1)

# Listbox with scrollbar
list_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
list_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
list_frame.grid_columnconfigure(0, weight=1)
list_frame.grid_rowconfigure(0, weight=1)

scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical", button_color=COLORS["primary"])
scrollbar.grid(row=0, column=1, sticky="ns")

listbox = tk.Listbox(
    list_frame,
    width=100,
    height=25,
    font=root.text_font,
    selectbackground=COLORS["primary"],
    selectforeground=COLORS["text_primary"],
    activestyle="none",
    bg=COLORS["bg_dark"],
    fg=COLORS["text_primary"],
    borderwidth=0,
    highlightthickness=0,
    yscrollcommand=scrollbar.set
)
listbox.grid(row=0, column=0, sticky="nsew")
scrollbar.configure(command=listbox.yview)

# Bind double click to view material
listbox.bind("<Double-Button-1>", lambda e: view_material())

# Action buttons
btn_frame = ctk.CTkFrame(root, fg_color=COLORS["bg_light"], corner_radius=10)
btn_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))

def get_selected_id() -> Optional[int]:
    """Get ID of currently selected material"""
    selected = listbox.curselection()
    return materials[selected[0]][0] if selected else None

button_configs = [
    ("➕ Add", add_material, COLORS["success"], COLORS["success_hover"]),
    ("👁️ View", view_material, COLORS["primary"], COLORS["primary_hover"]),
    ("📂 Open File", open_attachment, COLORS["info"], COLORS["info_hover"]),
    ("✏️ Edit", lambda: add_material(get_selected_id()), "#4a90e2", "#357abd"),
    ("🗑️ Delete", lambda: confirm_delete(get_selected_id()), COLORS["danger"], COLORS["danger_hover"]),
    ("🔄 Refresh", lambda: refresh_list(), COLORS["secondary"], COLORS["secondary_hover"])
]

for i, (text, command, color, hover_color) in enumerate(button_configs):
    ctk.CTkButton(
        btn_frame,
        text=text,
        command=command,
        fg_color=color,
        hover_color=hover_color,
        width=120,
        height=35,
        corner_radius=8,
        font=root.text_font
    ).grid(row=0, column=i, padx=8, pady=8)

drive_button = ctk.CTkButton(
    btn_frame,
    text="Connect to Drive",
    command=connect_to_drive,
    fg_color=COLORS["info"],
    hover_color=COLORS["info_hover"],
    width=150,
    height=35,
    corner_radius=8,
    font=root.text_font
)
drive_button.grid(row=0, column=len(button_configs), padx=8, pady=8)

# Status bar
status_frame = ctk.CTkFrame(root, height=40, fg_color=COLORS["bg_light"], corner_radius=10)
status_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 15))
status_var = ctk.StringVar(value="Ready")
ctk.CTkLabel(
    status_frame, 
    textvariable=status_var, 
    anchor="w",
    font=root.small_font,
    text_color=COLORS["text_secondary"]
).pack(fill="x", padx=15)

# Initial load
refresh_list()

# Run the application
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
