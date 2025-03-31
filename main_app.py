import tkinter as tk
from tkinter import ttk
import os
import sys
from PIL import Image, ImageTk
import matplotlib
matplotlib.use("TkAgg")  # Set matplotlib backend

# Import modules
from thread_simulator import ThreadSimulator
from deadlock_visualizer import DeadlockVisualizer

class MultiThreadingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Multi-Threading & Deadlock Simulator")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use clam theme as base
        
        # Configure colors
        self.style.configure('.',
                            background='white',
                            foreground='black',
                            font=('Segoe UI', 12))
        self.style.configure('TFrame', background='white')
        self.style.configure('TButton', 
                            background='#2980B9', 
                            foreground='white',
                            font=('Segoe UI', 12, 'bold'),
                            padding=5)
        self.style.map('TButton',
                      background=[('active', '#3498DB'), ('pressed', '#1A5276')])
        self.style.configure('Heading.TLabel', 
                            font=('Segoe UI', 14, 'bold'),
                            background='white')
        self.style.configure('Nav.TButton', 
                            font=('Segoe UI', 12),
                            padding=10,
                            width=20)
        
        # Create main layout
        self.create_layout()
        
        # Load and display logo
        self.load_logo()
        
        # Initialize current module
        self.current_module = None
        
    def create_layout(self):
        # Main container
        self.main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Navigation panel (left)
        self.nav_panel = ttk.Frame(self.main_container, width=220)
        self.main_container.add(self.nav_panel, weight=0)
        
        # Content area (right)
        self.content_area = ttk.Frame(self.main_container)
        self.main_container.add(self.content_area, weight=1)
        
        # Configure navigation panel
        self.setup_navigation()
        
    def setup_navigation(self):
        # Navigation heading
        nav_heading = ttk.Label(self.nav_panel, text="MODULES", style='Heading.TLabel')
        nav_heading.pack(pady=(20, 10), padx=10, anchor=tk.W)
        
        # Separator
        separator = ttk.Separator(self.nav_panel, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, padx=10, pady=5)
        
        # Thread Simulator button
        thread_btn = ttk.Button(self.nav_panel, 
                               text="Thread Simulator", 
                               style='Nav.TButton',
                               command=lambda: self.show_module("thread"))
        thread_btn.pack(pady=5, padx=10, fill=tk.X)
        
        # Deadlock Visualizer button
        deadlock_btn = ttk.Button(self.nav_panel, 
                                 text="Deadlock Visualizer", 
                                 style='Nav.TButton',
                                 command=lambda: self.show_module("deadlock"))
        deadlock_btn.pack(pady=5, padx=10, fill=tk.X)
        
    def load_logo(self):
        # Create a canvas for the logo
        self.logo_canvas = tk.Canvas(self.content_area, bg='white', highlightthickness=0)
        self.logo_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create a simple logo (in a real app, you'd load an image)
        self.logo_canvas.create_text(
            self.winfo_width() // 2,
            self.winfo_height() // 2,
            text="MT&DS",
            font=('Segoe UI', 48, 'bold'),
            fill='#CCCCCC'
        )
        
        # Bind resize event to update logo position
        self.logo_canvas.bind('<Configure>', self.update_logo_position)
        
    def update_logo_position(self, event):
        # Update logo position when window is resized
        self.logo_canvas.delete("all")
        self.logo_canvas.create_text(
            event.width // 2,
            event.height // 2,
            text="MT&DS",
            font=('Segoe UI', 48, 'bold'),
            fill='#CCCCCC'
        )
        
    def show_module(self, module_name):
        # Clear content area
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        # Show selected module
        if module_name == "thread":
            self.current_module = ThreadSimulator(self.content_area)
        elif module_name == "deadlock":
            self.current_module = DeadlockVisualizer(self.content_area)
            
        # Pack the module's frame
        if self.current_module:
            self.current_module.frame.pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    app = MultiThreadingApp()
    app.mainloop()