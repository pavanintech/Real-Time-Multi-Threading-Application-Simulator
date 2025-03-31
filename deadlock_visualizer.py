import tkinter as tk
from tkinter import ttk
import time
import threading
import random
import numpy as np
import matplotlib
matplotlib.use("TkAgg")  # Set matplotlib backend
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx

class DeadlockVisualizer:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        
        # Deadlock visualization variables
        self.running = False
        self.paused = False
        self.animation_speed = tk.DoubleVar(value=1.0)
        self.current_scenario = tk.StringVar(value="Basic Deadlock")
        
        # Graph data
        self.G = nx.DiGraph()
        self.pos = {}  # Node positions
        self.node_colors = {}
        self.edge_colors = {}
        self.labels = {}
        
        # Animation variables
        self.animation_thread = None
        self.current_step = 0
        self.total_steps = 0
        self.scenarios = {
            "Basic Deadlock": self.scenario_basic_deadlock,
            "Hold and Wait": self.scenario_hold_and_wait,
            "Circular Wait": self.scenario_circular_wait,
            "Resource Hierarchy": self.scenario_resource_hierarchy
        }
        
        # Create UI components
        self.create_control_panel()
        self.create_visualization_area()
        self.create_info_panel()
        
        # Initialize with default scenario
        self.load_scenario(self.current_scenario.get())
        
    def create_control_panel(self):
        # Control panel frame
        control_frame = ttk.Frame(self.frame, padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Scenario selection
        scenario_label = ttk.Label(control_frame, text="Scenario:")
        scenario_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        scenario_combo = ttk.Combobox(control_frame, textvariable=self.current_scenario, 
                                     values=list(self.scenarios.keys()), state="readonly", width=20)
        scenario_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        scenario_combo.bind("<<ComboboxSelected>>", lambda e: self.load_scenario(self.current_scenario.get()))
        
        # Speed control
        speed_label = ttk.Label(control_frame, text="Speed:")
        speed_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        speed_scale = ttk.Scale(control_frame, from_=0.5, to=2.0, variable=self.animation_speed, 
                               orient=tk.HORIZONTAL, length=100)
        speed_scale.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Control buttons
        self.play_button = ttk.Button(control_frame, text="Play", command=self.play_animation)
        self.play_button.grid(row=0, column=4, padx=5, pady=5)
        
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self.pause_animation, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=5, padx=5, pady=5)
        
        self.reset_button = ttk.Button(control_frame, text="Reset", command=self.reset_animation)
        self.reset_button.grid(row=0, column=6, padx=5, pady=5)
        
    def create_visualization_area(self):
        # Visualization frame
        viz_frame = ttk.Frame(self.frame, padding=10)
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Graph visualization (Matplotlib)
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize empty graph
        self.update_graph()
        
        # Step indicator
        step_frame = ttk.Frame(viz_frame)
        step_frame.pack(fill=tk.X, pady=5)
        
        self.step_label = ttk.Label(step_frame, text="Step: 0 / 0")
        self.step_label.pack(side=tk.LEFT, padx=5)
        
        self.step_var = tk.IntVar(value=0)
        self.step_scale = ttk.Scale(step_frame, from_=0, to=10, variable=self.step_var, 
                                  orient=tk.HORIZONTAL, length=400)
        self.step_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.step_scale.bind("<ButtonRelease-1>", self.on_step_change)
        
    def create_info_panel(self):
        # Information panel
        info_frame = ttk.LabelFrame(self.frame, text="Deadlock Conditions", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Create condition indicators
        self.condition_vars = {
            "Mutual Exclusion": tk.BooleanVar(value=False),
            "Hold and Wait": tk.BooleanVar(value=False),
            "No Preemption": tk.BooleanVar(value=False),
            "Circular Wait": tk.BooleanVar(value=False)
        }
        
        self.condition_labels = {}
        
        for i, (condition, var) in enumerate(self.condition_vars.items()):
            frame = ttk.Frame(info_frame)
            frame.grid(row=i//2, column=i%2, padx=10, pady=5, sticky=tk.W)
            
            indicator = ttk.Label(frame, text="●", foreground="gray")
            indicator.pack(side=tk.LEFT, padx=(0, 5))
            
            label = ttk.Label(frame, text=condition)
            label.pack(side=tk.LEFT)
            
            self.condition_labels[condition] = indicator
            
        # Description text
        desc_frame = ttk.LabelFrame(self.frame, text="Description", padding=10)
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.desc_text = tk.Text(desc_frame, height=4, width=50, wrap=tk.WORD)
        self.desc_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(desc_frame, command=self.desc_text.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.desc_text.config(yscrollcommand=scrollbar.set)
        
        # Make text read-only
        self.desc_text.config(state=tk.DISABLED)
        
    def update_graph(self):
        self.ax.clear()
        
        if not self.G.nodes():
            self.ax.set_title("No graph data")
            self.ax.text(0.5, 0.5, "Select a scenario to visualize", 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes)
        else:
            # Draw nodes
            process_nodes = [n for n, d in self.G.nodes(data=True) if d.get('type') == 'process']
            resource_nodes = [n for n, d in self.G.nodes(data=True) if d.get('type') == 'resource']
            
            # Draw processes (circles)
            if process_nodes:
                nx.draw_networkx_nodes(self.G, self.pos, nodelist=process_nodes, 
                                      node_color=[self.node_colors.get(n, 'blue') for n in process_nodes],
                                      node_shape='o', node_size=500, ax=self.ax)
            
            # Draw resources (squares)
            if resource_nodes:
                nx.draw_networkx_nodes(self.G, self.pos, nodelist=resource_nodes, 
                                      node_color=[self.node_colors.get(n, 'blue') for n in resource_nodes],
                                      node_shape='s', node_size=400, ax=self.ax)
            
            # Draw edges
            allocation_edges = [(u, v) for u, v, d in self.G.edges(data=True) if d.get('type') == 'allocation']
            request_edges = [(u, v) for u, v, d in self.G.edges(data=True) if d.get('type') == 'request']
            
            # Draw allocation edges (solid)
            if allocation_edges:
                nx.draw_networkx_edges(self.G, self.pos, edgelist=allocation_edges, 
                                      edge_color=[self.edge_colors.get((u, v), 'black') for u, v in allocation_edges],
                                      width=2, ax=self.ax)
            
            # Draw request edges (dashed)
            if request_edges:
                nx.draw_networkx_edges(self.G, self.pos, edgelist=request_edges, 
                                      edge_color=[self.edge_colors.get((u, v), 'black') for u, v in request_edges],
                                      width=2, style='dashed', ax=self.ax)
            
            # Draw labels
            if self.labels:
                nx.draw_networkx_labels(self.G, self.pos, labels=self.labels, font_size=10, ax=self.ax)
            
            self.ax.set_title(f"Resource Allocation Graph - {self.current_scenario.get()}")
            
        # Remove axis
        self.ax.set_axis_off()
        
        # Update canvas
        self.canvas.draw()
        
    def update_conditions(self, conditions):
        for condition, value in conditions.items():
            self.condition_vars[condition].set(value)
            color = "gray"
            if value:
                color = "#E74C3C"  # Red for active condition
            self.condition_labels[condition].config(foreground=color)
            
    def update_description(self, text):
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, text)
        self.desc_text.config(state=tk.DISABLED)
        
    def load_scenario(self, scenario_name):
        # Reset animation state
        self.reset_animation()
        
        # Clear graph
        self.G = nx.DiGraph()
        self.pos = {}
        self.node_colors = {}
        self.edge_colors = {}
        self.labels = {}
        
        # Load selected scenario
        if scenario_name in self.scenarios:
            self.scenarios[scenario_name]()
            
        # Update UI
        self.update_graph()
        self.step_var.set(0)
        self.current_step = 0
        self.step_scale.config(to=self.total_steps)
        self.step_label.config(text=f"Step: {self.current_step} / {self.total_steps}")
        
    def play_animation(self):
        if self.running:
            return
            
        self.running = True
        self.paused = False
        
        # Update UI
        self.play_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        
        # Start animation thread
        self.animation_thread = threading.Thread(target=self.animation_loop, daemon=True)
        self.animation_thread.start()
        
    def pause_animation(self):
        self.paused = True
        self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        
    def reset_animation(self):
        # Stop animation if running
        self.running = False
        self.paused = False
        
        # Wait for thread to finish
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(0.1)
            
        # Reset to initial state
        self.current_step = 0
        self.step_var.set(0)
        
        # Update UI
        self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        
        # Reload current scenario
        if self.current_scenario.get() in self.scenarios:
            self.scenarios[self.current_scenario.get()]()
            self.update_graph()
            self.step_scale.config(to=self.total_steps)
            self.step_label.config(text=f"Step: {self.current_step} / {self.total_steps}")
        
    def animation_loop(self):
        while self.running and self.current_step < self.total_steps:
            if not self.paused:
                # Update step
                self.current_step += 1
                self.step_var.set(self.current_step)
                
                # Update UI from main thread
                self.frame.after(0, self.update_step, self.current_step)
                
                # Sleep based on animation speed
                time.sleep(1.0 / self.animation_speed.get())
            else:
                # When paused, just sleep briefly
                time.sleep(0.1)
                
        # Animation complete
        if self.current_step >= self.total_steps:
            self.frame.after(0, self.animation_complete)
            
    def animation_complete(self):
        self.running = False
        self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        
    def on_step_change(self, event):
        # User manually changed the step
        step = self.step_var.get()
        if step != self.current_step:
            self.current_step = step
            self.update_step(step)
            
    def update_step(self, step):
        # This method should be overridden by each scenario
        # to update the graph based on the current step
        self.step_label.config(text=f"Step: {step} / {self.total_steps}")
        
        # Update graph based on current scenario
        scenario = self.current_scenario.get()
        
        if scenario == "Basic Deadlock":
            self.update_basic_deadlock_step(step)
        elif scenario == "Hold and Wait":
            self.update_hold_and_wait_step(step)
        elif scenario == "Circular Wait":
            self.update_circular_wait_step(step)
        elif scenario == "Resource Hierarchy":
            self.update_resource_hierarchy_step(step)
            
    # Scenario implementations
    def scenario_basic_deadlock(self):
        # Initialize graph for basic deadlock scenario
        self.G.add_node('P1', type='process')
        self.G.add_node('P2', type='process')
        self.G.add_node('R1', type='resource')
        self.G.add_node('R2', type='resource')
        
        # Set initial positions
        self.pos = {
            'P1': (0, 1),
            'P2': (1, 1),
            'R1': (0, 0),
            'R2': (1, 0)
        }
        
        # Set labels
        self.labels = {
            'P1': 'Process 1',
            'P2': 'Process 2',
            'R1': 'Resource 1',
            'R2': 'Resource 2'
        }
        
        # Set initial colors
        for node in self.G.nodes():
            self.node_colors[node] = '#3498DB'  # Blue
            
        # Define animation steps
        self.total_steps = 6
        
        # Set initial description
        self.update_description("This scenario demonstrates a classic deadlock situation where two processes each hold one resource and request another, creating a circular wait condition.")
        
        # Set initial conditions
        self.update_conditions({
            "Mutual Exclusion": True,
            "Hold and Wait": False,
            "No Preemption": True,
            "Circular Wait": False
        })
        
    def update_basic_deadlock_step(self, step):
        # Reset graph to initial state
        for u, v in list(self.G.edges()):
            self.G.remove_edge(u, v)
            
        for node in self.G.nodes():
            self.node_colors[node] = '#3498DB'  # Blue
            
        # Update based on step
        if step >= 1:
            # P1 allocates R1
            self.G.add_edge('R1', 'P1', type='allocation')
            self.edge_colors[('R1', 'P1')] = '#2ECC71'  # Green
            
            self.update_description("Step 1: Process 1 acquires Resource 1.")
            self.update_conditions({
                "Mutual Exclusion": True,
                "Hold and Wait": False,
                "No Preemption": True,
                "Circular Wait": False
            })
            
        if step >= 2:
            # P2 allocates R2
            self.G.add_edge('R2', 'P2', type='allocation')
            self.edge_colors[('R2', 'P2')] = '#2ECC71'  # Green
            
            self.update_description("Step 2: Process 2 acquires Resource 2.")
            self.update_conditions({
                "Mutual Exclusion": True,
                "Hold and Wait": False,
                "No Preemption": True,
                "Circular Wait": False
            })
            
        if step >= 3:
            # P1 requests R2
            self.G.add_edge('P1', 'R2', type='request')
            self.edge_colors[('P1', 'R2')] = '#E74C3C'  # Red
            
            self.update_description("Step 3: Process 1 requests Resource 2 while holding Resource 1.")
            self.update_conditions({
                "Mutual Exclusion": True,
                "Hold and Wait": True,
                "No Preemption": True,
                "Circular Wait": False
            })
            
        if step >= 4:
            # P2 requests R1
            self.G.add_edge('P2', 'R1', type='request')
            self.edge_colors[('P2', 'R1')] = '#E74C3C'  # Red
            
            self.update_description("Step 4: Process 2 requests Resource 1 while holding Resource 2. A circular wait condition now exists.")
            self.update_conditions({
                "Mutual Exclusion": True,
                "Hold and Wait": True,
                "No Preemption": True,
                "Circular Wait": True
            })
            
        if step >= 5:
            # Deadlock detected
            self.node_colors['P1'] = '#E74C3C'  # Red
            self.node_colors['P2'] = '#E74C3C'  # Red
            self.node_colors['R1'] = '#F39C12'  # Orange
            self.node_colors['R2'] = '#F39C12'  # Orange
            
            self.update_description("Step 5: Deadlock detected! Both processes are waiting for resources held by the other, creating a circular wait. All four conditions for deadlock are now satisfied.")
            
        if step >= 6:
            # Potential resolution (not implemented in this basic scenario)
            self.update_description("Step 6: In a real system, deadlock could be resolved by: 1) Process termination, 2) Resource preemption, or 3) Rollback to a safe state. In this scenario, we simply detect the deadlock.")
            
        # Update graph
        self.update_graph()
        
    def scenario_hold_and_wait(self):
        # Initialize graph for hold and wait scenario
        self.G.add_node('P1', type='process')
        self.G.add_node('P2', type='process')
        self.G.add_node('P3', type='process')
        self.G.add_node('R1', type='resource')
        self.G.add_node('R2', type='resource')
        self.G.add_node('R3', type='resource')
        
        # Set initial positions
        self.pos = {
            'P1': (0, 1),
            'P2': (1, 1),
            'P3': (2, 1),
            'R1': (0, 0),
            'R2': (1, 0),
            'R3': (2, 0)
        }
        
        # Set labels
        self.labels = {
            'P1': 'Process 1',
            'P2': 'Process 2',
            'P3': 'Process 3',
            'R1': 'Resource 1',
            'R2': 'Resource 2',
            'R3': 'Resource 3'
        }
        
        # Set initial colors
        for node in self.G.nodes():
            self.node_colors[node] = '#3498DB'  # Blue
            
        # Define animation steps
        self.total_steps = 8
        
        # Set initial description
        self.update_description("This scenario demonstrates the Hold and Wait condition, where processes hold resources while waiting for others, and how it can be prevented.")
        
        # Set initial conditions
        self.update_conditions({
            "Mutual Exclusion": True,
            "Hold and Wait": False,
            "No Preemption": True,
            "Circular Wait": False
        })
        
    def update_hold_and_wait_step(self, step):
        # Reset graph to initial state
        for u, v in list(self.G.edges()):
            self.G.remove_edge(u, v)
            
        for node in self.G.nodes():
            self.node_colors[node] = '#3498DB'  # Blue
            
        # Update based on step
        if step >= 1:
            # P1 allocates R1
            self.G.add_edge('R1', 'P1', type='allocation')
            self.edge_colors[('R1', 'P1')] = '#2ECC71'  # Green
            
            self.update_description("Step 1: Process 1 acquires Resource 1.")
            self.update_conditions({
                "Mutual Exclusion": True,
                "Hold and Wait": False,
                "No Preemption": True,
                "Circular Wait": False
            })
            
        if step >= 2:
            # P1 requests R2 while holding R1 (Hold and Wait)
            self.G.add_edge('P1', 'R2', type='request')
            self.edge_colors[('P1', 'R2')] = '#E74C3C'  # Red
            
            self.update_description("Step 2: Process 1 requests Resource 2 while still holding Resource 1. This is the Hold and Wait condition.")
            self.update_conditions({
                "Mutual Exclusion": True,
                "Hold and Wait": True,
                "No Preemption": True,
                "Circular Wait": False
            })
            
        if step >= 3:
            # P2 allocates R2
            self.G.add_edge('R2', 'P2', type='allocation')
            self.edge_colors[('R2', 'P2')] = '#2ECC71'  # Green
            
            self.update_description("Step 3: Process 2 acquires Resource 2, which Process 1 is waiting for.")
            
        if step >= 4:
            # P2 requests R3 while holding R2 (Hold and Wait)
            self.G.add_edge('P2', 'R3', type='request')
            self.edge_colors[('P2', 'R3')] = '#E74C3C'  # Red
            
            self.update_description("Step 4: Process 2 requests Resource 3 while holding Resource 2, extending the Hold and Wait condition.")
            
        if step >= 5:
            # P3 allocates R3
            self.G.add_edge('R3', 'P3', type='allocation')
            self.edge_colors[('R3', 'P3')] = '#2ECC71'  # Green
            
            self.update_description("Step 5: Process 3 acquires Resource 3, which Process 2 is waiting for.")
            
        if step >= 6:
            # P3 requests R1 while holding R3 (Hold and Wait + Circular Wait)
            self.G.add_edge('P3', 'R1', type='request')
            self.edge_colors[('P3', 'R1')] = '#E74C3C'  # Red
            
            self.update_description("Step 6: Process 3 requests Resource 1 while holding Resource 3. This creates a circular wait condition, resulting in deadlock.")
            self.update_conditions({
                "Mutual Exclusion": True,
                "Hold and Wait": True,
                "No Preemption": True,
                "Circular Wait": True
            })
            
        if step >= 7:
            # Deadlock detected
            self.node_colors['P1'] = '#E74C3C'  # Red
            self.node_colors['P2'] = '#E74C3C'  # Red
            self.node_colors['P3'] = '#E74C3C'  # Red
            self.node_colors['R1'] = '#F39C12'  # Orange
            self.node_colors['R2'] = '#F39C12'  # Orange
            self.node_colors['R3'] = '#F39C12'  # Orange
            
            self.update_description("Step 7: Deadlock detected! All processes are waiting for resources held by others in a circular chain.")
            
        if step >= 8:
            # Prevention strategy
            self.update_description("Step 8: To prevent Hold and Wait, we could require processes to request all needed resources at once before execution begins, or release all resources before requesting new ones. This breaks the Hold and Wait condition.")
            
        # Update graph
        self.update_graph()
        
    def scenario_circular_wait(self):
        # Initialize graph for circular wait scenario
        self.G.add_node('P1', type='process')
        self.G.add_node('P2', type='process')
        self.G.add_node('P3', type='process')
        self.G.add_node('P4', type='process')
        self.G.add_node('R1', type='resource')
        self.G.add_node('R2', type='resource')
        self.G.add_node('R3', type='resource')
        self.G.add_node('R4', type='resource')
        
        # Set positions in a circle
        self.pos = {
            'P1': (1, 2),
            'R1': (2, 1),
            'P2': (1, 0),
            'R2': (0, 1),
            'P3': (0.5, 1.5),
            'R3': (1.5, 1.5),
            'P4': (1.5, 0.5),
            'R4': (0.5, 0.5)
        }
        
        # Set labels
        self.labels = {
            'P1': 'P1',
            'P2': 'P2',
            'P3': 'P3',
            'P4': 'P4',
            'R1': 'R1',
            'R2': 'R2',
            'R3': 'R3',
            'R4': 'R4'
        }
        
        # Set initial colors
        for node in self.G.nodes():
            self.node_colors[node] = '#3498DB'  # Blue
            
        # Define animation steps
        self.total_steps = 7
        
        # Set initial description
        self.update_description("This scenario demonstrates the Circular Wait condition, where a cycle of processes each wait for resources held by the next process in the cycle.")
        
        # Set initial conditions
        self.update_conditions({
            "Mutual Exclusion": True,
            "Hold and Wait": False,
            "No Preemption": True,
            "Circular Wait": False
        })
        
    def update_circular_wait_step(self, step):
        # Reset graph to initial state
        for u, v in list(self.G.edges()):
            self.G.remove_edge(u, v)
            
        for node in self.G.nodes():
            self.node_colors[node] = '#3498DB'  # Blue
            
        # Update based on step
        if step >= 1:
            # Initial allocations
            self.G.add_edge('R1', 'P1', type='allocation')
            self.G.add_edge('R2', 'P2', type='allocation')
            self.edge_colors[('R1', 'P1')] = '#2ECC71'  # Green
            self.edge_colors[('R2', 'P2')] = '#2ECC71'  # Green
            
            self.update_description("Step 1: Process 1 holds Resource 1, and Process 2 holds Resource 2.")
            self.update_conditions({
                "Mutual Exclusion": True,
                "Hold and Wait": False,
                "No Preemption": True,
                "Circular Wait": False
            })
            
        if step >= 2:
            # More allocations
            self.G.add_edge('R3', 'P3', type='allocation')
            self.G.add_edge('R4', 'P4', type='allocation')
            self.edge_colors[('R3', 'P3')] = '#2ECC71'  # Green
            self.edge_colors[('R4', 'P4')] = '#2ECC71'  # Green
            
            self.update_description("Step 2: Process 3 holds Resource 3, and Process 4 holds Resource 4.")
            
        if step >= 3:
            # P1 requests R2 (start of circular chain)
            self.G.add_edge('P1', 'R2', type='request')
            self.edge_colors[('P1', 'R2')] = '#E74C3C'  # Red
            
            self.update_description("Step 3: Process 1 requests Resource 2 (held by Process 2) while holding Resource 1.")
            self.update_conditions({
                "Mutual Exclusion": True,
                "Hold and Wait": True,
                "No Preemption": True,
                "Circular Wait": False
            })
            
        if step >= 4:
            # P2 requests R3
            self.G.add_edge('P2', 'R3', type='request')
            self.edge_colors[('P2', 'R3')] = '#E74C3C'  # Red
            
            self.update_description("Step 4: Process 2 requests Resource 3 (held by Process 3) while holding Resource 2.")
            
        if step >= 5:
            # P3 requests R4
            self.G.add_edge('P3', 'R4', type='request')
            self.edge_colors[('P3', 'R4')] = '#E74C3C'  # Red
            
            self.update_description("Step 5: Process 3 requests Resource 4 (held by Process 4) while holding Resource 3.")
            
        if step >= 6:
            # P4 requests R1 (completing the circle)
            self.G.add_edge('P4', 'R1', type='request')
            self.edge_colors[('P4', 'R1')] = '#E74C3C'  # Red
            
            self.update_description("Step 6: Process 4 requests Resource 1 (held by Process 1) while holding Resource 4. This completes a circular wait condition, resulting in deadlock.")
            self.update_conditions({
                "Mutual Exclusion": True,
                "Hold and Wait": True,
                "No Preemption": True,
                "Circular Wait": True
            })
            
            # Highlight the deadlock
            self.node_colors['P1'] = '#E74C3C'  # Red
            self.node_colors['P2'] = '#E74C3C'  # Red
            self.node_colors['P3'] = '#E74C3C'  # Red
            self.node_colors['P4'] = '#E74C3C'  # Red
            self.node_colors['R1'] = '#F39C12'  # Orange
            self.node_colors['R2'] = '#F39C12'  # Orange
            self.node_colors['R3'] = '#F39C12'  # Orange
            self.node_colors['R4'] = '#F39C12'  # Orange
            
        if step >= 7:
            # Prevention strategy
            self.update_description("Step 7: To prevent Circular Wait, we can impose a total ordering on resource types and require that processes request resources in increasing order of enumeration. This breaks the circular wait condition and prevents deadlock.")
            
        # Update graph
        self.update_graph()
        
    def scenario_resource_hierarchy(self):
        # Initialize graph for resource hierarchy scenario
        self.G.add_node('P1', type='process')
        self.G.add_node('P2', type='process')
        self.G.add_node('R1', type='resource')
        self.G.add_node('R2', type='resource')
        self.G.add_node('R3', type='resource')
        
        # Set initial positions
        self.pos = {
            'P1': (0, 1),
            'P2': (2, 1),
            'R1': (0, 0),
            'R2': (1, 0),
            'R3': (2, 0)
        }
        
        # Set labels
        self.labels = {
            'P1': 'Process 1',
            'P2': 'Process 2',
            'R1': 'R1 (Low)',
            'R2': 'R2 (Medium)',
            'R3': 'R3 (High)'
        }
        
        # Set initial colors
        for node in self.G.nodes():
            self.node_colors[node] = '#3498DB'  # Blue
            
        # Define animation steps
        self.total_steps = 8
        
        # Set initial description
        self.update_description("This scenario demonstrates how resource hierarchy can prevent deadlock by ensuring resources are always requested in a specific order.")
        
        # Set initial conditions
        self.update_conditions({
            "Mutual Exclusion": True,
            "Hold and Wait": False,
            "No Preemption": True,
            "Circular Wait": False
        })
        
    def update_resource_hierarchy_step(self, step):
        # Reset graph to initial state
        for u, v in list(self.G.edges()):
            self.G.remove_edge(u, v)
            
        for node in self.G.nodes():
            self.node_colors[node] = '#3498DB'  # Blue
            
        # Update based on step
        if step >= 1:
            self.update_description("Step 1: Resources are assigned priorities: R1 (low), R2 (medium), R3 (high). Processes must request resources in increasing order of priority.")
            
        if step >= 2:
            # P1 allocates R1 (following hierarchy)
            self.G.add_edge('R1', 'P1', type='allocation')
            self.edge_colors[('R1', 'P1')] = '#2ECC71'  # Green
            
            self.update_description("Step 2: Process 1 acquires Resource 1 (lowest priority).")
            
        if step >= 3:
            # P1 allocates R2 (following hierarchy)
            self.G.add_edge('R2', 'P1', type='allocation')
            self.edge_colors[('R2', 'P1')] = '#2ECC71'  # Green
            
            self.update_description("Step 3: Process 1 acquires Resource 2 (medium priority) after already holding Resource 1 (lower priority). This follows the hierarchy.")
            self.update_conditions({
                "Mutual Exclusion": True,
                "Hold and Wait": True,
                "No Preemption": True,
                "Circular Wait": False
            })
            
        if step >= 4:
            # P2 allocates R1 (following hierarchy)
            self.G.add_edge('R1', 'P2', type='allocation')
            self.edge_colors[('R1', 'P2')] = '#2ECC71'  # Green
            
            self.update_description("Step 4: Process 2 acquires Resource 1 (lowest priority).")
            
        if step >= 5:
            # P2 requests R3 (skipping R2, but still following hierarchy)
            self.G.add_edge('P2', 'R3', type='request')
            self.edge_colors[('P2', 'R3')] = '#E74C3C'  # Red
            
            self.update_description("Step 5: Process 2 requests Resource 3 (highest priority) without needing Resource 2. This is still valid in the hierarchy approach.")
            
        if step >= 6:
            # P1 requests R3 (following hierarchy)
            self.G.add_edge('P1', 'R3', type='request')
            self.edge_colors[('P1', 'R3')] = '#E74C3C'  # Red
            
            self.update_description("Step 6: Process 1 requests Resource 3 (highest priority) after already holding Resources 1 and 2. This follows the hierarchy.")
            
        if step >= 7:
            # Show what would cause deadlock (but doesn't happen with hierarchy)
            self.update_description("Step 7: Note that even though both processes are waiting for Resource 3, there is no deadlock because the resource hierarchy prevents circular wait. If Process 2 had tried to request Resource 2 after holding Resource 3, it would violate the hierarchy and be denied.")
            
            # Highlight the non-deadlock state
            self.node_colors['P1'] = '#2ECC71'  # Green
            self.node_colors['P2'] = '#2ECC71'  # Green
            
        if step >= 8:
            # Prevention strategy
            self.update_description("Step 8: Resource hierarchy is an effective deadlock prevention strategy because it ensures that circular wait can never occur. By requiring processes to request resources in a specific order, we can guarantee that deadlock will not happen, though it may reduce concurrency.")
            
        # Update graph
        self.update_graph()