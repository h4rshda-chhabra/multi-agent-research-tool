"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Bookmark, Loader2, BookOpen } from "lucide-react";
import { useSavedReports, useUnsaveReport } from "@/hooks/use-research";
import { formatRelative, truncate } from "@/lib/utils";

export default function SavedPage() {
  const { data: reports = [], isLoading } = useSavedReports();
  const { mutate: unsave } = useUnsaveReport();

  return (
    <div className="px-6 py-8 max-w-4xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="text-2xl font-bold text-white">Saved Reports</h1>
        <p className="text-slate-400 mt-1">{reports.length} saved</p>
      </motion.div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
        </div>
      ) : reports.length === 0 ? (
        <div className="glass rounded-xl p-12 text-center">
          <Bookmark className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">No saved reports yet.</p>
          <p className="text-slate-500 text-sm mt-1">Bookmark reports from the report viewer to find them here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((report, i) => (
            <motion.div
              key={report.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="glass rounded-xl p-4 flex items-center justify-between gap-3 group"
            >
              <Link href={`/research/${report.id}`} className="flex items-center gap-3 min-w-0 flex-1">
                <BookOpen className="w-4 h-4 text-brand-400 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm text-slate-200 group-hover:text-white transition truncate">
                    {truncate(report.topic, 70)}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">{formatRelative(report.created_at)}</p>
                </div>
              </Link>
              <button
                onClick={() => unsave(report.id)}
                className="opacity-0 group-hover:opacity-100 p-1.5 text-brand-400 hover:text-slate-400 transition rounded-lg hover:bg-slate-700"
              >
                <Bookmark className="w-4 h-4 fill-current" />
              </button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
