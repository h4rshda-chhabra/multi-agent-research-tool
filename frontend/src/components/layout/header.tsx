"use client";

import { useSession } from "next-auth/react";
import Link from "next/link";
import { PlusCircle, Sparkles } from "lucide-react";

export function Header({ title }: { title: string }) {
  const { data: session } = useSession();

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#0f172a]/80 backdrop-blur-sm sticky top-0 z-10">
      <h1 className="text-lg font-semibold text-white">{title}</h1>
      <div className="flex items-center gap-4">
        <Link
          href="/research/new"
          className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-xl transition"
        >
          <PlusCircle className="w-4 h-4" />
          New Research
        </Link>
        <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-sm font-semibold">
          {session?.user?.name?.[0]?.toUpperCase() ?? "U"}
        </div>
      </div>
    </header>
  );
}

export function MobileHeader() {
  return (
    <header className="lg:hidden flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-[#111827]">
      <Link href="/dashboard" className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
          <Sparkles className="w-3.5 h-3.5 text-white" />
        </div>
        <span className="font-bold text-white">AI Research</span>
      </Link>
      <Link
        href="/research/new"
        className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition"
      >
        <PlusCircle className="w-3.5 h-3.5" />
        New
      </Link>
    </header>
  );
}
