import axios from "axios";
import { getSession } from "next-auth/react";
import type { AuthToken, Report, ReportListItem } from "@/types";
import { API_URL } from "./config";

declare module "axios" {
  export interface AxiosRequestConfig {
    retry?: number;
    retryDelay?: number;
    __retryCount?: number;
  }
}

const BASE = API_URL;

export const apiClient = axios.create({ baseURL: `${BASE}/api/v1` });

apiClient.defaults.retry = 3;
apiClient.defaults.retryDelay = 1000;

apiClient.interceptors.request.use(async (config) => {
  // Skip calling getSession() for public auth endpoints to prevent deadlocks during authorize callback
  if (config.url?.includes("/auth/login") || config.url?.includes("/auth/register")) {
    return config;
  }

  const session = await getSession();
  const token = (session?.user as { access_token?: string } | undefined)?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    if (!config || !config.retry) {
      return Promise.reject(error);
    }

    config.__retryCount = config.__retryCount || 0;

    if (config.__retryCount >= config.retry) {
      const port = new URL(BASE).port || "8000";
      
      if (error.code === "ERR_NETWORK" || !error.response) {
        return Promise.reject(new Error(`Backend server is not running on port ${port}`));
      }

      if (error.response) {
        const status = error.response.status;
        const detail = error.response.data?.detail || error.response.data?.message;
        if (status === 400) {
          return Promise.reject(new Error(detail || "Bad Request"));
        }
        if (status === 401) {
          return Promise.reject(new Error("Unauthorized: Please sign in again."));
        }
        if (status === 403) {
          return Promise.reject(new Error("Forbidden: You do not have access to this resource."));
        }
        if (status === 404) {
          return Promise.reject(new Error("Resource not found."));
        }
        if (status >= 500) {
          return Promise.reject(new Error(`Backend Error (${status}): ${detail || "Internal Server Error"}`));
        }
      }
      return Promise.reject(error);
    }

    config.__retryCount += 1;

    const backoff = new Promise((resolve) => {
      setTimeout(() => resolve(null), config.retryDelay || 1000);
    });

    await backoff;
    return apiClient(config);
  }
);

// ─── Auth ────────────────────────────────────────────────────────────────────

export async function loginApi(email: string, password: string): Promise<AuthToken> {
  const { data } = await apiClient.post<AuthToken>("/auth/login", { email, password });
  return data;
}

export async function registerApi(name: string, email: string, password: string): Promise<AuthToken> {
  const { data } = await apiClient.post<AuthToken>("/auth/register", { name, email, password });
  return data;
}

// ─── Research ────────────────────────────────────────────────────────────────

export async function startResearch(topic: string): Promise<{ report_id: string; status: string }> {
  const { data } = await apiClient.post("/research", { topic });
  return data;
}

export async function getReport(reportId: string): Promise<Report> {
  const { data } = await apiClient.get<Report>(`/research/${reportId}`);
  return data;
}

// ─── Reports ─────────────────────────────────────────────────────────────────

export async function listReports(): Promise<ReportListItem[]> {
  const { data } = await apiClient.get<ReportListItem[]>("/reports");
  return data;
}

export async function deleteReport(reportId: string): Promise<void> {
  await apiClient.delete(`/reports/${reportId}`);
}

export async function listSaved(): Promise<ReportListItem[]> {
  const { data } = await apiClient.get<ReportListItem[]>("/reports/saved");
  return data;
}

export async function saveReport(reportId: string): Promise<void> {
  await apiClient.post("/reports/save", { report_id: reportId });
}

export async function unsaveReport(reportId: string): Promise<void> {
  await apiClient.delete(`/reports/save/${reportId}`);
}

// ─── Export ──────────────────────────────────────────────────────────────────

export function exportUrl(reportId: string, format: "pdf" | "markdown"): string {
  return `${BASE}/api/v1/export?report_id=${reportId}&format=${format}`;
}

export async function exportReport(reportId: string, format: "pdf" | "markdown"): Promise<Blob> {
  const { data } = await apiClient.post<Blob>(
    "/export",
    { report_id: reportId, format },
    { responseType: "blob" }
  );
  return data;
}
