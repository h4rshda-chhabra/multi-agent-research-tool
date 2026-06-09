"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { PlusCircle, BookOpen, Clock, Bookmark, ArrowRight, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { useSession } from "next-auth/react";
import { useReports } from "@/hooks/use-research";
import { formatRelative, truncate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { ReportStatus } from "@/types";

const STATUS_CONFIG: Record<ReportStatus, { label: string; color: string; icon: React.ElementType }> = {
  pending: { label: "Queued", color: "text-yellow-400 bg-yellow-400/10", icon: Clock },
  running: { label: "Running", color: "text-brand-400 bg-brand-400/10", icon: Loader2 },
  complete: { label: "Complete", color: "text-green-400 bg-green-400/10", icon: CheckCircle2 },
  failed: { label: "Failed", color: "text-red-400 bg-red-400/10", icon: AlertCircle },
  cancelled: { label: "Cancelled", color: "text-yellow-400 bg-yellow-400/10", icon: AlertCircle },
};

export default function DashboardPage() {
  const { data: session } = useSession();
  const { data: reports = [], isLoading } = useReports();

  const stats = {
    total: reports.length,
    complete: reports.filter((r) => r.status === "complete").length,
    saved: reports.filter((r) => r.is_saved).length,
    running: reports.filter((r) => r.status === "running").length,
  };

  return (
    <div className="px-6 py-8 max-w-5xl mx-auto">
      {/* Welcome */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="text-2xl font-bold text-white">
          Welcome back, {session?.user?.name?.split(" ")[0]} 👋
        </h1>
        <p className="text-slate-400 mt-1">Here&apos;s your research overview.</p>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Total Reports", value: stats.total, icon: BookOpen, color: "text-brand-400" },
          { label: "Completed", value: stats.complete, icon: CheckCircle2, color: "text-green-400" },
          { label: "Saved", value: stats.saved, icon: Bookmark, color: "text-yellow-400" },
          { label: "In Progress", value: stats.running, icon: Loader2, color: "text-orange-400" },
        ].map(({ label, value, icon: Icon, color }, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="glass rounded-xl p-5"
          >
            <Icon className={cn("w-5 h-5 mb-3", color)} />
            <p className="text-2xl font-bold text-white">{value}</p>
            <p className="text-xs text-slate-400 mt-1">{label}</p>
          </motion.div>
        ))}
      </div>

      {/* New Research CTA */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <Link
          href="/research/new"
          className="flex items-center justify-between p-5 rounded-2xl bg-brand-600/20 border border-brand-600/30 hover:bg-brand-600/30 transition group"
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center">
              <PlusCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-semibold text-white">Start New Research</p>
              <p className="text-sm text-slate-400">Generate a citation-backed report in minutes</p>
            </div>
          </div>
          <ArrowRight className="w-5 h-5 text-brand-400 group-hover:translate-x-1 transition" />
        </Link>
      </motion.div>

      {/* Recent Reports */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25 }}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-white">Recent Reports</h2>
          <Link href="/history" className="text-sm text-brand-400 hover:text-brand-300">
            View all →
          </Link>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
          </div>
        ) : reports.length === 0 ? (
          <div className="glass rounded-xl p-8 text-center">
            <BookOpen className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400">No reports yet. Start your first research!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.slice(0, 5).map((report, i) => {
              const config = STATUS_CONFIG[report.status];
              const StatusIcon = config.icon;
              return (
                <motion.div
                  key={report.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + i * 0.04 }}
                >
                  <Link
                    href={`/research/${report.id}`}
                    className="flex items-center justify-between p-4 glass rounded-xl hover:bg-slate-800/50 transition group"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className={cn("flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium flex-shrink-0", config.color)}>
                        <StatusIcon className={cn("w-3 h-3", report.status === "running" && "animate-spin")} />
                        {config.label}
                      </div>
                      <p className="text-sm text-slate-200 truncate group-hover:text-white transition">
                        {truncate(report.topic, 60)}
                      </p>
                    </div>
                    <span className="text-xs text-slate-500 flex-shrink-0 ml-3">
                      {formatRelative(report.created_at)}
                    </span>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        )}
      </motion.div>
    </div>
  );
}
