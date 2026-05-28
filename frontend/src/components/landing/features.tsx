"use client";

import { motion } from "framer-motion";
import { Brain, Search, ShieldCheck, FileSearch, BookOpen, Download } from "lucide-react";

const FEATURES = [
  {
    icon: Brain,
    title: "Intelligent Planning",
    description: "The Planner agent decomposes your topic into 6-8 targeted academic queries, identifying subtopics and research directions automatically.",
    color: "text-purple-400 bg-purple-400/10",
  },
  {
    icon: Search,
    title: "Trusted Source Search",
    description: "Searches Tavily and arXiv simultaneously, filtering for arxiv.org, IEEE, ACM, GitHub and top research institutions.",
    color: "text-blue-400 bg-blue-400/10",
  },
  {
    icon: ShieldCheck,
    title: "Source Validation",
    description: "Every source is scored on relevance, credibility, recency and technical depth. Spam and low-quality references are removed.",
    color: "text-green-400 bg-green-400/10",
  },
  {
    icon: FileSearch,
    title: "Deep Extraction",
    description: "The Extractor reads each paper and webpage, pulling out methodologies, benchmarks, metrics, and limitations in structured form.",
    color: "text-orange-400 bg-orange-400/10",
  },
  {
    icon: BookOpen,
    title: "Report Synthesis",
    description: "Claude Sonnet synthesizes all findings into a structured 10-section report with inline citations, comparison tables and references.",
    color: "text-brand-400 bg-brand-400/10",
  },
  {
    icon: Download,
    title: "PDF & Markdown Export",
    description: "Export your complete research report as a formatted PDF or raw Markdown — ready to include in papers, pitches or blogs.",
    color: "text-cyan-400 bg-cyan-400/10",
  },
];

export function Features() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Everything you need for serious research
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            A complete research pipeline — not a chatbot. Five agents work in sequence so every report is evidence-backed.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map(({ icon: Icon, title, description, color }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.07 }}
              className="glass rounded-2xl p-6 hover:bg-white/5 transition"
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white mb-2">{title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
