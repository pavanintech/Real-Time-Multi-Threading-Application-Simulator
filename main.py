import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
import random
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class ThreadSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time Multi-Threading Simulator")
        self.root.geometry("900x700")

        try:
            self.root.iconbitmap('app_icon.ico')
        except:
            pass
        
        # Thread management
        self.threads = []
        self.running = False
        self.task_queue = queue.Queue()
        self.results = []
        
        # Create GUI
        self.create_widgets()
        
        # Start the GUI update thread
        self.update_thread = threading.Thread(target=self.update_gui, daemon=True)
        self.update_thread.start()
    
    def create_widgets(self):
        # Control panel
        control_frame = ttk.LabelFrame(self.root, text="Thread Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Thread count control
        ttk.Label(control_frame, text="Number of Threads:").grid(row=0, column=0, sticky=tk.W)
        self.thread_count = tk.IntVar(value=4)
        ttk.Spinbox(control_frame, from_=1, to=16, textvariable=self.thread_count, width=5).grid(row=0, column=1, sticky=tk.W)
        
        # Task count control
        ttk.Label(control_frame, text="Number of Tasks:").grid(row=1, column=0, sticky=tk.W)
        self.task_count = tk.IntVar(value=20)
        ttk.Spinbox(control_frame, from_=1, to=100, textvariable=self.task_count, width=5).grid(row=1, column=1, sticky=tk.W)
        
        # Start/Stop buttons
        ttk.Button(control_frame, text="Start Simulation", command=self.start_simulation).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="Stop Simulation", command=self.stop_simulation).grid(row=0, column=3, padx=5)
        ttk.Button(control_frame, text="Clear Results", command=self.clear_results).grid(row=1, column=2, columnspan=2)
        
        # Thread status display
        status_frame = ttk.LabelFrame(self.root, text="Thread Status", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.status_text = tk.Text(status_frame, height=10, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Results visualization
        viz_frame = ttk.LabelFrame(self.root, text="Performance Visualization", padding=10)
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.figure, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
    
    def worker(self, thread_id):
        while self.running:
            try:
                # Get task from queue with timeout to allow thread to check running status
                task_num = self.task_queue.get(timeout=0.1)
                
                # Simulate work with random duration
                work_time = random.uniform(0.5, 2.5)
                time.sleep(work_time)
                
                # Record result
                self.results.append((thread_id, task_num, work_time))
                
                # Update queue task done
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
    
    def start_simulation(self):
        if self.running:
            messagebox.showwarning("Warning", "Simulation is already running!")
            return
        
        # Clear previous results
        self.results = []
        self.ax.clear()
        
        # Initialize task queue
        for i in range(self.task_count.get()):
            self.task_queue.put(i)
        
        # Set running flag
        self.running = True
        
        # Create and start worker threads
        self.threads = []
        for i in range(self.thread_count.get()):
            thread = threading.Thread(target=self.worker, args=(i,), daemon=True)
            thread.start()
            self.threads.append(thread)
        
        # Update progress bar
        self.progress["maximum"] = self.task_count.get()
        self.progress["value"] = 0
    
    def stop_simulation(self):
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=0.5)
        
        self.threads = []
        self.task_queue = queue.Queue()  # Clear the queue
    
    def clear_results(self):
        self.results = []
        self.ax.clear()
        self.canvas.draw()
        self.update_status_text()
        self.progress["value"] = 0
    
    def update_status_text(self):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        
        if not self.results:
            self.status_text.insert(tk.END, "No tasks completed yet.")
        else:
            # Group results by thread
            thread_stats = {}
            for thread_id, task_num, work_time in self.results:
                if thread_id not in thread_stats:
                    thread_stats[thread_id] = {'count': 0, 'total_time': 0}
                thread_stats[thread_id]['count'] += 1
                thread_stats[thread_id]['total_time'] += work_time
            
            # Display stats
            for thread_id, stats in thread_stats.items():
                avg_time = stats['total_time'] / stats['count']
                self.status_text.insert(tk.END, 
                    f"Thread {thread_id}: Completed {stats['count']} tasks, "
                    f"Avg time: {avg_time:.2f}s, Total time: {stats['total_time']:.2f}s\n")
            
            # Show queue status
            remaining = self.task_queue.qsize()
            completed = len(self.results)
            total = self.task_count.get()
            self.status_text.insert(tk.END, 
                f"\nTasks: {completed}/{total} completed, {remaining} remaining in queue\n")
        
        self.status_text.config(state=tk.DISABLED)
    
    def update_visualization(self):
        self.ax.clear()
        
        if not self.results:
            self.ax.text(0.5, 0.5, "No data to display", 
                         ha='center', va='center')
            self.canvas.draw()
            return
        
        # Prepare data for visualization
        thread_ids = sorted(set(r[0] for r in self.results))
        colors = plt.cm.get_cmap('tab10', len(thread_ids))
        
        # Plot each thread's tasks
        for thread_id in thread_ids:
            thread_tasks = [r for r in self.results if r[0] == thread_id]
            task_nums = [r[1] for r in thread_tasks]
            durations = [r[2] for r in thread_tasks]
            
            self.ax.barh([f"Thread {thread_id}"], sum(durations), 
                        left=0, color=colors(thread_id), alpha=0.6)
            
            # Add markers for individual tasks
            cumulative = 0
            for i, duration in enumerate(durations):
                self.ax.barh([f"Thread {thread_id}"], duration, 
                            left=cumulative, color=colors(thread_id), 
                            edgecolor='black', alpha=0.8)
                cumulative += duration
        
        self.ax.set_xlabel('Time (seconds)')
        self.ax.set_title('Thread Work Distribution')
        self.canvas.draw()
    
    def update_gui(self):
        while True:
            if self.running:
                # Update progress
                completed = len(self.results)
                total = self.task_count.get()
                self.progress["value"] = completed
                
                # Check if all tasks are done
                if completed >= total:
                    self.running = False
            
            # Update status and visualization
            self.update_status_text()
            self.update_visualization()
            
            # Sleep to prevent high CPU usage
            time.sleep(0.5)

if __name__ == "__main__":
    root = tk.Tk()
    app = ThreadSimulatorApp(root)
    root.mainloop()