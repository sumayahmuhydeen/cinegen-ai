"use client"
import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { supabase } from "@/lib/supabase"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Film } from "lucide-react"

export default function SignupPage() {
  const router = useRouter()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState(false)

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")
    const { error } = await supabase.auth.signUp({
      email, password,
      options: { data: { full_name: name } }
    })
    if (error) { setError(error.message); setLoading(false) }
    else setSuccess(true)
  }

  if (success) return (
    <div className="min-h-screen bg-[#0D0D1A] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-[#22C55E]/20 rounded-full flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl">✉️</span>
        </div>
        <h2 className="text-2xl font-bold text-white mb-3">Check your email</h2>
        <p className="text-white/50">We sent a confirmation link to <strong className="text-white">{email}</strong>. Click it to activate your account.</p>
        <Link href="/auth/login" className="inline-block mt-6 text-[#6D5DFC] hover:underline text-sm">Back to sign in</Link>
      </div>
    </div>
  )

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
          <h1 className="text-2xl font-bold text-white">Create your account</h1>
          <p className="text-white/50 mt-1">Start building AI films today</p>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl p-8">
          <form onSubmit={handleSignup} className="space-y-4">
            {error && <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 text-red-400 text-sm">{error}</div>}
            <div className="space-y-1.5">
              <Label className="text-white/70">Full name</Label>
              <Input placeholder="Your name" value={name} onChange={e => setName(e.target.value)} required className="bg-white/5 border-white/20 text-white placeholder:text-white/30" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-white/70">Email</Label>
              <Input type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required className="bg-white/5 border-white/20 text-white placeholder:text-white/30" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-white/70">Password</Label>
              <Input type="password" placeholder="At least 8 characters" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} className="bg-white/5 border-white/20 text-white placeholder:text-white/30" />
            </div>
            <Button type="submit" className="w-full bg-[#6D5DFC] hover:bg-[#5648d4]" disabled={loading}>
              {loading ? "Creating account..." : "Create account"}
            </Button>
          </form>
          <p className="text-center text-white/40 text-sm mt-6">
            Already have an account? <Link href="/auth/login" className="text-[#6D5DFC] hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
