"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useSession } from "next-auth/react";
import type { SSEEvent, AgentStep, AgentName } from "@/types";
import { API_URL } from "@/lib/config";
import { cancelResearch } from "@/lib/api";

const AGENT_STEPS: AgentStep[] = [
  { name: "planner", label: "Planning Research Strategy", status: "idle" },
  { name: "search", label: "Searching Trusted Sources", status: "idle" },
  { name: "validator", label: "Validating Source Quality", status: "idle" },
  { name: "extractor", label: "Extracting Key Findings", status: "idle" },
  { name: "synthesizer", label: "Synthesizing Report", status: "idle" },
];

function freshSteps(): AgentStep[] {
  return AGENT_STEPS.map((s) => ({ ...s }));
}

export function useSSE(reportId: string | null) {
  const { data: session } = useSession();
  const [steps, setSteps] = useState<AgentStep[]>(freshSteps);
  const [isDone, setIsDone] = useState(false);
  const [isError, setIsError] = useState(false);
  const [isCancelled, setIsCancelled] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [currentAgent, setCurrentAgent] = useState<AgentName | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const handleCancel = useCallback(async () => {
    if (!reportId || isCancelling) return;
    setIsCancelling(true);
    try {
      await cancelResearch(reportId);
      // isCancelling stays true — it resets when the "cancelled" SSE event arrives
    } catch {
      // API returns 400 if already finished — safe to ignore
      setIsCancelling(false);
    }
  }, [reportId, isCancelling]);

  useEffect(() => {
    if (!reportId || !session) return;

    // Reset all state for a fresh connection (e.g. navigating to a new research)
    setSteps(freshSteps());
    setIsDone(false);
    setIsError(false);
    setIsCancelled(false);
    setIsCancelling(false);
    setErrorMessage("");
    setCurrentAgent(null);

    const token = (session.user as { access_token?: string })?.access_token;
    const url = `${API_URL}/api/v1/research/${reportId}/stream?token=${token}`;

    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (e) => {
      let event: SSEEvent;
      try {
        event = JSON.parse(e.data);
      } catch {
        return; // malformed event — ignore
      }

      if (event.type === "ping") return;

      if (event.type === "agent_start" && event.agent) {
        setCurrentAgent(event.agent);
        setSteps((prev) =>
          prev.map((s) =>
            s.name === event.agent ? { ...s, status: "running", message: undefined } : s
          )
        );
      }

      if (event.type === "agent_complete" && event.agent) {
        setCurrentAgent(event.agent);
        const next = getNextAgent(event.agent);
        setSteps((prev) =>
          prev.map((s) => {
            if (s.name === event.agent) return { ...s, status: "complete", message: event.message };
            // Mark the next agent running here too as a fallback in case
            // the agent_start event was missed or not emitted by an older backend.
            if (s.name === next && s.status === "idle") return { ...s, status: "running" };
            return s;
          })
        );
      }

      if (event.type === "agent_error" && event.agent) {
        setSteps((prev) =>
          prev.map((s) =>
            s.name === event.agent ? { ...s, status: "error", message: event.message } : s
          )
        );
      }

      if (event.type === "complete") {
        setSteps((prev) =>
          prev.map((s) => ({ ...s, status: s.status === "idle" ? "idle" : "complete" }))
        );
        setIsDone(true);
        es.close();
      }

      if (event.type === "error") {
        setIsError(true);
        setErrorMessage(event.message || "An unexpected error occurred.");
        es.close();
      }

      if (event.type === "cancelled") {
        setSteps((prev) =>
          prev.map((s) =>
            s.status === "running" ? { ...s, status: "error", message: "Cancelled by user" } : s
          )
        );
        setIsCancelled(true);
        setIsCancelling(false);
        es.close();
      }
    };

    es.onerror = () => {
      // Guard: if we already closed the connection on a terminal SSE event
      // (complete / error / cancelled), the EventSource state is CLOSED and
      // this handler should be a no-op to avoid overwriting the real message.
      if (es.readyState === EventSource.CLOSED) return;
      setIsError(true);
      setErrorMessage("Connection to server lost. Please refresh the page.");
      es.close();
    };

    // Optimistically mark the first agent as running while we wait for the
    // agent_start SSE event. If the backend is older and doesn't emit agent_start,
    // this keeps the timeline visually correct from the moment the stream opens.
    setSteps((prev) => prev.map((s, i) => (i === 0 ? { ...s, status: "running" } : s)));

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [reportId, session]);

  return {
    steps,
    isDone,
    isError,
    isCancelled,
    isCancelling,
    errorMessage,
    currentAgent,
    cancel: handleCancel,
  };
}

function getNextAgent(current: AgentName): AgentName | null {
  const order: AgentName[] = ["planner", "search", "validator", "extractor", "synthesizer"];
  const idx = order.indexOf(current);
  return idx >= 0 && idx < order.length - 1 ? order[idx + 1] : null;
}
