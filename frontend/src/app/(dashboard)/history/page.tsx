"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Clock, Loader2, Trash2, BookOpen, CheckCircle2, AlertCircle } from "lucide-react";
import { useReports, useDeleteReport } from "@/hooks/use-research";
import { formatRelative, truncate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { ReportStatus } from "@/types";

const STATUS_ICON: Record<ReportStatus, React.ElementType> = {
  pending: Clock,
  running: Loader2,
  complete: CheckCircle2,
  failed: AlertCircle,
};

const STATUS_COLOR: Record<ReportStatus, string> = {
  pending: "text-yellow-400",
  running: "text-brand-400",
  complete: "text-green-400",
  failed: "text-red-400",
};

export default function HistoryPage() {
  const { data: reports = [], isLoading } = useReports();
  const { mutate: remove } = useDeleteReport();

  return (
    <div className="px-6 py-8 max-w-4xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="text-2xl font-bold text-white">Research History</h1>
        <p className="text-slate-400 mt-1">{reports.length} report{reports.length !== 1 ? "s" : ""} total</p>
      </motion.div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
        </div>
      ) : reports.length === 0 ? (
        <div className="glass rounded-xl p-12 text-center">
          <BookOpen className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">No reports yet.</p>
          <Link href="/research/new" className="text-brand-400 text-sm mt-2 inline-block hover:underline">
            Start your first research →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((report, i) => {
            const Icon = STATUS_ICON[report.status];
            return (
              <motion.div
                key={report.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                className="glass rounded-xl p-4 flex items-center justify-between gap-3 group"
              >
                <Link href={`/research/${report.id}`} className="flex items-center gap-3 min-w-0 flex-1">
                  <Icon className={cn("w-4 h-4 flex-shrink-0", STATUS_COLOR[report.status], report.status === "running" && "animate-spin")} />
                  <div className="min-w-0">
                    <p className="text-sm text-slate-200 group-hover:text-white transition truncate">
                      {truncate(report.topic, 70)}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">{formatRelative(report.created_at)}</p>
                  </div>
                </Link>
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    if (confirm("Delete this report?")) remove(report.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1.5 text-slate-500 hover:text-red-400 transition rounded-lg hover:bg-red-400/10"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
