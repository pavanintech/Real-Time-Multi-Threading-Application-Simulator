"use client"

import { useState, useEffect, useRef } from "react"
import { Play, Pause, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { ThreadVisualizer } from "@/components/thread-visualizer"
import { ResourceMonitor } from "@/components/resource-monitor"
import { ThreadCreator } from "@/components/thread-creator"
import { DeadlockDemo } from "@/components/deadlock-demo"
import { ThreadManager } from "@/lib/thread-manager"

export function ThreadSimulator() {
  // Use simple primitive states instead of complex objects
  const [isRunning, setIsRunning] = useState(false)
  const [schedulingAlgorithm, setSchedulingAlgorithm] = useState("round-robin")
  const [timeQuantum, setTimeQuantum] = useState(100)
  const [threads, setThreads] = useState<any[]>([])
  const [runningThreadId, setRunningThreadId] = useState<string | null>(null)
  const [cpuUtilization, setCpuUtilization] = useState<number[]>([])
  const [currentTab, setCurrentTab] = useState("threads")

  // Use a ref for the thread manager to avoid re-renders
  const threadManagerRef = useRef<ThreadManager>(new ThreadManager(schedulingAlgorithm, timeQuantum))

  // Reset the simulation when scheduling algorithm or time quantum changes
  useEffect(() => {
    if (isRunning) return // Don't reset while running

    threadManagerRef.current = new ThreadManager(schedulingAlgorithm, timeQuantum)
    setThreads([])
    setCpuUtilization([])
    setRunningThreadId(null)
  }, [schedulingAlgorithm, timeQuantum, isRunning])

  // Run the simulation
  useEffect(() => {
    let interval: NodeJS.Timeout

    if (isRunning) {
      interval = setInterval(() => {
        const manager = threadManagerRef.current
        manager.tick()

        // Update state with simple values
        setThreads([...manager.getThreads()])
        setRunningThreadId(manager.getRunningThread()?.id || null)
        setCpuUtilization((prev) => [...prev, manager.getCpuUtilization()])
      }, 100)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isRunning])

  const handleAddThread = (thread: any) => {
    threadManagerRef.current.addThread(thread)
    setThreads([...threadManagerRef.current.getThreads()])
  }

  const handleClearThreads = () => {
    threadManagerRef.current.clearThreads()
    setThreads([])
    setCpuUtilization([])
    setRunningThreadId(null)
  }

  const handleToggleSimulation = () => {
    setIsRunning(!isRunning)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Simulation Controls</CardTitle>
          <CardDescription>Configure and control the thread simulation</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label htmlFor="scheduling-algorithm">Scheduling Algorithm</Label>
              <Select value={schedulingAlgorithm} onValueChange={setSchedulingAlgorithm} disabled={isRunning}>
                <SelectTrigger id="scheduling-algorithm">
                  <SelectValue placeholder="Select algorithm" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fifo">First-In-First-Out</SelectItem>
                  <SelectItem value="round-robin">Round Robin</SelectItem>
                  <SelectItem value="priority">Priority-based</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="time-quantum">
                Time Quantum (ms) {schedulingAlgorithm === "round-robin" ? "" : "(Round Robin only)"}
              </Label>
              <div className="flex items-center gap-4">
                <Slider
                  id="time-quantum"
                  min={10}
                  max={500}
                  step={10}
                  value={[timeQuantum]}
                  onValueChange={(value) => setTimeQuantum(value[0])}
                  disabled={isRunning || schedulingAlgorithm !== "round-robin"}
                  className="flex-1"
                />
                <span className="w-12 text-right">{timeQuantum}ms</span>
              </div>
            </div>

            <div className="flex items-end gap-2">
              <Button
                onClick={handleToggleSimulation}
                className="flex-1"
                variant={isRunning ? "destructive" : "default"}
              >
                {isRunning ? <Pause className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />}
                {isRunning ? "Pause" : "Start"} Simulation
              </Button>
              <Button onClick={handleClearThreads} variant="outline" disabled={isRunning}>
                <Trash2 className="h-4 w-4" />
                <span className="sr-only">Clear Threads</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={currentTab} onValueChange={setCurrentTab}>
        <TabsList className="grid grid-cols-3">
          <TabsTrigger value="threads">Thread Management</TabsTrigger>
          <TabsTrigger value="visualization">Visualization</TabsTrigger>
          <TabsTrigger value="deadlock">Deadlock Simulation</TabsTrigger>
        </TabsList>

        <TabsContent value="threads" className="space-y-6">
          <ThreadCreator onAddThread={handleAddThread} disabled={isRunning} />
          <ThreadVisualizer threads={threads} runningThreadId={runningThreadId} />
        </TabsContent>

        <TabsContent value="visualization" className="space-y-6">
          <ResourceMonitor cpuUtilization={cpuUtilization} threads={threads} />
        </TabsContent>

        <TabsContent value="deadlock" className="space-y-6">
          <DeadlockDemo />
        </TabsContent>
      </Tabs>
    </div>
  )
}

