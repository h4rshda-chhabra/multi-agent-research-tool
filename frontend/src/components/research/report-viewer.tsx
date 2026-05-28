"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import {
  Download,
  Bookmark,
  BookmarkCheck,
  ExternalLink,
  Star,
} from "lucide-react";
import { cn, formatDate } from "@/lib/utils";
import { useSaveReport, useUnsaveReport, useExportReport } from "@/hooks/use-research";
import type { Report } from "@/types";

interface Props {
  report: Report;
}

export function ReportViewer({ report }: Props) {
  const [activeTab, setActiveTab] = useState<"report" | "sources">("report");
  const { mutate: save, isPending: saving } = useSaveReport();
  const { mutate: unsave, isPending: unsaving } = useUnsaveReport();
  const { mutate: exportFn, isPending: exporting } = useExportReport();

  const handleSave = () => {
    if (report.is_saved) unsave(report.id);
    else save(report.id);
  };

  const handleExport = (format: "pdf" | "markdown") => {
    exportFn({ reportId: report.id, format });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* Toolbar */}
      <div className="glass rounded-xl px-5 py-3 flex items-center justify-between flex-wrap gap-3">
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
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-white hover:border-slate-600 transition"
          >
            <Download className="w-3.5 h-3.5" />
            .md
          </button>
          <button
            onClick={() => handleExport("pdf")}
            disabled={exporting}
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition"
          >
            <Download className="w-3.5 h-3.5" />
            PDF
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-800/50 p-1 rounded-xl w-fit">
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

      {/* Report Content */}
      {activeTab === "report" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass rounded-2xl p-8"
        >
          <div className="prose">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
              {report.markdown_content ?? ""}
            </ReactMarkdown>
          </div>
        </motion.div>
      )}

      {/* Sources */}
      {activeTab === "sources" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-3"
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
    </motion.div>
  );
}
