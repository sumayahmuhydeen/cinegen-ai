import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "CineGen AI — AI Film Studio",
  description: "Transform scripts into complete long-form AI videos with persistent characters, intelligent directing, and cinematic continuity.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body style={{ fontFamily: "system-ui, -apple-system, sans-serif" }}>
        {children}
      </body>
    </html>
  )
}
