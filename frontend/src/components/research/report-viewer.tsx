"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import { useSession } from "next-auth/react";
import {
  Download,
  Bookmark,
  BookmarkCheck,
  ExternalLink,
  Loader2,
  Star,
  BookOpen,
  X,
} from "lucide-react";
import { cn, formatDate } from "@/lib/utils";
import { API_URL } from "@/lib/config";
import { useSaveReport, useUnsaveReport } from "@/hooks/use-research";
import toast from "react-hot-toast";
import type { Report } from "@/types";

interface Props {
  report: Report;
}

export function ReportViewer({ report }: Props) {
  const [activeTab, setActiveTab] = useState<"report" | "sources">("report");
  const [exporting, setExporting] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data: session } = useSession();
  const { mutate: save, isPending: saving } = useSaveReport();
  const { mutate: unsave, isPending: unsaving } = useUnsaveReport();

  const handleSave = () => {
    if (report.is_saved) unsave(report.id);
    else save(report.id);
  };

  const handleExport = (format: "pdf" | "markdown") => {
    const token = (session?.user as { access_token?: string })?.access_token;
    if (!token) {
      toast.error("Session expired. Please sign in again.");
      return;
    }
    setExporting(true);
    const url = `${API_URL}/api/v1/export?report_id=${report.id}&format=${format}&token=${encodeURIComponent(token)}`;
    const a = document.createElement("a");
    a.href = url;
    a.rel = "noopener noreferrer";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => setExporting(false), 1500);
    toast.success(`Downloading ${format.toUpperCase()}…`);
  };

  return (
    <>
      {/* ── Panel (fills grid cell height) ────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="h-full flex flex-col gap-3 min-h-0"
      >
        {/* Toolbar */}
        <div className="glass rounded-xl px-5 py-3 flex items-center justify-between flex-wrap gap-3 flex-shrink-0">
          <div>
            <h2 className="font-semibold text-white text-sm line-clamp-1">{report.topic}</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {formatDate(report.created_at)} · {report.sources.length} sources
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              disabled={saving || unsaving}
              className={cn(
                "flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border transition",
                report.is_saved
                  ? "bg-brand-600/20 border-brand-600/30 text-brand-400"
                  : "border-slate-700 text-slate-400 hover:text-white hover:border-slate-600"
              )}
            >
              {report.is_saved ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
              {report.is_saved ? "Saved" : "Save"}
            </button>
            <button
              onClick={() => handleExport("markdown")}
              disabled={exporting}
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-white hover:border-slate-600 transition disabled:opacity-50"
            >
              {exporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
              .md
            </button>
            <button
              onClick={() => handleExport("pdf")}
              disabled={exporting}
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition disabled:opacity-50"
            >
              {exporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
              PDF
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-800/50 p-1 rounded-xl w-fit flex-shrink-0">
          {(["report", "sources"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "px-4 py-1.5 rounded-lg text-sm font-medium capitalize transition",
                activeTab === tab
                  ? "bg-brand-600 text-white"
                  : "text-slate-400 hover:text-white"
              )}
            >
              {tab}
              {tab === "sources" && (
                <span className="ml-1.5 text-xs bg-white/10 px-1.5 py-0.5 rounded-full">
                  {report.sources.length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Content area — fills remaining height */}
        <div className="flex-1 min-h-0 overflow-hidden">
          {/* ── Report preview ───────────────────────────────────────── */}
          {activeTab === "report" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="glass rounded-2xl h-full flex flex-col overflow-hidden relative group cursor-pointer"
              onClick={() => setIsModalOpen(true)}
            >
              {/* Scrollable preview content (pointer-events off so clicks reach parent) */}
              <div className="flex-1 min-h-0 overflow-hidden px-8 pt-8 pb-0 pointer-events-none select-none">
                <div className="prose prose-invert max-w-none text-sm">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                    {report.markdown_content ?? ""}
                  </ReactMarkdown>
                </div>
              </div>

              {/* Gradient fade + CTA */}
              <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-[#111827] via-[#111827]/80 to-transparent pointer-events-none" />
              <div className="relative flex items-center justify-center pb-7 flex-shrink-0">
                <button className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold px-6 py-2.5 rounded-xl transition shadow-lg shadow-brand-600/30 group-hover:scale-105 duration-150 pointer-events-auto">
                  <BookOpen className="w-4 h-4" />
                  Read Full Report
                </button>
              </div>
            </motion.div>
          )}

          {/* ── Sources ───────────────────────────────────────────────── */}
          {activeTab === "sources" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="h-full overflow-y-auto space-y-3 pr-1"
            >
              {report.sources
                .sort((a, b) => b.total_score - a.total_score)
                .map((source) => (
                  <div key={source.id} className="glass rounded-xl p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-brand-400 hover:text-brand-300 flex items-center gap-1 mb-1 group"
                        >
                          <span className="truncate">{source.title}</span>
                          <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 flex-shrink-0 transition" />
                        </a>
                        <p className="text-xs text-slate-500 mb-2">{source.domain}</p>
                        {source.snippet && (
                          <p className="text-xs text-slate-400 line-clamp-2">{source.snippet}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-1 text-yellow-400 flex-shrink-0">
                        <Star className="w-3.5 h-3.5 fill-current" />
                        <span className="text-xs font-semibold">{source.total_score.toFixed(1)}</span>
                      </div>
                    </div>
                    <div className="flex gap-3 mt-3 pt-3 border-t border-slate-800">
                      {[
                        { label: "Relevance", value: source.relevance_score },
                        { label: "Credibility", value: source.credibility_score },
                        { label: "Recency", value: source.recency_score },
                        { label: "Depth", value: source.technical_depth_score },
                      ].map(({ label, value }) => (
                        <div key={label} className="flex-1">
                          <p className="text-[10px] text-slate-600 mb-1">{label}</p>
                          <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-brand-500 rounded-full"
                              style={{ width: `${(value / 10) * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
            </motion.div>
          )}
        </div>
      </motion.div>

      {/* ── Full-report modal ──────────────────────────────────────────── */}
      <AnimatePresence>
        {isModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 bg-black/70 backdrop-blur-sm"
            onClick={() => setIsModalOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: 16 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: 16 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="bg-[#0f1623] border border-slate-800 rounded-2xl w-full max-w-4xl h-[88vh] flex flex-col shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal header */}
              <div className="flex items-center justify-between px-7 py-4 border-b border-slate-800 flex-shrink-0">
                <div>
                  <h2 className="font-semibold text-white text-base line-clamp-1">
                    {report.topic}
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {formatDate(report.created_at)} · {report.sources.length} sources
                  </p>
                </div>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition flex-shrink-0"
                  aria-label="Close"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal body — full scrollable report */}
              <div className="flex-1 overflow-y-auto px-7 md:px-10 py-8">
                <div className="prose prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                    {report.markdown_content ?? ""}
                  </ReactMarkdown>
                </div>
              </div>

              {/* Modal footer */}
              <div className="flex items-center justify-end gap-3 px-7 py-4 border-t border-slate-800 flex-shrink-0">
                <button
                  onClick={() => handleExport("markdown")}
                  disabled={exporting}
                  className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-white hover:border-slate-600 transition disabled:opacity-50"
                >
                  {exporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                  .md
                </button>
                <button
                  onClick={() => handleExport("pdf")}
                  disabled={exporting}
                  className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition disabled:opacity-50"
                >
                  {exporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                  PDF
                </button>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="text-xs font-medium px-4 py-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-white hover:border-slate-600 transition"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
