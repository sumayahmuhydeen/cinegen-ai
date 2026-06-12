"use client"
import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { supabase } from "@/lib/supabase"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Film } from "lucide-react"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) { setError(error.message); setLoading(false) }
    else router.push("/dashboard")
  }

  async function handleGoogle() {
    await supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo: `${window.location.origin}/dashboard` } })
  }

  async function handleGithub() {
    await supabase.auth.signInWithOAuth({ provider: "github", options: { redirectTo: `${window.location.origin}/dashboard` } })
  }

  return (
    <div className="min-h-screen bg-[#0D0D1A] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-9 h-9 bg-[#6D5DFC] rounded-lg flex items-center justify-center">
              <Film className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-white">CineGen AI</span>
          </Link>
          <h1 className="text-2xl font-bold text-white">Welcome back</h1>
          <p className="text-white/50 mt-1">Sign in to your account</p>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-xl p-8">
          <div className="grid grid-cols-2 gap-3 mb-6">
            <button onClick={handleGoogle} className="flex items-center justify-center gap-2 border border-white/20 rounded-lg py-2.5 text-sm text-white hover:bg-white/10 transition-colors">
              <svg className="w-4 h-4" viewBox="0 0 24 24"><path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
              Google
            </button>
            <button onClick={handleGithub} className="flex items-center justify-center gap-2 border border-white/20 rounded-lg py-2.5 text-sm text-white hover:bg-white/10 transition-colors">
              GitHub
            </button>
          </div>

          <div className="flex items-center gap-3 mb-6">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-white/30 text-xs">or continue with email</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            {error && <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 text-red-400 text-sm">{error}</div>}
            <div className="space-y-1.5">
              <Label className="text-white/70">Email</Label>
              <Input type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required className="bg-white/5 border-white/20 text-white placeholder:text-white/30" />
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label className="text-white/70">Password</Label>
                <Link href="/auth/forgot-password" className="text-xs text-[#6D5DFC] hover:underline">Forgot password?</Link>
              </div>
              <Input type="password" placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} required className="bg-white/5 border-white/20 text-white placeholder:text-white/30" />
            </div>
            <Button type="submit" className="w-full bg-[#6D5DFC] hover:bg-[#5648d4]" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </Button>
          </form>

          <p className="text-center text-white/40 text-sm mt-6">
            No account? <Link href="/auth/signup" className="text-[#6D5DFC] hover:underline">Sign up free</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
