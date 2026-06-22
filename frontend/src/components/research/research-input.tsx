"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Search, Sparkles, Loader2 } from "lucide-react";
import { useStartResearch } from "@/hooks/use-research";
import toast from "react-hot-toast";

const SUGGESTIONS = [
  "Retrieval Augmented Generation in LLMs",
  "Transformer architecture explained",
  "Quantum computing and cryptography",
  "Diffusion models for image synthesis",
  "Graph Neural Networks applications",
];

const MODELS = [
  { id: "", name: "Default (Gemini 2.5 Flash)" },
  { id: "google/gemma-4-31b-it:free", name: "Gemma 4 31B (Free)" },
  { id: "meta-llama/llama-3.2-3b-instruct:free", name: "Llama 3.2 3B (Free)" },
  { id: "meta-llama/llama-3.3-70b-instruct:free", name: "Llama 3.3 70B (Free)" },
  { id: "qwen/qwen3-coder:free", name: "Qwen 3 Coder (Free)" },
];

export function ResearchInput() {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [model, setModel] = useState("");
  const { mutateAsync: start, isPending } = useStartResearch();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = topic.trim();
    if (!trimmed || trimmed.length < 5) {
      toast.error("Please enter a topic (min 5 characters)");
      return;
    }
    try {
      const { report_id } = await start({ topic: trimmed, model: model || undefined });
      router.push(`/research/${report_id}`);
    } catch {
      // onError in useStartResearch already shows a toast; swallow the rejection
      // so it doesn't surface as an unhandled promise error in the console.
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10"
      >
        <div className="inline-flex items-center gap-2 bg-brand-600/20 text-brand-400 border border-brand-600/30 text-sm font-medium px-4 py-1.5 rounded-full mb-5">
          <Sparkles className="w-3.5 h-3.5" />
          Multi-Agent Research Engine
        </div>
        <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
          What do you want to<br />
          <span className="text-brand-400">research today?</span>
        </h1>
        <p className="text-slate-400">
          Enter any topic and our 5-agent pipeline will generate a citation-backed report in minutes.
        </p>
      </motion.div>

      <motion.form
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        onSubmit={handleSubmit}
      >
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., Retrieval Augmented Generation"
            className="w-full bg-slate-800/80 border border-slate-700 rounded-2xl pl-12 pr-36 py-4 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500 transition text-base"
          />
          <button
            type="submit"
            disabled={isPending || !topic.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-brand-600 hover:bg-brand-700 text-white font-medium px-5 py-2.5 rounded-xl transition disabled:opacity-50 flex items-center gap-2"
          >
            {isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {isPending ? "Starting…" : "Research"}
          </button>
        </div>

        <div className="mt-4 flex items-center justify-center gap-2">
          <span className="text-sm text-slate-400">AI Model:</span>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="bg-slate-800/80 border border-slate-700 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-brand-500 transition cursor-pointer"
          >
            {MODELS.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>
      </motion.form>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="mt-6"
      >
        <p className="text-xs text-slate-500 mb-3">Try these examples:</p>
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setTopic(s)}
              className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 px-3 py-1.5 rounded-lg transition"
            >
              {s}
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
