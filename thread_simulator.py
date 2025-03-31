import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
import random
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class ThreadSimulator:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        
        # Thread simulation variables
        self.num_threads = tk.IntVar(value=4)
        self.num_tasks = tk.IntVar(value=20)
        self.task_queue = queue.Queue()
        self.threads = []
        self.running = False
        self.thread_status = {}  # To track thread status
        self.thread_history = {}  # To track thread history for visualization
        self.start_time = 0
        
        # Create UI components
        self.create_control_panel()
        self.create_visualization_area()
        
    def create_control_panel(self):
        # Control panel frame
        control_frame = ttk.Frame(self.frame, padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Thread configuration
        thread_label = ttk.Label(control_frame, text="Worker Threads:")
        thread_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        thread_spinbox = ttk.Spinbox(control_frame, from_=1, to=16, textvariable=self.num_threads, width=5)
        thread_spinbox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Task configuration
        task_label = ttk.Label(control_frame, text="Tasks:")
        task_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        task_spinbox = ttk.Spinbox(control_frame, from_=1, to=100, textvariable=self.num_tasks, width=5)
        task_spinbox.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Control buttons
        self.start_button = ttk.Button(control_frame, text="Start", command=self.start_simulation)
        self.start_button.grid(row=0, column=4, padx=5, pady=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=5, padx=5, pady=5)
        
        self.clear_button = ttk.Button(control_frame, text="Clear", command=self.clear_simulation)
        self.clear_button.grid(row=0, column=6, padx=5, pady=5)
        
    def create_visualization_area(self):
        # Visualization frame
        viz_frame = ttk.Frame(self.frame, padding=10)
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Timeline visualization (Matplotlib)
        timeline_frame = ttk.LabelFrame(viz_frame, text="Thread Activity Timeline", padding=10)
        timeline_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=timeline_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize empty plot
        self.update_timeline()
        
        # Progress frame
        progress_frame = ttk.Frame(viz_frame, padding=10)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Overall progress bar
        progress_label = ttk.Label(progress_frame, text="Overall Progress:")
        progress_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=400)
        self.progress_bar.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        progress_frame.columnconfigure(1, weight=1)
        
        # Status text area
        status_frame = ttk.LabelFrame(viz_frame, text="Status Updates", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_text = tk.Text(status_frame, height=8, width=50, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(status_frame, command=self.status_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # Make text read-only
        self.status_text.config(state=tk.DISABLED)
        
    def update_timeline(self):
        self.ax.clear()
        
        if not self.thread_history:
            self.ax.set_title("No thread activity data")
            self.ax.text(0.5, 0.5, "Start simulation to see thread activity", 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes)
        else:
            # Plot thread activity
            current_time = time.time() - self.start_time
            
            y_ticks = []
            y_labels = []
            
            for thread_id, events in self.thread_history.items():
                y_pos = thread_id
                y_ticks.append(y_pos)
                y_labels.append(f"Thread {thread_id}")
                
                # Plot active periods
                for start, end, task_id in events:
                    if end is None:  # Still active
                        end = current_time
                    self.ax.barh(y_pos, end - start, left=start, height=0.5, 
                                color='#2980B9', alpha=0.7)
                    
                    # Add task label if there's enough space
                    if end - start > 0.3:
                        self.ax.text(start + (end - start) / 2, y_pos, f"Task {task_id}",
                                    ha='center', va='center', color='white', fontsize=8)
            
            self.ax.set_yticks(y_ticks)
            self.ax.set_yticklabels(y_labels)
            self.ax.set_xlabel("Time (seconds)")
            self.ax.set_title("Thread Activity Timeline")
            self.ax.grid(True, axis='x', linestyle='--', alpha=0.7)
            
            # Set x-axis limits
            self.ax.set_xlim(0, max(current_time, 1))
        
        self.canvas.draw()
        
    def log_status(self, message):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        
    def worker_thread(self, thread_id):
        self.thread_status[thread_id] = "idle"
        self.thread_history[thread_id] = []
        
        while self.running:
            try:
                # Get task with timeout to allow thread to check if simulation is still running
                task_id = self.task_queue.get(timeout=0.1)
                
                # Log start of task
                self.log_status(f"Thread {thread_id} started task {task_id}")
                self.thread_status[thread_id] = f"processing task {task_id}"
                
                # Record start time
                start_time = time.time() - self.start_time
                
                # Simulate work (random duration between 0.5 and 2 seconds)
                work_duration = random.uniform(0.5, 2.0)
                time.sleep(work_duration)
                
                # Record end time
                end_time = time.time() - self.start_time
                
                # Add to history
                self.thread_history[thread_id].append((start_time, end_time, task_id))
                
                # Log completion
                self.log_status(f"Thread {thread_id} completed task {task_id}")
                self.thread_status[thread_id] = "idle"
                
                # Mark task as done
                self.task_queue.task_done()
                
                # Update progress
                completed = self.num_tasks.get() - self.task_queue.qsize()
                progress = completed / self.num_tasks.get()
                self.progress_var.set(progress)
                
            except queue.Empty:
                # No tasks available, continue checking
                pass
            
            # Update visualization periodically
            if thread_id == 0:  # Only one thread should update the UI
                self.update_ui()
                
    def update_ui(self):
        # This method is called from the worker thread
        # We need to use after() to update the UI from the main thread
        self.frame.after(100, self.update_timeline)
        
    def start_simulation(self):
        if self.running:
            return
            
        # Reset simulation
        self.clear_simulation()
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.running = True
        
        # Record start time
        self.start_time = time.time()
        
        # Create tasks
        for i in range(self.num_tasks.get()):
            self.task_queue.put(i)
            
        # Log start
        self.log_status(f"Starting simulation with {self.num_threads.get()} threads and {self.num_tasks.get()} tasks")
        
        # Create and start worker threads
        for i in range(self.num_threads.get()):
            thread = threading.Thread(target=self.worker_thread, args=(i,), daemon=True)
            self.threads.append(thread)
            thread.start()
            self.log_status(f"Started worker thread {i}")
            
        # Start a monitoring thread to update progress and check for completion
        self.monitor_thread = threading.Thread(target=self.monitor_simulation, daemon=True)
        self.monitor_thread.start()
        
    def monitor_simulation(self):
        while self.running and any(thread.is_alive() for thread in self.threads):
            # Check if all tasks are done
            if self.task_queue.empty() and all(status == "idle" for status in self.thread_status.values()):
                self.frame.after(0, self.simulation_complete)
                break
                
            # Sleep briefly
            time.sleep(0.1)
            
    def simulation_complete(self):
        if not self.running:
            return
            
        self.stop_simulation()
        self.log_status("Simulation completed successfully")
        messagebox.showinfo("Simulation Complete", "All tasks have been processed!")
        
    def stop_simulation(self):
        if not self.running:
            return
            
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(0.1)
                
        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # Log stop
        self.log_status("Simulation stopped")
        
        # Final UI update
        self.update_timeline()
        
    def clear_simulation(self):
        # Stop simulation if running
        if self.running:
            self.stop_simulation()
            
        # Clear data
        self.threads = []
        self.thread_status = {}
        self.thread_history = {}
        self.task_queue = queue.Queue()
        self.progress_var.set(0.0)
        
        # Clear status text
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        # Reset timeline
        self.update_timeline()
        
        # Log clear
        self.log_status("Simulation cleared")