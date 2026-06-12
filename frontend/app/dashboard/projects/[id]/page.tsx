"use client"
import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { ArrowLeft, Film, Users, MapPin, Music, Video, CheckCircle, Settings, Download, RefreshCw, Play } from "lucide-react"
import Link from "next/link"

const tabs = [
  { id: "blueprint", label: "Blueprint", icon: Film },
  { id: "characters", label: "Characters", icon: Users },
  { id: "storyboard", label: "Storyboard", icon: Film },
  { id: "locations", label: "Locations", icon: MapPin },
  { id: "audio", label: "Audio", icon: Music },
  { id: "generation", label: "Generation", icon: Video },
  { id: "export", label: "Export", icon: Download },
]

const mockShots = [
  { id: "s1", scene: 1, shot: 1, camera: "Wide Shot", action: "Establishing shot of city skyline at dawn", status: "completed", emotion: "Inspiring" },
  { id: "s2", scene: 1, shot: 2, camera: "Medium Shot", action: "Character walks toward camera", status: "completed", emotion: "Determined" },
  { id: "s3", scene: 2, shot: 1, camera: "Close-Up", action: "Reaction shot — character reads letter", status: "generating", emotion: "Shocked" },
  { id: "s4", scene: 2, shot: 2, camera: "Over-Shoulder", action: "Two characters in heated discussion", status: "pending", emotion: "Tense" },
  { id: "s5", scene: 3, shot: 1, camera: "POV", action: "Walking through crowded market", status: "pending", emotion: "Curious" },
]

const mockCharacters = [
  { id: "c1", name: "Marcus Cole", role: "Protagonist", age: "35–42", approved: true },
  { id: "c2", name: "Dr. Elena Voss", role: "Antagonist", age: "40–48", approved: true },
  { id: "c3", name: "Juno", role: "Ally", age: "25–30", approved: false },
]

