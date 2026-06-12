"use client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Users, Film, Server, HardDrive, Zap, TrendingUp, AlertCircle, CheckCircle } from "lucide-react"

const users = [
  { id: "u1", name: "Alex Johnson", email: "alex@example.com", plan: "Pro", projects: 12, status: "active" },
  { id: "u2", name: "Maria Garcia", email: "maria@example.com", plan: "Studio", projects: 34, status: "active" },
  { id: "u3", name: "James Lee", email: "james@example.com", plan: "Starter", projects: 3, status: "active" },
  { id: "u4", name: "Sara Okonkwo", email: "sara@example.com", plan: "Pro", projects: 8, status: "suspended" },
]

const jobs = [
  { id: "job-001", project: "The Last Frontier", user: "Alex Johnson", status: "completed", duration: "22 min", started: "2h ago" },
  { id: "job-002", project: "Silicon Dreams", user: "Maria Garcia", status: "running", duration: "—", started: "Running" },
  { id: "job-003", project: "Urban Legends", user: "James Lee", status: "failed", duration: "—", started: "5h ago" },
  { id: "job-004", project: "The Algorithm", user: "Sara Okonkwo", status: "queued", duration: "—", started: "Queued" },
]

export default function AdminPage() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Admin Panel</h1>
        <p className="text-white/50 mt-1">Platform overview and management</p>
      </div>

      {/* Platform stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          { label: "Total users", value: "1,284", icon: Users, color: "text-[#6D5DFC]", bg: "bg-[#6D5DFC]/10" },
          { label: "Active projects", value: "347", icon: Film, color: "text-[#22C55E]", bg: "bg-[#22C55E]/10" },
          { label: "Render jobs today", value: "89", icon: Zap, color: "text-amber-400", bg: "bg-amber-400/10" },
          { label: "Revenue (MRR)", value: "$18,432", icon: TrendingUp, color: "text-blue-400", bg: "bg-blue-400/10" },
        ].map(stat => (
          <Card key={stat.label} className="bg-white/5 border-white/10">
            <CardContent className="p-5">
              <div className={`w-9 h-9 ${stat.bg} rounded-lg flex items-center justify-center mb-3`}>
                <stat.icon className={`w-4 h-4 ${stat.color}`} />
              </div>
              <div className="text-2xl font-bold text-white mb-0.5">{stat.value}</div>
              <div className="text-sm text-white/50">{stat.label}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* System health */}
      <Card className="bg-white/5 border-white/10 mb-8">
        <CardHeader><CardTitle className="text-white text-base flex items-center gap-2"><Server className="w-4 h-4" /> System health</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-3 gap-6">
          {[
            { label: "API Gateway", uptime: "99.98%", status: "healthy" },
            { label: "GPU Cluster", uptime: "98.2%", status: "healthy" },
            { label: "Storage (R2)", uptime: "100%", status: "healthy" },
          ].map(s => (
            <div key={s.label}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-white/60">{s.label}</span>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-[#22C55E]" />
                  <span className="text-xs text-[#22C55E]">{s.status}</span>
                </div>
              </div>
              <div className="text-lg font-semibold text-white mb-1">{s.uptime}</div>
              <Progress value={parseFloat(s.uptime)} className="h-1.5" />
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-6">
        {/* Users table */}
        <Card className="bg-white/5 border-white/10">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-white text-base flex items-center gap-2"><Users className="w-4 h-4" /> Recent users</CardTitle>
            <Button size="sm" variant="ghost" className="text-[#6D5DFC] text-xs">View all</Button>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  {["User", "Plan", "Projects", "Status"].map(h => (
                    <th key={h} className="text-left px-5 py-2.5 text-white/40 font-medium text-xs">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} className="border-b border-white/5 hover:bg-white/3">
                    <td className="px-5 py-3">
                      <div className="text-white text-sm font-medium">{u.name}</div>
                      <div className="text-white/40 text-xs">{u.email}</div>
                    </td>
                    <td className="px-5 py-3"><Badge variant="purple" className="text-xs">{u.plan}</Badge></td>
                    <td className="px-5 py-3 text-white/60">{u.projects}</td>
                    <td className="px-5 py-3">
                      <Badge variant={u.status === "active" ? "success" : "destructive"} className="text-xs capitalize">{u.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        {/* Render jobs */}
        <Card className="bg-white/5 border-white/10">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-white text-base flex items-center gap-2"><Zap className="w-4 h-4" /> Render jobs</CardTitle>
            <Button size="sm" variant="ghost" className="text-[#6D5DFC] text-xs">View all</Button>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  {["Project", "User", "Status", "Started"].map(h => (
                    <th key={h} className="text-left px-5 py-2.5 text-white/40 font-medium text-xs">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {jobs.map(job => (
                  <tr key={job.id} className="border-b border-white/5 hover:bg-white/3">
                    <td className="px-5 py-3 text-white text-sm">{job.project}</td>
                    <td className="px-5 py-3 text-white/60 text-xs">{job.user}</td>
                    <td className="px-5 py-3">
                      <Badge
                        variant={job.status === "completed" ? "success" : job.status === "running" ? "purple" : job.status === "failed" ? "destructive" : "secondary"}
                        className="text-xs capitalize">{job.status}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 text-white/40 text-xs">{job.started}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
