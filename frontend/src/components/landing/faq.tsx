"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";

const FAQS = [
  { q: "How is this different from ChatGPT?", a: "The platform runs a 5-agent pipeline that searches real academic sources (arXiv, IEEE, ACM) and validates them before synthesizing. ChatGPT relies on training data. The platform produces citations you can verify." },
  { q: "Which LLM does the assistant use?", a: "Claude Sonnet by Anthropic powers the Planner and Synthesizer agents. Claude Haiku powers the Extractor for speed. Claude is chosen for its reasoning accuracy and long-context support." },
  { q: "How long does a report take?", a: "Most reports complete in 2–4 minutes depending on topic complexity and source availability." },
  { q: "Can I trust the citations?", a: "Each source is independently fetched, scored, and validated before being included. Links in the References section point to the original papers or pages." },
  { q: "Is my data private?", a: "Reports are stored in your private account and are never shared. API keys for Claude and Tavily are used only to power your requests." },
];

export function FAQ() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section className="py-24 px-6 bg-slate-900/30">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-3">Frequently asked questions</h2>
        </div>
        <div className="space-y-3">
          {FAQS.map(({ q, a }, i) => (
            <div key={i} className="glass rounded-xl overflow-hidden">
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between px-5 py-4 text-left"
              >
                <span className="font-medium text-white text-sm">{q}</span>
                <ChevronDown className={`w-4 h-4 text-slate-400 transition ${open === i ? "rotate-180" : ""}`} />
              </button>
              <AnimatePresence>
                {open === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <p className="px-5 pb-4 text-sm text-slate-400 leading-relaxed">{a}</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
