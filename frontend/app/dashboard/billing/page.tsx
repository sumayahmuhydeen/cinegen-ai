"use client"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { CheckCircle, Zap, CreditCard, Download } from "lucide-react"

const plans = [
  {
    id: "starter", name: "Starter", price: "$29", period: "/month",
    desc: "Perfect for individuals getting started",
    features: ["5 projects/month", "Up to 5 min videos", "Basic character engine", "720p export", "Email support"],
    credits: 500,
  },
  {
    id: "pro", name: "Pro", price: "$79", period: "/month",
    desc: "For serious creators and small teams",
    features: ["25 projects/month", "Up to 20 min videos", "Advanced continuity engine", "1080p export", "Priority support", "Character Bible locking"],
    credits: 2000, popular: true,
  },
  {
    id: "studio", name: "Studio", price: "$199", period: "/month",
    desc: "Unlimited production for studios",
    features: ["Unlimited projects", "Up to 40 min videos", "Full AI director", "4K export", "Dedicated support", "API access", "Team seats (5)"],
    credits: 10000,
  },
]

const invoices = [
  { id: "INV-001", date: "Jun 1, 2025", amount: "$79.00", status: "Paid", plan: "Pro" },
  { id: "INV-002", date: "May 1, 2025", amount: "$79.00", status: "Paid", plan: "Pro" },
  { id: "INV-003", date: "Apr 1, 2025", amount: "$29.00", status: "Paid", plan: "Starter" },
]

export default function BillingPage() {
  const [currentPlan, setCurrentPlan] = useState("pro")
  const [billing, setBilling] = useState<"monthly"|"annual">("monthly")

  return (
    <div className="p-8 max-w-5xl">
      <h1 className="text-2xl font-bold text-white mb-2">Billing</h1>
      <p className="text-white/50 mb-8">Manage your subscription and usage</p>

      {/* Current usage */}
      <Card className="bg-white/5 border-white/10 mb-8">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm text-white/50 mb-1">Current plan</div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold text-white">Pro Plan</span>
                <Badge variant="purple">Active</Badge>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-white/50">Next billing date</div>
              <div className="text-white font-medium">July 1, 2025</div>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 mt-4">
            {[
              { label: "AI Credits", used: 840, total: 2000 },
              { label: "Projects", used: 4, total: 25 },
              { label: "Video minutes", used: 192, total: 500 },
            ].map(item => (
              <div key={item.label}>
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="text-white/60">{item.label}</span>
                  <span className="text-white/40">{item.used}/{item.total}</span>
                </div>
                <Progress value={(item.used/item.total)*100} className="h-1.5" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Billing toggle */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">Change plan</h2>
        <div className="flex items-center gap-1 bg-white/5 border border-white/10 rounded-lg p-1">
          {(["monthly","annual"] as const).map(b => (
            <button key={b} onClick={() => setBilling(b)}
              className={`px-4 py-1.5 rounded-md text-sm transition-colors capitalize ${billing === b ? "bg-[#6D5DFC] text-white" : "text-white/50 hover:text-white"}`}>
              {b} {b === "annual" && <span className="text-[#22C55E] text-xs ml-1">-20%</span>}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-5 mb-10">
        {plans.map(plan => (
          <Card key={plan.id} className={`border transition-all ${currentPlan === plan.id ? "border-[#6D5DFC] bg-[#6D5DFC]/5" : "border-white/10 bg-white/5"}`}>
            <CardContent className="p-5">
              {plan.popular && <Badge variant="purple" className="mb-3 text-xs">Most popular</Badge>}
              <div className="text-lg font-bold text-white mb-1">{plan.name}</div>
              <div className="flex items-baseline gap-1 mb-1">
                <span className="text-3xl font-bold text-white">{billing === "annual" ? `$${parseInt(plan.price.slice(1))*0.8|0}` : plan.price}</span>
                <span className="text-white/40 text-sm">{plan.period}</span>
              </div>
              <div className="text-xs text-white/40 mb-4">{plan.desc}</div>
              <div className="flex items-center gap-1 mb-4 text-xs text-[#6D5DFC]">
                <Zap className="w-3 h-3" /> {plan.credits.toLocaleString()} credits/month
              </div>
              <ul className="space-y-2 mb-5">
                {plan.features.map(f => (
                  <li key={f} className="flex items-center gap-2 text-xs text-white/60">
                    <CheckCircle className="w-3 h-3 text-[#22C55E] flex-shrink-0" /> {f}
                  </li>
                ))}
              </ul>
              {currentPlan === plan.id ? (
                <Button variant="outline" className="w-full border-[#6D5DFC] text-[#6D5DFC] text-sm" disabled>Current plan</Button>
              ) : (
                <Button className="w-full bg-[#6D5DFC] hover:bg-[#5648d4] text-sm" onClick={() => setCurrentPlan(plan.id)}>
                  {plans.findIndex(p=>p.id===plan.id) > plans.findIndex(p=>p.id===currentPlan) ? "Upgrade" : "Downgrade"}
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Payment method */}
      <Card className="bg-white/5 border-white/10 mb-8">
        <CardHeader><CardTitle className="text-white text-base flex items-center gap-2"><CreditCard className="w-4 h-4" /> Payment method</CardTitle></CardHeader>
        <CardContent className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-7 bg-white/10 rounded flex items-center justify-center text-xs text-white font-bold">VISA</div>
            <div>
              <div className="text-sm text-white">•••• •••• •••• 4242</div>
              <div className="text-xs text-white/40">Expires 12/27</div>
            </div>
          </div>
          <Button size="sm" variant="outline" className="border-white/20 text-white/60 hover:text-white">Update</Button>
        </CardContent>
      </Card>

      {/* Invoices */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader><CardTitle className="text-white text-base">Invoice history</CardTitle></CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10">
                {["Invoice", "Date", "Plan", "Amount", "Status", ""].map(h => (
                  <th key={h} className="text-left px-5 py-3 text-white/40 font-medium text-xs">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {invoices.map(inv => (
                <tr key={inv.id} className="border-b border-white/5">
                  <td className="px-5 py-3 text-white font-mono text-xs">{inv.id}</td>
                  <td className="px-5 py-3 text-white/60">{inv.date}</td>
                  <td className="px-5 py-3 text-white/60">{inv.plan}</td>
                  <td className="px-5 py-3 text-white font-medium">{inv.amount}</td>
                  <td className="px-5 py-3"><Badge variant="success" className="text-xs">{inv.status}</Badge></td>
                  <td className="px-5 py-3">
                    <button className="text-[#6D5DFC] hover:underline text-xs flex items-center gap-1">
                      <Download className="w-3 h-3" /> PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
