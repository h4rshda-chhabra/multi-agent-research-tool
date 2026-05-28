"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { WifiOff, AlertTriangle, RefreshCw } from "lucide-react";
import axios from "axios";
import { API_URL } from "@/lib/config";

interface BackendHealthContextType {
  isHealthy: boolean | null;
  checkHealth: () => Promise<boolean>;
}

const BackendHealthContext = createContext<BackendHealthContextType>({
  isHealthy: null,
  checkHealth: async () => false,
});

export const useBackendHealth = () => useContext(BackendHealthContext);

export function BackendHealthProvider({ children }: { children: React.ReactNode }) {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  // Extract port dynamically from API_URL to satisfy "Prevent hardcoded localhost ports across files"
  const getPort = useCallback(() => {
    try {
      const url = new URL(API_URL);
      return url.port || "8000";
    } catch {
      return "8000";
    }
  }, []);

  const checkHealth = useCallback(async (): Promise<boolean> => {
    const healthUrl = `${API_URL}/health`;
    
    // Attempt health pings with retry mechanism for temporary failures
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const response = await axios.get(healthUrl, { timeout: 2000 });
        if (response.data && response.data.status === "ok") {
          setIsHealthy(true);
          return true;
        }
      } catch (err) {
        // Only on the final attempt do we confirm it is down
        if (attempt === 3) {
          setIsHealthy(false);
          return false;
        }
        // Delay slightly before retrying
        await new Promise((r) => setTimeout(r, 1000));
      }
    }
    setIsHealthy(false);
    return false;
  }, []);

  const handleManualRetry = async () => {
    setIsRetrying(true);
    await checkHealth();
    // Keep spin active slightly for visual satisfaction
    setTimeout(() => setIsRetrying(false), 800);
  };

  useEffect(() => {
    // Initial startup check
    checkHealth();

    // Periodic check every 10 seconds
    const interval = setInterval(() => {
      checkHealth();
    }, 10000);

    return () => clearInterval(interval);
  }, [checkHealth]);

  const port = getPort();

  return (
    <BackendHealthContext.Provider value={{ isHealthy, checkHealth }}>
      {children}
      <AnimatePresence>
        {isHealthy === false && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="fixed top-4 left-1/2 -translate-x-1/2 z-[9999] w-[90%] max-w-lg"
          >
            <div className="relative overflow-hidden rounded-xl border border-red-500/20 bg-slate-950/80 backdrop-blur-md px-4 py-3.5 shadow-2xl shadow-red-950/20">
              {/* Pulsing glow background decoration */}
              <div className="absolute -left-10 -top-10 h-32 w-32 rounded-full bg-red-600/10 blur-2xl pointer-events-none" />
              
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-red-500/10 text-red-500">
                    <WifiOff className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-100 text-sm leading-tight flex items-center gap-1.5">
                      Service Unreachable
                      <span className="flex h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                    </h4>
                    <p className="mt-0.5 text-xs text-red-400 font-medium">
                      Backend server is not running on port {port}
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleManualRetry}
                  disabled={isRetrying}
                  className="flex items-center gap-1.5 shrink-0 rounded-lg bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 active:bg-red-500/30 px-3 py-1.5 text-xs font-semibold text-red-400 hover:text-red-300 transition-all disabled:opacity-50"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${isRetrying ? "animate-spin" : ""}`} />
                  Retry
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </BackendHealthContext.Provider>
  );
}
