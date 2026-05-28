"use client";

import { useEffect, useRef, useState } from "react";
import { useSession } from "next-auth/react";
import type { SSEEvent, AgentStep, AgentName } from "@/types";
import { API_URL } from "@/lib/config";

const AGENT_STEPS: AgentStep[] = [
  { name: "planner", label: "Planning Research Strategy", status: "idle" },
  { name: "search", label: "Searching Trusted Sources", status: "idle" },
  { name: "validator", label: "Validating Source Quality", status: "idle" },
  { name: "extractor", label: "Extracting Key Findings", status: "idle" },
  { name: "synthesizer", label: "Synthesizing Report", status: "idle" },
];

export function useSSE(reportId: string | null) {
  const { data: session } = useSession();
  const [steps, setSteps] = useState<AgentStep[]>(AGENT_STEPS.map((s) => ({ ...s })));
  const [isDone, setIsDone] = useState(false);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [currentAgent, setCurrentAgent] = useState<AgentName | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!reportId || !session) return;

    const token = (session.user as { access_token?: string })?.access_token;
    const apiUrl = API_URL;
    const url = `${apiUrl}/api/v1/research/${reportId}/stream?token=${token}`;

    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const event: SSEEvent = JSON.parse(e.data);

        if (event.type === "ping") return;

        if (event.type === "agent_complete" && event.agent) {
          setCurrentAgent(event.agent);
          setSteps((prev) =>
            prev.map((s) =>
              s.name === event.agent
                ? { ...s, status: "complete", message: event.message }
                : s.name === getNextAgent(event.agent!)
                ? { ...s, status: "running" }
                : s
            )
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
          setSteps((prev) => prev.map((s) => ({ ...s, status: s.status === "idle" ? "idle" : "complete" })));
          setIsDone(true);
          es.close();
        }

        if (event.type === "error") {
          setIsError(true);
          setErrorMessage(event.message);
          es.close();
        }
      } catch {
        // malformed event — ignore
      }
    };

    es.onerror = () => {
      setIsError(true);
      setErrorMessage("Connection lost");
      es.close();
    };

    // Mark first agent as running immediately
    setSteps((prev) => prev.map((s, i) => (i === 0 ? { ...s, status: "running" } : s)));

    return () => es.close();
  }, [reportId, session]);

  return { steps, isDone, isError, errorMessage, currentAgent };
}

function getNextAgent(current: AgentName): AgentName | null {
  const order: AgentName[] = ["planner", "search", "validator", "extractor", "synthesizer"];
  const idx = order.indexOf(current);
  return idx < order.length - 1 ? order[idx + 1] : null;
}
