"use client"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Film, Zap, Shield, ArrowRight, Play } from "lucide-react"

export default function LandingPage() {
  return (
    <div style={{ minHeight: "100vh", background: "#0D0D1A", color: "white", fontFamily: "system-ui, sans-serif" }}>

      {/* Nav */}
      <nav style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", padding: "16px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ width: 36, height: 36, background: "#6D5DFC", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Film size={18} color="white" />
          </div>
          <span style={{ fontSize: 18, fontWeight: 600 }}>CineGen AI</span>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <Link href="/auth/login" style={{ color: "rgba(255,255,255,0.6)", textDecoration: "none", padding: "8px 16px", borderRadius: 8 }}>
            Sign in
          </Link>
          <Link href="/auth/signup" style={{ background: "#6D5DFC", color: "white", textDecoration: "none", padding: "8px 20px", borderRadius: 8, fontWeight: 500 }}>
            Get started free
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ maxWidth: 900, margin: "0 auto", padding: "100px 32px", textAlign: "center" }}>
        <div style={{ display: "inline-block", background: "rgba(109,93,252,0.15)", border: "1px solid rgba(109,93,252,0.4)", borderRadius: 20, padding: "6px 18px", fontSize: 13, color: "#a89cfd", marginBottom: 32 }}>
          🎬 AI Film Studio — Now in Beta
        </div>
        <h1 style={{ fontSize: "clamp(36px, 6vw, 68px)", fontWeight: 700, lineHeight: 1.15, marginBottom: 24, margin: "0 0 24px 0" }}>
          Turn your script into a<br />
          <span style={{ color: "#6D5DFC" }}>complete AI film</span>
        </h1>
        <p style={{ fontSize: 18, color: "rgba(255,255,255,0.55)", marginBottom: 40, maxWidth: 600, margin: "0 auto 40px" }}>
          CineGen AI orchestrates the entire production pipeline — characters, environments, voice, music, and continuity — producing long-form videos up to 40 minutes.
        </p>
        <div style={{ display: "flex", gap: 16, justifyContent: "center", flexWrap: "wrap" }}>
          <Link href="/auth/signup" style={{ background: "#6D5DFC", color: "white", textDecoration: "none", padding: "14px 32px", borderRadius: 10, fontWeight: 600, fontSize: 16, display: "flex", alignItems: "center", gap: 8 }}>
            Start creating <ArrowRight size={18} />
          </Link>
          <button style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.2)", color: "white", padding: "14px 32px", borderRadius: 10, fontWeight: 500, fontSize: 16, cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}>
            <Play size={18} /> Watch demo
          </button>
        </div>
      </section>

      {/* Features */}
      <section style={{ maxWidth: 1000, margin: "0 auto", padding: "0 32px 80px", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 20 }}>
        {[
          { icon: Film, title: "Script to film", desc: "Upload any script and our AI breaks it into scenes, shots, characters and locations automatically." },
          { icon: Shield, title: "Character consistency", desc: "Our continuity engine keeps every character looking identical across hundreds of AI-generated shots." },
          { icon: Zap, title: "Full audio pipeline", desc: "Voice, music, and sound effects generated and synced automatically to every scene." },
        ].map((f) => (
          <div key={f.title} style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 16, padding: 28 }}>
            <div style={{ width: 44, height: 44, background: "rgba(109,93,252,0.15)", borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 16 }}>
              <f.icon size={22} color="#6D5DFC" />
            </div>
            <h3 style={{ fontSize: 17, fontWeight: 600, marginBottom: 10, margin: "0 0 10px 0" }}>{f.title}</h3>
            <p style={{ fontSize: 14, color: "rgba(255,255,255,0.55)", lineHeight: 1.6, margin: 0 }}>{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Pricing */}
      <section style={{ maxWidth: 1000, margin: "0 auto", padding: "0 32px 80px" }}>
        <h2 style={{ textAlign: "center", fontSize: 32, fontWeight: 700, marginBottom: 48 }}>Simple pricing</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 20 }}>
          {[
            { name: "Starter", price: "$29", desc: "5 projects/month", features: ["Up to 5 min videos", "Basic characters", "720p export", "Email support"], popular: false },
            { name: "Pro", price: "$79", desc: "25 projects/month", features: ["Up to 20 min videos", "Advanced continuity", "1080p export", "Priority support"], popular: true },
            { name: "Studio", price: "$199", desc: "Unlimited projects", features: ["Up to 40 min videos", "Full AI director", "4K export", "Dedicated support"], popular: false },
          ].map((plan) => (
            <div key={plan.name} style={{ background: plan.popular ? "rgba(109,93,252,0.1)" : "rgba(255,255,255,0.04)", border: plan.popular ? "1px solid #6D5DFC" : "1px solid rgba(255,255,255,0.1)", borderRadius: 16, padding: 28, position: "relative" }}>
              {plan.popular && (
                <div style={{ position: "absolute", top: -12, left: "50%", transform: "translateX(-50%)", background: "#6D5DFC", color: "white", fontSize: 12, fontWeight: 600, padding: "3px 14px", borderRadius: 20 }}>Most popular</div>
              )}
              <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>{plan.name}</div>
              <div style={{ fontSize: 38, fontWeight: 700, marginBottom: 4 }}>{plan.price}<span style={{ fontSize: 16, fontWeight: 400, color: "rgba(255,255,255,0.5)" }}>/mo</span></div>
              <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", marginBottom: 20 }}>{plan.desc}</div>
              <ul style={{ listStyle: "none", padding: 0, margin: "0 0 24px 0" }}>
                {plan.features.map(f => (
                  <li key={f} style={{ fontSize: 14, color: "rgba(255,255,255,0.7)", padding: "4px 0", display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ color: "#22C55E" }}>✓</span> {f}
                  </li>
                ))}
              </ul>
              <Link href="/auth/signup" style={{ display: "block", textAlign: "center", background: plan.popular ? "#6D5DFC" : "rgba(255,255,255,0.1)", color: "white", textDecoration: "none", padding: "10px 0", borderRadius: 8, fontWeight: 500 }}>
                Get started
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: "1px solid rgba(255,255,255,0.1)", padding: "24px 32px", textAlign: "center", color: "rgba(255,255,255,0.3)", fontSize: 13 }}>
        © 2025 CineGen AI. All rights reserved.
      </footer>
    </div>
  )
}
