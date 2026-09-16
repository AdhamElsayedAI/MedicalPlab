"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  ArrowRight,
  HelpCircle,
  AlertCircle,
  Lock,
  Award,
} from "lucide-react";
import type { TransferItemDTO, TransferSubmissionResponse } from "../../lib/types";

interface MobileTransferViewProps {
  transferItem: TransferItemDTO;
  sessionId: string;
  isSubmitting: boolean;
  onSubmitTransfer: (selectedOption: string, wasAssisted: boolean) => Promise<TransferSubmissionResponse>;
  onViewMastery: () => void;
  onExit: () => void;
}

export const MobileTransferView: React.FC<MobileTransferViewProps> = ({
  transferItem,
  sessionId,
  isSubmitting,
  onSubmitTransfer,
  onViewMastery,
  onExit,
}) => {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [wasAssisted, setWasAssisted] = useState(false);
  const [result, setResult] = useState<TransferSubmissionResponse | null>(null);
  const [errorText, setErrorText] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!selectedOption || isSubmitting || result) return;
    setErrorText(null);
    try {
      const res = await onSubmitTransfer(selectedOption, wasAssisted);
      setResult(res);
    } catch (err: any) {
      setErrorText(err.message || "Failed to score transfer assessment");
    }
  };

  const isConfirmed = result?.outcome === "TRANSFER_CONFIRMED";
  const isAnswered = result !== null;

  return (
    <div className="space-y-4">
      {/* Assessment Header */}
      <div className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 border border-indigo-500/30 p-4 sm:p-5 shadow-xl relative overflow-hidden">
        <div className="flex items-center justify-between text-xs mb-3 border-b border-slate-800/80 pb-2.5">
          <span className="flex items-center gap-1.5 font-semibold text-indigo-400">
            <Lock className="w-3.5 h-3.5" />
            Independent Transfer Assessment
          </span>
          <span className="font-mono bg-indigo-500/10 text-indigo-300 px-2 py-0.5 rounded-full text-[10px] border border-indigo-500/20">
            {transferItem.question_id}
          </span>
        </div>

        <p className="text-[11px] text-slate-400 mb-3 leading-relaxed">
          This held-out question tests the core mechanism in a new context. To confirm transfer, answer independently without assistance.
        </p>

        <h2 className="text-base sm:text-lg font-medium text-slate-100 leading-snug">
          {transferItem.stem}
        </h2>
      </div>

      {/* Options List */}
      <div className="space-y-2.5">
        {Object.entries(transferItem.options).map(([key, text]) => {
          const isChosen = selectedOption === key;

          let cardStyle = "bg-slate-900/60 border-slate-800/80 text-slate-300 hover:border-slate-700";
          if (isChosen && !isAnswered) {
            cardStyle = "bg-indigo-950/40 border-indigo-500 text-indigo-100 ring-1 ring-indigo-500/50";
          } else if (isAnswered) {
            if (isChosen) {
              cardStyle = isConfirmed
                ? "bg-emerald-950/40 border-emerald-500 text-emerald-100 ring-1 ring-emerald-500/30"
                : "bg-rose-950/40 border-rose-500 text-rose-100 ring-1 ring-rose-500/30";
            } else {
              cardStyle = "bg-slate-900/30 border-slate-800/40 text-slate-500 opacity-60";
            }
          }

          return (
            <button
              key={key}
              type="button"
              disabled={isAnswered || isSubmitting}
              onClick={() => setSelectedOption(key)}
              className={`w-full text-left p-3.5 sm:p-4 rounded-xl border transition-all duration-150 flex items-start gap-3 active:scale-[0.99] ${cardStyle}`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center font-semibold text-xs shrink-0 ${
                  isChosen
                    ? isAnswered
                      ? isConfirmed
                        ? "bg-emerald-500 text-slate-950"
                        : "bg-rose-500 text-white"
                      : "bg-indigo-500 text-white"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {key}
              </div>
              <div className="text-sm font-normal pt-0.5 leading-relaxed">{text}</div>
            </button>
          );
        })}
      </div>

      {/* Assistance checkbox */}
      {!isAnswered && (
        <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={wasAssisted}
              onChange={(e) => setWasAssisted(e.target.checked)}
              className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-slate-950"
            />
            <span>I received external assistance on this question</span>
          </label>
          <span className="text-[10px] text-slate-500 font-mono">
            {wasAssisted ? "(Disqualifies transfer)" : "(Independent)"}
          </span>
        </div>
      )}

      {errorText && (
        <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs">
          {errorText}
        </div>
      )}

      {/* Submit or Result */}
      {!isAnswered ? (
        <button
          type="button"
          disabled={!selectedOption || isSubmitting}
          onClick={handleSubmit}
          className={`w-full py-3.5 px-4 rounded-xl font-semibold text-sm transition-all shadow-md flex items-center justify-center gap-2 ${
            selectedOption && !isSubmitting
              ? "bg-indigo-500 hover:bg-indigo-400 active:bg-indigo-600 text-white shadow-indigo-500/20"
              : "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-850"
          }`}
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Scoring transfer assessment…</span>
            </>
          ) : (
            <span>Submit Transfer Assessment</span>
          )}
        </button>
      ) : (
        /* Scored Outcome Card */
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 sm:p-5 space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="flex items-center gap-3">
            {isConfirmed ? (
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/30">
                <Award className="w-6 h-6" />
              </div>
            ) : (
              <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 border border-amber-500/30">
                <AlertCircle className="w-6 h-6" />
              </div>
            )}
            <div>
              <div
                className={`font-semibold text-sm sm:text-base ${
                  isConfirmed ? "text-emerald-400" : "text-amber-400"
                }`}
              >
                {isConfirmed ? "Transfer Confirmed!" : "Transfer Not Confirmed"}
              </div>
              <div className="text-xs text-slate-400">
                Outcome: <strong className="text-slate-200">{result.outcome}</strong>
              </div>
            </div>
          </div>

          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed bg-slate-950/50 p-3.5 rounded-xl border border-slate-800">
            {result.explanation}
          </p>

          <div className="pt-2 flex flex-col sm:flex-row gap-2.5">
            <button
              type="button"
              onClick={onViewMastery}
              className="w-full py-3 px-4 rounded-xl bg-sky-600 hover:bg-sky-500 active:bg-sky-700 text-white font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg shadow-sky-600/20 transition-all"
            >
              <span>View Updated Learning State</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={onExit}
              className="w-full py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs sm:text-sm transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
