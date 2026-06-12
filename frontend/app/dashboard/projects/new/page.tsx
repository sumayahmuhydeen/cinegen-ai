"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { ArrowLeft, Upload, FileText, Film, Zap } from "lucide-react"
import Link from "next/link"

const styles = [
  { id: "documentary", label: "Documentary", desc: "Real-world storytelling" },
  { id: "drama", label: "Drama", desc: "Character-driven narrative" },
  { id: "scifi", label: "Sci-Fi", desc: "Futuristic worlds" },
  { id: "corporate", label: "Corporate", desc: "Business & explainers" },
  { id: "educational", label: "Educational", desc: "Learning content" },
  { id: "horror", label: "Horror / Thriller", desc: "Suspense & tension" },
]

export default function NewProjectPage() {
  const router = useRouter()
  const [title, setTitle] = useState("")
  const [script, setScript] = useState("")
  const [selectedStyle, setSelectedStyle] = useState("")
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)

  async function handleCreate() {
    setLoading(true)
    await new Promise(r => setTimeout(r, 1500))
    router.push("/dashboard/projects/2")
  }

  return (
    <div className="p-8 max-w-3xl">
      <Link href="/dashboard/projects" className="flex items-center gap-2 text-white/50 hover:text-white text-sm mb-8 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to projects
      </Link>

      <h1 className="text-2xl font-bold text-white mb-2">New project</h1>
      <p className="text-white/50 mb-8">Set up your AI film project in 3 steps</p>

      {/* Steps */}
      <div className="flex items-center gap-2 mb-8">
        {[1,2,3].map(s => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium transition-colors
              ${step >= s ? "bg-[#6D5DFC] text-white" : "bg-white/10 text-white/40"}`}>
              {s}
            </div>
            {s < 3 && <div className={`h-px w-12 transition-colors ${step > s ? "bg-[#6D5DFC]" : "bg-white/10"}`} />}
          </div>
        ))}
        <span className="text-sm text-white/40 ml-2">
          {step === 1 ? "Project details" : step === 2 ? "Your script" : "Visual style"}
        </span>
      </div>

      {step === 1 && (
        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-6 space-y-5">
            <div className="space-y-1.5">
              <Label className="text-white/70">Project title</Label>
              <Input placeholder="e.g. The Last Frontier" value={title} onChange={e => setTitle(e.target.value)}
                className="bg-white/5 border-white/20 text-white placeholder:text-white/30" />
            </div>
            <Button className="bg-[#6D5DFC] hover:bg-[#5648d4]" disabled={!title.trim()} onClick={() => setStep(2)}>
              Continue
            </Button>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-6 space-y-5">
            <div className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center hover:border-[#6D5DFC]/50 transition-colors cursor-pointer">
              <Upload className="w-8 h-8 text-white/30 mx-auto mb-3" />
              <p className="text-white/60 text-sm">Drop your script here, or <span className="text-[#6D5DFC]">browse</span></p>
              <p className="text-white/30 text-xs mt-1">PDF, DOCX, or TXT</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-white/10" />
              <span className="text-white/30 text-xs">or paste directly</span>
              <div className="flex-1 h-px bg-white/10" />
            </div>
            <textarea value={script} onChange={e => setScript(e.target.value)}
              placeholder="Paste your full script here..."
              className="w-full h-40 bg-white/5 border border-white/20 rounded-lg p-3 text-sm text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-[#6D5DFC] resize-none" />
            <div className="flex gap-3">
              <Button variant="ghost" className="text-white/50 hover:text-white" onClick={() => setStep(1)}>Back</Button>
              <Button className="bg-[#6D5DFC] hover:bg-[#5648d4]" disabled={!script.trim()} onClick={() => setStep(3)}>Continue</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 3 && (
        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-6">
            <p className="text-white/70 text-sm mb-4">Choose a visual style for your film</p>
            <div className="grid grid-cols-2 gap-3 mb-6">
              {styles.map(s => (
                <button key={s.id} onClick={() => setSelectedStyle(s.id)}
                  className={`p-4 rounded-lg border text-left transition-all ${selectedStyle === s.id ? "border-[#6D5DFC] bg-[#6D5DFC]/10" : "border-white/10 bg-white/5 hover:border-white/30"}`}>
                  <div className="font-medium text-white text-sm">{s.label}</div>
                  <div className="text-white/40 text-xs mt-0.5">{s.desc}</div>
                </button>
              ))}
            </div>
            <div className="flex gap-3">
              <Button variant="ghost" className="text-white/50 hover:text-white" onClick={() => setStep(2)}>Back</Button>
              <Button className="bg-[#6D5DFC] hover:bg-[#5648d4] gap-2" disabled={!selectedStyle || loading} onClick={handleCreate}>
                <Zap className="w-4 h-4" /> {loading ? "Creating project..." : "Create & analyse script"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
