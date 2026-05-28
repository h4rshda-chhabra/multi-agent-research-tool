"use client";

import { use, useEffect } from "react";
import { motion } from "framer-motion";
import { AlertCircle, Loader2 } from "lucide-react";
import { AgentTimeline } from "@/components/research/agent-timeline";
import { ReportViewer } from "@/components/research/report-viewer";
import { useReport } from "@/hooks/use-research";
import { useSSE } from "@/hooks/use-sse";

export default function ResearchPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: report, refetch } = useReport(id);
  const { steps, isDone, isError, errorMessage } = useSSE(
    report?.status === "running" ? id : null
  );

  useEffect(() => {
    if (isDone) refetch();
  }, [isDone, refetch]);

  const isRunning = report?.status === "running" || report?.status === "pending";
  const isFailed = report?.status === "failed" || isError;

  return (
    <div className="px-4 md:px-8 py-8 max-w-6xl mx-auto">
      {/* Running state: two-column layout */}
      {isRunning && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <div className="mb-4">
                <p className="text-sm text-slate-400 mb-1">Researching</p>
                <h2 className="text-xl font-bold text-white">{report?.topic}</h2>
              </div>
              <AgentTimeline steps={steps} />
            </motion.div>
          </div>
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="glass rounded-2xl p-8 h-full min-h-64 flex flex-col items-center justify-center text-center"
            >
              <div className="w-14 h-14 rounded-2xl bg-brand-600/20 flex items-center justify-center mb-4">
                <Loader2 className="w-7 h-7 text-brand-400 animate-spin" />
              </div>
              <p className="text-white font-semibold mb-2">Agents are working…</p>
              <p className="text-slate-400 text-sm">
                Your report will appear here as soon as all agents complete.
              </p>
            </motion.div>
          </div>
        </div>
      )}

      {/* Failed state */}
      {isFailed && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass rounded-2xl p-8 text-center max-w-md mx-auto"
        >
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-4" />
          <p className="text-white font-semibold mb-2">Research failed</p>
          <p className="text-slate-400 text-sm">
            {report?.error_message || errorMessage || "An unexpected error occurred."}
          </p>
        </motion.div>
      )}

      {/* Complete state */}
      {report?.status === "complete" && report.markdown_content && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <AgentTimeline
              steps={steps.map((s) => ({ ...s, status: s.status === "idle" ? "complete" : s.status }))}
            />
          </div>
          <div className="lg:col-span-2">
            <ReportViewer report={report} />
          </div>
        </div>
      )}
    </div>
  );
}
