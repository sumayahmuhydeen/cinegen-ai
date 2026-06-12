"use client"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Plus, Film, Search, ArrowRight, Clock, CheckCircle, Loader, AlertCircle } from "lucide-react"
import { useState } from "react"

const allProjects = [
  { id: "1", title: "The Last Frontier", status: "completed", scenes: 24, duration: "18 min", updated: "2h ago", style: "Documentary" },
  { id: "2", title: "Silicon Dreams", status: "generating", scenes: 31, duration: "28 min", updated: "Running now", style: "Sci-Fi" },
  { id: "3", title: "Urban Legends", status: "review", scenes: 18, duration: "14 min", updated: "Yesterday", style: "Drama" },
  { id: "4", title: "Beyond the Horizon", status: "draft", scenes: 0, duration: "—", updated: "3 days ago", style: "Adventure" },
  { id: "5", title: "The Algorithm", status: "completed", scenes: 20, duration: "16 min", updated: "Last week", style: "Thriller" },
]

const statusConfig = {
  completed: { label: "Completed", color: "success" },
  generating: { label: "Generating", color: "purple" },
  review: { label: "In Review", color: "warning" },
  draft: { label: "Draft", color: "secondary" },
} as const

export default function ProjectsPage() {
  const [search, setSearch] = useState("")
  const filtered = allProjects.filter(p => p.title.toLowerCase().includes(search.toLowerCase()))
  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Projects</h1>
          <p className="text-white/50 mt-1">{allProjects.length} total projects</p>
        </div>
        <Link href="/dashboard/projects/new">
          <Button className="bg-[#6D5DFC] hover:bg-[#5648d4] gap-2">
            <Plus className="w-4 h-4" /> New project
          </Button>
        </Link>
      </div>
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <Input placeholder="Search projects..." value={search} onChange={e => setSearch(e.target.value)}
          className="pl-9 bg-white/5 border-white/10 text-white placeholder:text-white/30" />
      </div>
      <div className="space-y-3">
        {filtered.map((project) => {
          const s = statusConfig[project.status as keyof typeof statusConfig]
          return (
            <Link key={project.id} href={`/dashboard/projects/${project.id}`}>
              <Card className="bg-white/5 border-white/10 hover:border-[#6D5DFC]/40 transition-all cursor-pointer">
                <CardContent className="p-5 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-[#6D5DFC]/20 rounded-lg flex items-center justify-center">
                      <Film className="w-5 h-5 text-[#6D5DFC]" />
                    </div>
                    <div>
                      <div className="font-medium text-white">{project.title}</div>
                      <div className="text-sm text-white/40 mt-0.5">{project.style} · {project.scenes} scenes · {project.duration} · {project.updated}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={s.color as any}>{s.label}</Badge>
                    <ArrowRight className="w-4 h-4 text-white/30" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
