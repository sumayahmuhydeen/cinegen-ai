"use client"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Plus, Film, Clock, CheckCircle, Loader, AlertCircle, ArrowRight, Zap } from "lucide-react"

const mockProjects = [
  { id: "1", title: "The Last Frontier", status: "completed", scenes: 24, duration: "18 min", updated: "2h ago" },
  { id: "2", title: "Silicon Dreams", status: "generating", scenes: 31, duration: "28 min", updated: "Running now", progress: 67 },
  { id: "3", title: "Urban Legends", status: "review", scenes: 18, duration: "14 min", updated: "Yesterday" },
  { id: "4", title: "Beyond the Horizon", status: "draft", scenes: 0, duration: "—", updated: "3 days ago" },
]

const statusConfig = {
  completed: { label: "Completed", color: "success", icon: CheckCircle },
  generating: { label: "Generating", color: "purple", icon: Loader },
  review: { label: "In Review", color: "warning", icon: AlertCircle },
  draft: { label: "Draft", color: "secondary", icon: Film },
} as const

const stats = [
  { label: "Total projects", value: "4", sub: "2 active", icon: Film, color: "text-[#6D5DFC]", bg: "bg-[#6D5DFC]/10" },
  { label: "Videos generated", value: "12", sub: "↑ 3 this week", icon: CheckCircle, color: "text-[#22C55E]", bg: "bg-[#22C55E]/10" },
  { label: "Total runtime", value: "3.2 hrs", sub: "AI-generated", icon: Clock, color: "text-amber-400", bg: "bg-amber-400/10" },
  { label: "AI credits used", value: "840", sub: "of 2,000", icon: Zap, color: "text-blue-400", bg: "bg-blue-400/10" },
]

export default function DashboardPage() {
  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-white/50 mt-1">Welcome back. Here's what's happening.</p>
        </div>
        <Link href="/dashboard/projects/new">
          <Button className="bg-[#6D5DFC] hover:bg-[#5648d4] gap-2">
            <Plus className="w-4 h-4" /> New project
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((stat) => (
          <Card key={stat.label} className="bg-white/5 border-white/10">
            <CardContent className="p-5">
              <div className="flex items-start justify-between mb-3">
                <div className={`w-9 h-9 ${stat.bg} rounded-lg flex items-center justify-center`}>
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </div>
              <div className="text-2xl font-bold text-white mb-0.5">{stat.value}</div>
              <div className="text-sm font-medium text-white/70">{stat.label}</div>
              <div className="text-xs text-white/40 mt-0.5">{stat.sub}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Credits usage */}
      <Card className="bg-white/5 border-white/10 mb-8">
        <CardContent className="p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-white">AI Credits — Pro Plan</span>
            <span className="text-sm text-white/50">840 / 2,000 used</span>
          </div>
          <Progress value={42} className="h-2" />
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-white/40">1,160 credits remaining</span>
            <Link href="/dashboard/billing" className="text-xs text-[#6D5DFC] hover:underline">Upgrade plan</Link>
          </div>
        </CardContent>
      </Card>

      {/* Projects */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Recent projects</h2>
        <Link href="/dashboard/projects" className="text-sm text-[#6D5DFC] hover:underline flex items-center gap-1">
          View all <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      <div className="space-y-3">
        {mockProjects.map((project) => {
          const s = statusConfig[project.status as keyof typeof statusConfig]
          return (
            <Link key={project.id} href={`/dashboard/projects/${project.id}`}>
              <Card className="bg-white/5 border-white/10 hover:border-[#6D5DFC]/40 hover:bg-white/8 transition-all cursor-pointer">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-[#6D5DFC]/20 rounded-lg flex items-center justify-center">
                        <Film className="w-5 h-5 text-[#6D5DFC]" />
                      </div>
                      <div>
                        <div className="font-medium text-white">{project.title}</div>
                        <div className="text-sm text-white/40 mt-0.5">{project.scenes} scenes · {project.duration} · {project.updated}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={s.color as any}>{s.label}</Badge>
                      <ArrowRight className="w-4 h-4 text-white/30" />
                    </div>
                  </div>
                  {project.status === "generating" && (
                    <div className="mt-4">
                      <div className="flex justify-between text-xs text-white/40 mb-1.5">
                        <span>Generating shots...</span>
                        <span>{project.progress}%</span>
                      </div>
                      <Progress value={project.progress} className="h-1.5" />
                    </div>
                  )}
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
