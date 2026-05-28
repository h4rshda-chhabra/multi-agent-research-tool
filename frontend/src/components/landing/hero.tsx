"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles, ArrowRight, Brain, Search, ShieldCheck, FileSearch, BookOpen } from "lucide-react";

const AGENTS = [
  { icon: Brain, label: "Planner", color: "bg-purple-500/20 text-purple-400" },
  { icon: Search, label: "Search", color: "bg-blue-500/20 text-blue-400" },
  { icon: ShieldCheck, label: "Validator", color: "bg-green-500/20 text-green-400" },
  { icon: FileSearch, label: "Extractor", color: "bg-orange-500/20 text-orange-400" },
  { icon: BookOpen, label: "Synthesizer", color: "bg-brand-500/20 text-brand-400" },
];

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-brand-600/10 rounded-full blur-[120px]" />
      </div>

      <div className="max-w-6xl mx-auto px-6 py-24 relative z-10 w-full">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-brand-600/20 text-brand-300 border border-brand-600/30 text-sm font-medium px-4 py-1.5 rounded-full mb-6"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Multi-Agent Research Intelligence
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-5xl md:text-7xl font-black text-white leading-tight mb-6"
          >
            Research Faster with{" "}
            <span className="bg-gradient-to-r from-brand-400 to-cyan-400 bg-clip-text text-transparent">
              AI-Powered
            </span>{" "}
            Multi-Agent Intelligence
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-lg text-slate-400 mb-8 max-w-2xl mx-auto leading-relaxed"
          >
            Generate citation-backed research reports from trusted academic sources in minutes.
            Five specialized agents collaborate to deliver evidence-quality research.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex items-center justify-center gap-4 flex-wrap"
          >
            <Link
              href="/sign-up"
              className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold px-6 py-3 rounded-xl transition text-sm"
            >
              Start Researching Free
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/sign-in"
              className="text-slate-300 hover:text-white font-medium px-6 py-3 rounded-xl border border-slate-700 hover:border-slate-600 transition text-sm"
            >
              Sign In
            </Link>
          </motion.div>
        </div>

        {/* Agent pipeline visualization */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="flex items-center justify-center gap-2 md:gap-4 flex-wrap"
        >
          {AGENTS.map(({ icon: Icon, label, color }, i) => (
            <div key={label} className="flex items-center gap-2 md:gap-4">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.5 + i * 0.1, type: "spring" }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border border-white/10 backdrop-blur-sm ${color.split(" ")[0]}`}
              >
                <Icon className={`w-4 h-4 ${color.split(" ")[1]}`} />
                <span className="text-sm font-medium text-white">{label}</span>
              </motion.div>
              {i < AGENTS.length - 1 && (
                <div className="text-slate-600 font-mono text-lg hidden sm:block">→</div>
              )}
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