export default function ProjectWorkspacePage() {
  const [activeTab, setActiveTab] = useState("blueprint")

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-white/10 px-8 py-5">
        <div className="flex items-center gap-4 mb-4">
          <Link href="/dashboard/projects" className="text-white/40 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-white">Silicon Dreams</h1>
              <Badge variant="purple">Generating</Badge>
            </div>
            <p className="text-white/40 text-sm mt-0.5">Sci-Fi · 31 scenes · Est. 28 min</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs text-white/40 mb-1">Overall progress</div>
              <div className="flex items-center gap-2">
                <Progress value={67} className="w-32 h-1.5" />
                <span className="text-xs text-white/60">67%</span>
              </div>
            </div>
            <Button size="sm" className="bg-[#6D5DFC] hover:bg-[#5648d4] gap-1.5">
              <Play className="w-3.5 h-3.5" /> Preview
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1">
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm transition-colors ${activeTab === tab.id ? "bg-[#6D5DFC]/20 text-[#6D5DFC] font-medium" : "text-white/40 hover:text-white hover:bg-white/5"}`}>
              <tab.icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-auto p-8">

        {activeTab === "blueprint" && (
          <div className="space-y-6 max-w-4xl">
            <div className="grid grid-cols-3 gap-4">
              {[["31", "Total scenes"], ["147", "Total shots"], ["28 min", "Est. duration"]].map(([v, l]) => (
                <Card key={l} className="bg-white/5 border-white/10">
                  <CardContent className="p-5 text-center">
                    <div className="text-3xl font-bold text-white mb-1">{v}</div>
                    <div className="text-sm text-white/50">{l}</div>
                  </CardContent>
                </Card>
              ))}
            </div>
            <Card className="bg-white/5 border-white/10">
              <CardHeader><CardTitle className="text-white text-base">Shot breakdown</CardTitle></CardHeader>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10">
                      {["Scene", "Shot", "Camera", "Action", "Emotion", "Status"].map(h => (
                        <th key={h} className="text-left px-5 py-3 text-white/40 font-medium text-xs">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {mockShots.map(shot => (
                      <tr key={shot.id} className="border-b border-white/5 hover:bg-white/3">
                        <td className="px-5 py-3 text-white/60">{shot.scene}</td>
                        <td className="px-5 py-3 text-white/60">{shot.shot}</td>
                        <td className="px-5 py-3 text-white/80 font-medium">{shot.camera}</td>
                        <td className="px-5 py-3 text-white/60 max-w-xs truncate">{shot.action}</td>
                        <td className="px-5 py-3"><Badge variant="secondary" className="text-xs">{shot.emotion}</Badge></td>
                        <td className="px-5 py-3">
                          <Badge variant={shot.status === "completed" ? "success" : shot.status === "generating" ? "purple" : "secondary"} className="text-xs capitalize">{shot.status}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "characters" && (
          <div className="max-w-3xl space-y-4">
            <p className="text-white/50 text-sm">Review and approve character reference images before generation begins.</p>
            {mockCharacters.map(char => (
              <Card key={char.id} className="bg-white/5 border-white/10">
                <CardContent className="p-5 flex items-center gap-5">
                  <div className="w-16 h-20 bg-[#6D5DFC]/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Users className="w-6 h-6 text-[#6D5DFC]" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">{char.name}</span>
                      <Badge variant="secondary" className="text-xs">{char.role}</Badge>
                    </div>
                    <div className="text-sm text-white/40">Age range: {char.age}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {char.approved ? (
                      <Badge variant="success" className="gap-1"><CheckCircle className="w-3 h-3" /> Approved</Badge>
                    ) : (
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" className="border-white/20 text-white/70 hover:text-white gap-1">
                          <RefreshCw className="w-3 h-3" /> Regenerate
                        </Button>
                        <Button size="sm" className="bg-[#22C55E] hover:bg-green-600 gap-1">
                          <CheckCircle className="w-3 h-3" /> Approve
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {activeTab === "storyboard" && (
          <div className="max-w-5xl">
            <p className="text-white/50 text-sm mb-6">AI-generated storyboard panels. Approve or regenerate each scene before video generation.</p>
            <div className="grid grid-cols-3 gap-4">
              {mockShots.map(shot => (
                <Card key={shot.id} className="bg-white/5 border-white/10 overflow-hidden">
                  <div className="aspect-video bg-[#6D5DFC]/10 flex items-center justify-center">
                    <Film className="w-8 h-8 text-[#6D5DFC]/40" />
                  </div>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-white/40">Scene {shot.scene} · Shot {shot.shot}</span>
                      <Badge variant="secondary" className="text-xs">{shot.camera}</Badge>
                    </div>
                    <p className="text-xs text-white/60 mb-3 leading-relaxed">{shot.action}</p>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" className="flex-1 border-white/20 text-white/60 text-xs h-7">Regenerate</Button>
                      <Button size="sm" className="flex-1 bg-[#6D5DFC] hover:bg-[#5648d4] text-xs h-7">Approve</Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {activeTab === "generation" && (
          <div className="max-w-3xl space-y-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-white/50 text-sm">Shot generation queue</p>
              <Button size="sm" className="bg-[#6D5DFC] hover:bg-[#5648d4]">Generate all</Button>
            </div>
            {mockShots.map(shot => (
              <Card key={shot.id} className="bg-white/5 border-white/10">
                <CardContent className="p-4 flex items-center gap-4">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${shot.status === "completed" ? "bg-[#22C55E]" : shot.status === "generating" ? "bg-[#6D5DFC] animate-pulse" : "bg-white/20"}`} />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-white">Scene {shot.scene}, Shot {shot.shot} — {shot.camera}</div>
                    <div className="text-xs text-white/40 mt-0.5">{shot.action}</div>
                    {shot.status === "generating" && <Progress value={45} className="h-1 mt-2" />}
                  </div>
                  <Badge variant={shot.status === "completed" ? "success" : shot.status === "generating" ? "purple" : "secondary"} className="text-xs capitalize">
                    {shot.status}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {activeTab === "audio" && (
          <div className="max-w-2xl space-y-6">
            {[
              { title: "Narration", desc: "Main voiceover track", status: "Completed" },
              { title: "Character dialogue", desc: "3 character voices assigned", status: "Completed" },
              { title: "Background music", desc: "Scene-matched music beds", status: "Generating..." },
              { title: "Sound effects", desc: "Ambient and action SFX", status: "Pending" },
            ].map(item => (
              <Card key={item.title} className="bg-white/5 border-white/10">
                <CardContent className="p-5 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-[#6D5DFC]/20 rounded-lg flex items-center justify-center">
                      <Music className="w-5 h-5 text-[#6D5DFC]" />
                    </div>
                    <div>
                      <div className="font-medium text-white">{item.title}</div>
                      <div className="text-sm text-white/40">{item.desc}</div>
                    </div>
                  </div>
                  <Badge variant={item.status === "Completed" ? "success" : item.status.includes("Gen") ? "purple" : "secondary"}>{item.status}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {activeTab === "export" && (
          <div className="max-w-xl space-y-6">
            <Card className="bg-white/5 border-white/10">
              <CardHeader><CardTitle className="text-white text-base">Export settings</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm text-white/60 mb-2 block">Resolution</label>
                  <div className="flex gap-2">
                    {["720p", "1080p"].map(r => (
                      <button key={r} className={`px-4 py-2 rounded-lg border text-sm transition-colors ${r === "1080p" ? "border-[#6D5DFC] bg-[#6D5DFC]/10 text-[#6D5DFC]" : "border-white/20 text-white/60 hover:border-white/40"}`}>{r}</button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-sm text-white/60 mb-2 block">Format</label>
                  <div className="flex gap-2">
                    {["MP4", "MOV"].map(f => (
                      <button key={f} className={`px-4 py-2 rounded-lg border text-sm transition-colors ${f === "MP4" ? "border-[#6D5DFC] bg-[#6D5DFC]/10 text-[#6D5DFC]" : "border-white/20 text-white/60 hover:border-white/40"}`}>{f}</button>
                    ))}
                  </div>
                </div>
                <Button className="w-full bg-[#6D5DFC] hover:bg-[#5648d4] gap-2">
                  <Download className="w-4 h-4" /> Export film
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "locations" && (
          <div className="max-w-3xl">
            <p className="text-white/50 text-sm mb-6">Generated location reference images. Approve each before generation.</p>
            <div className="grid grid-cols-2 gap-4">
              {[["City Skyline", "Exterior — Dawn"], ["Research Lab", "Interior — Night"], ["Abandoned Warehouse", "Interior — Day"], ["Underground Station", "Interior — Evening"]].map(([name, desc]) => (
                <Card key={name} className="bg-white/5 border-white/10 overflow-hidden">
                  <div className="aspect-video bg-[#6D5DFC]/10 flex items-center justify-center">
                    <MapPin className="w-8 h-8 text-[#6D5DFC]/40" />
                  </div>
                  <CardContent className="p-4">
                    <div className="font-medium text-white mb-1">{name}</div>
                    <div className="text-xs text-white/40 mb-3">{desc}</div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" className="flex-1 border-white/20 text-white/60 text-xs h-7">Regenerate</Button>
                      <Button size="sm" className="flex-1 bg-[#6D5DFC] hover:bg-[#5648d4] text-xs h-7">Approve</Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
