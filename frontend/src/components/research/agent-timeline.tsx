"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Search,
  ShieldCheck,
  FileSearch,
  BookOpen,
  Lightbulb,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { AgentStep } from "@/types";

const AGENT_ICONS: Record<string, React.ElementType> = {
  planner: Brain,
  search: Search,
  validator: ShieldCheck,
  extractor: FileSearch,
  synthesizer: BookOpen,
  insights: Lightbulb,
};

interface Props {
  steps: AgentStep[];
}

export function AgentTimeline({ steps }: Props) {
  return (
    <div className="glass rounded-2xl p-6 h-full flex flex-col">
      <h3 className="text-sm font-semibold text-slate-300 mb-5 uppercase tracking-wider flex-shrink-0">
        Agent Pipeline
      </h3>

      {/* Steps — scrollable if they somehow overflow, but 5 agents always fit */}
      <div className="flex-1 min-h-0 overflow-y-auto space-y-4">
        {steps.map((step, i) => {
          const Icon = AGENT_ICONS[step.name];
          const isRunning = step.status === "running";
          const isComplete = step.status === "complete";
          const isError = step.status === "error";

          return (
            <motion.div
              key={step.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
              className={cn(
                "flex items-start gap-4 p-3.5 rounded-xl transition-all border",
                isRunning && "bg-brand-600/10 border-brand-600/30",
                isComplete && "bg-green-500/10 border-green-500/20",
                isError && "bg-red-500/10 border-red-500/20",
                step.status === "idle" && "border-slate-800"
              )}
            >
              {/* Icon */}
              <div
                className={cn(
                  "w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0",
                  isRunning && "bg-brand-600/30 text-brand-400",
                  isComplete && "bg-green-500/20 text-green-400",
                  isError && "bg-red-500/20 text-red-400",
                  step.status === "idle" && "bg-slate-800 text-slate-600"
                )}
              >
                {isRunning ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "text-sm font-medium",
                      isRunning && "text-brand-300",
                      isComplete && "text-green-300",
                      isError && "text-red-300",
                      step.status === "idle" && "text-slate-500"
                    )}
                  >
                    {step.label}
                  </span>

                  <AnimatePresence>
                    {isComplete && (
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                        <CheckCircle2 className="w-4 h-4 text-green-400" />
                      </motion.div>
                    )}
                    {isError && (
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                        <XCircle className="w-4 h-4 text-red-400" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {isRunning && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mt-1.5 h-1 bg-slate-700 rounded-full overflow-hidden"
                  >
                    <motion.div
                      className="h-full bg-brand-500 rounded-full"
                      animate={{ x: ["-100%", "100%"] }}
                      transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                    />
                  </motion.div>
                )}

                {step.message && (isComplete || isError) && (
                  <p className={cn("text-xs mt-1", isComplete ? "text-slate-400" : "text-red-400")}>
                    {step.message}
                  </p>
                )}
              </div>

              {/* Step number */}
              <span className="text-xs text-slate-600 font-mono flex-shrink-0">
                {String(steps.indexOf(step) + 1).padStart(2, "0")}
              </span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
