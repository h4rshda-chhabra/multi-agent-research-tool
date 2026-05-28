"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Perfect for getting started",
    features: ["5 reports/month", "Standard sources", "Markdown export", "7-day history"],
    cta: "Get Started",
    href: "/sign-up",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$19",
    period: "/month",
    description: "For serious researchers",
    features: ["Unlimited reports", "Priority processing", "PDF export", "All sources", "Unlimited history", "API access"],
    cta: "Start Pro",
    href: "/sign-up",
    highlight: true,
  },
];

export function Pricing() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Simple pricing</h2>
          <p className="text-slate-400">Start free, upgrade when you need more.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto">
          {PLANS.map(({ name, price, period, description, features, cta, href, highlight }, i) => (
            <motion.div
              key={name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className={`rounded-2xl p-7 border ${highlight ? "bg-brand-600/20 border-brand-600/50 glow" : "glass"}`}
            >
              {highlight && (
                <div className="text-xs font-semibold text-brand-300 bg-brand-600/30 px-2.5 py-1 rounded-full inline-block mb-3">
                  MOST POPULAR
                </div>
              )}
              <p className="font-bold text-xl text-white">{name}</p>
              <div className="flex items-baseline gap-1 mt-2 mb-1">
                <span className="text-4xl font-black text-white">{price}</span>
                <span className="text-slate-400 text-sm">{period}</span>
              </div>
              <p className="text-sm text-slate-400 mb-6">{description}</p>

              <ul className="space-y-3 mb-8">
                {features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-slate-300">
                    <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>

              <Link
                href={href}
                className={`block text-center font-semibold py-3 rounded-xl transition text-sm ${
                  highlight
                    ? "bg-brand-600 hover:bg-brand-700 text-white"
                    : "border border-slate-600 text-slate-300 hover:text-white hover:border-slate-500"
                }`}
              >
                {cta}
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
