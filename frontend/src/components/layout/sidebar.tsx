"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  PlusCircle,
  Clock,
  Bookmark,
  Settings,
  LogOut,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/research/new", label: "New Research", icon: PlusCircle },
  { href: "/history", label: "History", icon: Clock },
  { href: "/saved", label: "Saved Reports", icon: Bookmark },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const path = usePathname();

  return (
    <aside className="hidden lg:flex flex-col w-64 min-h-screen bg-[#111827] border-r border-slate-800 p-5">
      {/* Logo */}
      <Link href="/dashboard" className="flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <span className="font-bold text-lg text-white">AI Research</span>
      </Link>

      {/* Nav */}
      <nav className="flex-1 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = path === href || (href !== "/dashboard" && path.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all",
                active
                  ? "bg-brand-600/20 text-brand-400 border border-brand-600/30"
                  : "text-slate-400 hover:text-white hover:bg-slate-800"
              )}
            >
              {active && (
                <motion.div
                  layoutId="nav-pill"
                  className="absolute left-0 w-1 h-8 bg-brand-500 rounded-r-full"
                />
              )}
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Sign out */}
      <button
        onClick={() => signOut({ callbackUrl: "/" })}
        className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all mt-4"
      >
        <LogOut className="w-4 h-4" />
        Sign Out
      </button>
    </aside>
  );
}
