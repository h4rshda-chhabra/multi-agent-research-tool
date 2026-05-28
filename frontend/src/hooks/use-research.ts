"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  startResearch,
  getReport,
  listReports,
  deleteReport,
  listSaved,
  saveReport,
  unsaveReport,
  exportReport,
} from "@/lib/api";

export function useStartResearch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (topic: string) => startResearch(topic),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reports"] }),
    onError: () => toast.error("Failed to start research"),
  });
}

export function useReport(reportId: string | null) {
  return useQuery({
    queryKey: ["report", reportId],
    queryFn: () => getReport(reportId!),
    enabled: !!reportId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "pending" ? 5000 : false;
    },
  });
}

export function useReports() {
  return useQuery({
    queryKey: ["reports"],
    queryFn: listReports,
  });
}

export function useDeleteReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteReport,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      toast.success("Report deleted");
    },
    onError: () => toast.error("Failed to delete report"),
  });
}

export function useSavedReports() {
  return useQuery({
    queryKey: ["saved-reports"],
    queryFn: listSaved,
  });
}

export function useSaveReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: saveReport,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      qc.invalidateQueries({ queryKey: ["saved-reports"] });
      toast.success("Report saved");
    },
    onError: () => toast.error("Failed to save report"),
  });
}

export function useUnsaveReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: unsaveReport,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      qc.invalidateQueries({ queryKey: ["saved-reports"] });
      toast.success("Removed from saved");
    },
  });
}

export function useExportReport() {
  return useMutation({
    mutationFn: ({ reportId, format }: { reportId: string; format: "pdf" | "markdown" }) =>
      exportReport(reportId, format),
    onSuccess: (blob, { format, reportId }) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report-${reportId.slice(0, 8)}.${format === "pdf" ? "pdf" : "md"}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`Downloaded as ${format.toUpperCase()}`);
    },
    onError: () => toast.error("Export failed"),
  });
}
