import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Film, Zap, Shield, ArrowRight, Play, Star } from "lucide-react"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0D0D1A] text-white">
      {/* Nav */}
      <nav className="border-b border-white/10 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#6D5DFC] rounded-lg flex items-center justify-center">
              <Film className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-semibold">CineGen AI</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/auth/login">
              <Button variant="ghost" className="text-white/70 hover:text-white hover:bg-white/10">Sign in</Button>
            </Link>
            <Link href="/auth/signup">
              <Button className="bg-[#6D5DFC] hover:bg-[#5648d4]">Get started free</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 py-24 text-center">
        <Badge variant="purple" className="mb-6 text-sm px-4 py-1">
          🎬 AI Film Studio — Now in Beta
        </Badge>
        <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
          Turn your script into a<br />
          <span className="text-[#6D5DFC]">complete AI film</span>
        </h1>
        <p className="text-xl text-white/60 mb-10 max-w-2xl mx-auto">
          CineGen AI orchestrates the entire production pipeline — characters, environments, voice, music, and continuity — to produce long-form videos up to 40 minutes.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link href="/auth/signup">
            <Button size="lg" className="bg-[#6D5DFC] hover:bg-[#5648d4] text-lg px-8 py-4 h-auto">
              Start creating <ArrowRight className="w-5 h-5" />
            </Button>
          </Link>
          <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10 text-lg px-8 py-4 h-auto">
            <Play className="w-5 h-5" /> Watch demo
          </Button>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-6 pb-24">
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { icon: Film, title: "Script to film", desc: "Upload any script and our AI breaks it into scenes, shots, characters, and locations automatically." },
            { icon: Shield, title: "Character consistency", desc: "Our continuity engine keeps every character looking identical across hundreds of shots." },
            { icon: Zap, title: "Full audio pipeline", desc: "Voice, music, and sound effects generated and synced automatically to every scene." },
          ].map((f) => (
            <div key={f.title} className="bg-white/5 border border-white/10 rounded-xl p-6">
              <div className="w-10 h-10 bg-[#6D5DFC]/20 rounded-lg flex items-center justify-center mb-4">
                <f.icon className="w-5 h-5 text-[#6D5DFC]" />
              </div>
              <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
              <p className="text-white/60 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-7xl mx-auto px-6 pb-24">
        <h2 className="text-3xl font-bold text-center mb-12">Simple pricing</h2>
        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {[
            { name: "Starter", price: "$29", desc: "5 projects/month", features: ["Up to 5 min videos", "Basic characters", "720p export", "Email support"] },
            { name: "Pro", price: "$79", desc: "25 projects/month", features: ["Up to 20 min videos", "Advanced continuity", "1080p export", "Priority support"], popular: true },
            { name: "Studio", price: "$199", desc: "Unlimited projects", features: ["Up to 40 min videos", "Full AI director", "4K export", "Dedicated support"] },
          ].map((plan) => (
            <div key={plan.name} className={`rounded-xl p-6 border ${plan.popular ? "border-[#6D5DFC] bg-[#6D5DFC]/10" : "border-white/10 bg-white/5"}`}>
              {plan.popular && <Badge variant="purple" className="mb-3">Most popular</Badge>}
              <div className="text-2xl font-bold mb-1">{plan.name}</div>
              <div className="text-4xl font-bold mb-1">{plan.price}<span className="text-lg font-normal text-white/60">/mo</span></div>
              <div className="text-white/60 text-sm mb-6">{plan.desc}</div>
              <ul className="space-y-2 mb-6">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-white/80">
                    <Star className="w-3 h-3 text-[#22C55E]" /> {f}
                  </li>
                ))}
              </ul>
              <Link href="/auth/signup">
                <Button className={`w-full ${plan.popular ? "bg-[#6D5DFC] hover:bg-[#5648d4]" : "bg-white/10 hover:bg-white/20"}`}>
                  Get started
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-white/10 px-6 py-8 text-center text-white/40 text-sm">
        © 2025 CineGen AI. All rights reserved.
      </footer>
    </div>
  )
}
