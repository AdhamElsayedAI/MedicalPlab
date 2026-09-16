"use client";

import React, { useEffect, useState } from "react";
import { AlertCircle, ArrowRight, RotateCcw, X, Sparkles } from "lucide-react";
import { mobileApi } from "./MobileApiClient";
import type { RemediationSessionResponse } from "../../lib/types";

interface MobileResumeBannerProps {
  onResume: (session: RemediationSessionResponse) => void;
  onDismiss?: () => void;
}

export const MobileResumeBanner: React.FC<MobileResumeBannerProps> = ({
  onResume,
  onDismiss,
}) => {
  const [activeSession, setActiveSession] = useState<RemediationSessionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const sessionId = mobileApi.getActiveSessionId();
    if (!sessionId || dismissed) {
      setActiveSession(null);
      return;
    }

    let isMounted = true;
    const checkActiveSession = async () => {
      try {
        setIsLoading(true);
        const session = await mobileApi.getRemediationSession(sessionId);
        if (isMounted) {
          // If session is still in progress or awaiting transfer, prompt resume
          if (
            session &&
            (session.lifecycle_state === "CREATED" ||
              session.lifecycle_state === "REMEDIATING" ||
              session.lifecycle_state === "AWAITING_TRANSFER")
          ) {
            setActiveSession(session);
          } else {
            // Already completed or closed
            mobileApi.setActiveSessionId(null);
            setActiveSession(null);
          }
        }
      } catch (err: any) {
        // Safe Resume: If 403 (ownership mismatch) or 404 (stale/not found), clear pointer safely without workaround
        if (err?.status === 404 || err?.status === 403) {
          mobileApi.setActiveSessionId(null);
        }
        if (isMounted) setActiveSession(null);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    checkActiveSession();

    return () => {
      isMounted = false;
    };
  }, [dismissed]);

  if (!activeSession || dismissed) {
    return null;
  }

  const handleDismiss = () => {
    setDismissed(true);
    if (onDismiss) onDismiss();
  };

  const handleAbandon = async () => {
    if (activeSession.session_id) {
      try {
        await mobileApi.abandonRemediation(activeSession.session_id);
      } catch (err) {
        // Silent catch
      }
      mobileApi.setActiveSessionId(null);
      setActiveSession(null);
      if (onDismiss) onDismiss();
    }
  };

  const isAwaitingTransfer = activeSession.lifecycle_state === "AWAITING_TRANSFER";

  return (
    <div className="bg-gradient-to-r from-sky-950/90 via-slate-900/90 to-indigo-950/90 border border-sky-500/40 rounded-xl p-3 shadow-lg backdrop-blur-md transition-all animate-in fade-in slide-in-from-top-2 duration-200">
      <div className="flex items-start justify-between gap-2.5">
        <div className="flex items-start gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-sky-500/20 border border-sky-500/30 flex items-center justify-center text-sky-400 shrink-0 mt-0.5">
            <RotateCcw className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-100">
                In-Progress Remediation
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                {isAwaitingTransfer ? "Transfer Ready" : `Turn ${activeSession.turn_number} / 3`}
              </span>
            </div>
            <p className="text-[11px] text-slate-300 mt-0.5 leading-snug">
              {isAwaitingTransfer
                ? "Socratic turns finished. Ready for held-out transfer assessment."
                : "You have an active Socratic dialogue session ready to resume."}
            </p>
          </div>
        </div>

        <button
          onClick={handleDismiss}
          className="text-slate-400 hover:text-slate-200 p-1 rounded-md transition-colors"
          title="Dismiss banner"
          type="button"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="mt-2.5 flex items-center justify-end gap-2 pt-2 border-t border-slate-800/80">
        <button
          type="button"
          onClick={handleAbandon}
          className="text-[11px] px-2.5 py-1 text-slate-400 hover:text-rose-400 transition-colors"
        >
          Abandon
        </button>
        <button
          type="button"
          onClick={() => onResume(activeSession)}
          className="text-[11px] font-semibold px-3 py-1 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 flex items-center gap-1 shadow transition-all active:scale-95"
        >
          <span>Resume Session</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
};
