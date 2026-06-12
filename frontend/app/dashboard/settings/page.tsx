"use client"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { User, Bell, Shield, Key } from "lucide-react"

export default function SettingsPage() {
  const [name, setName] = useState("Sumayah Muhydeen")
  const [email, setEmail] = useState("sumayah@example.com")
  const [saved, setSaved] = useState(false)

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-2">Settings</h1>
      <p className="text-white/50 mb-8">Manage your account preferences</p>

      {/* Profile */}
      <Card className="bg-white/5 border-white/10 mb-6">
        <CardHeader><CardTitle className="text-white text-base flex items-center gap-2"><User className="w-4 h-4" /> Profile</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 bg-[#6D5DFC]/30 rounded-full flex items-center justify-center text-2xl font-bold text-[#6D5DFC]">
                {name.charAt(0)}
              </div>
              <Button size="sm" variant="outline" type="button" className="border-white/20 text-white/60 hover:text-white">Change photo</Button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label className="text-white/70">Full name</Label>
                <Input value={name} onChange={e => setName(e.target.value)} className="bg-white/5 border-white/20 text-white" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-white/70">Email</Label>
                <Input type="email" value={email} onChange={e => setEmail(e.target.value)} className="bg-white/5 border-white/20 text-white" />
              </div>
            </div>
            <Button type="submit" className="bg-[#6D5DFC] hover:bg-[#5648d4]">
              {saved ? "✓ Saved!" : "Save changes"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card className="bg-white/5 border-white/10 mb-6">
        <CardHeader><CardTitle className="text-white text-base flex items-center gap-2"><Bell className="w-4 h-4" /> Notifications</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {[
            { label: "Render completed", desc: "When your video finishes generating", on: true },
            { label: "Render failed", desc: "When a generation job fails", on: true },
            { label: "Weekly summary", desc: "Usage and project summary", on: false },
            { label: "Product updates", desc: "New features and announcements", on: true },
          ].map(item => (
            <div key={item.label} className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-white">{item.label}</div>
                <div className="text-xs text-white/40">{item.desc}</div>
              </div>
              <button className={`w-10 h-5 rounded-full transition-colors relative ${item.on ? "bg-[#6D5DFC]" : "bg-white/20"}`}>
                <div className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-all ${item.on ? "left-5.5" : "left-0.5"}`} style={{left: item.on ? "22px" : "2px"}} />
              </button>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Security */}
      <Card className="bg-white/5 border-white/10 mb-6">
        <CardHeader><CardTitle className="text-white text-base flex items-center gap-2"><Shield className="w-4 h-4" /> Security</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-white">Password</div>
              <div className="text-xs text-white/40">Last changed 30 days ago</div>
            </div>
            <Button size="sm" variant="outline" className="border-white/20 text-white/60 hover:text-white">Change</Button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-white">Two-factor authentication</div>
              <div className="text-xs text-white/40">Add an extra layer of security</div>
            </div>
            <Badge variant="secondary">Not enabled</Badge>
          </div>
        </CardContent>
      </Card>

      {/* API Key */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader><CardTitle className="text-white text-base flex items-center gap-2"><Key className="w-4 h-4" /> API access</CardTitle></CardHeader>
        <CardContent>
          <div className="bg-white/5 border border-white/10 rounded-lg px-4 py-3 font-mono text-sm text-white/40 mb-3">
            cg_live_••••••••••••••••••••••••••••••••
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" className="border-white/20 text-white/60 hover:text-white">Reveal</Button>
            <Button size="sm" variant="outline" className="border-white/20 text-white/60 hover:text-white">Regenerate</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
