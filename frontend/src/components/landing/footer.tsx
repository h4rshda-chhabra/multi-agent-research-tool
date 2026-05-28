import Link from "next/link";
import { Sparkles } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-800 py-10 px-6">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-brand-400 font-bold">
          <Sparkles className="w-4 h-4" />
          AI Research Assistant
        </div>
        <p className="text-slate-500 text-sm">
          © {new Date().getFullYear()} AI Research Assistant. Built with Claude Sonnet &amp; LangGraph.
        </p>
        <div className="flex gap-4 text-sm text-slate-500">
          <Link href="/sign-in" className="hover:text-white transition">Sign In</Link>
          <Link href="/sign-up" className="hover:text-white transition">Sign Up</Link>
        </div>
      </div>
    </footer>
  );
}
