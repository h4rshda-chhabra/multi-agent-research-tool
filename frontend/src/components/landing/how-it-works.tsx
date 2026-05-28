"use client";

import { motion } from "framer-motion";

const STEPS = [
  { step: "01", title: "Enter a topic", description: "Type any research topic — a concept, technology, or question." },
  { step: "02", title: "Agents activate", description: "Planner → Search → Validator → Extractor → Synthesizer run in sequence." },
  { step: "03", title: "Watch live progress", description: "Track each agent in real-time via the progress timeline." },
  { step: "04", title: "Get your report", description: "A structured 10-section report with citations, tables and references." },
];

export function HowItWorks() {
  return (
    <section className="py-24 px-6 bg-slate-900/30">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">How it works</h2>
          <p className="text-slate-400">From topic to report in 4 steps.</p>
        </div>

        <div className="relative">
          <div className="absolute left-12 top-0 bottom-0 w-px bg-gradient-to-b from-brand-600 via-brand-600/50 to-transparent hidden md:block" />

          <div className="space-y-8">
            {STEPS.map(({ step, title, description }, i) => (
              <motion.div
                key={step}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="flex items-start gap-6"
              >
                <div className="w-10 h-10 rounded-full bg-brand-600 flex items-center justify-center font-mono text-sm font-bold text-white flex-shrink-0 relative z-10">
                  {step}
                </div>
                <div className="pt-1">
                  <h3 className="font-semibold text-white mb-1">{title}</h3>
                  <p className="text-slate-400 text-sm">{description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
