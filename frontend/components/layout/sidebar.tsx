"use client"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { Film, LayoutDashboard, FolderOpen, Settings, CreditCard, Shield, LogOut } from "lucide-react"
import { supabase } from "@/lib/supabase"

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/projects", label: "Projects", icon: FolderOpen },
  { href: "/dashboard/billing", label: "Billing", icon: CreditCard },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
  { href: "/admin", label: "Admin", icon: Shield },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()

  async function handleLogout() {
    await supabase.auth.signOut()
    router.push("/auth/login")
  }

  return (
    <aside style={{ width: 230, minHeight: "100vh", background: "#0D0D1A", borderRight: "1px solid rgba(255,255,255,0.08)", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "20px", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
        <Link href="/dashboard" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
          <div style={{ width: 32, height: 32, background: "#6D5DFC", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Film size={16} color="white" />
          </div>
          <span style={{ fontWeight: 600, color: "white", fontSize: 15 }}>CineGen AI</span>
        </Link>
      </div>

      <nav style={{ flex: 1, padding: "12px 8px" }}>
        {nav.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/")
          return (
            <Link key={item.href} href={item.href} style={{
              display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 8, marginBottom: 2,
              textDecoration: "none", fontSize: 14, fontWeight: active ? 500 : 400,
              background: active ? "rgba(109,93,252,0.15)" : "transparent",
              color: active ? "#6D5DFC" : "rgba(255,255,255,0.5)",
            }}>
              <item.icon size={16} />
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div style={{ padding: "8px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
        <button onClick={handleLogout} style={{
          display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 8, width: "100%",
          background: "transparent", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: 14,
        }}>
          <LogOut size={16} /> Sign out
        </button>
      </div>
    </aside>
  )
}
