import React, { useState, useEffect } from "react";

interface ScanConfirmationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title?: string;
}

export default function ScanConfirmationModal({
    isOpen,
    onClose,
    onConfirm,
    title = "Authorization Required"
}: ScanConfirmationModalProps) {
    const [isConfirmed, setIsConfirmed] = useState(false);

    // Reset state when modal opens
    useEffect(() => {
        if (isOpen) {
            setIsConfirmed(false);
        }
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 transition-all">
            <div className="bg-white/90 backdrop-blur-xl border border-white/50 rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in duration-300 ring-1 ring-black/5">

                {/* Glossy Header */}
                <div className="bg-gradient-to-r from-red-50/80 to-red-100/50 px-6 py-5 border-b border-red-100/50 flex items-center gap-3 relative overflow-hidden">
                    <div className="absolute inset-0 bg-white/20 backdrop-blur-md"></div>
                    <div className="relative z-10 flex items-center gap-3">
                        <div className="p-2 bg-red-100/50 rounded-full shadow-inner">
                            <svg className="w-6 h-6 text-red-600 drop-shadow-sm" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                            </svg>
                        </div>
                        <h3 className="text-xl font-bold text-slate-800 tracking-tight drop-shadow-sm">{title}</h3>
                    </div>
                </div>

                <div className="p-8 space-y-6">
                    <p className="text-slate-600 leading-relaxed text-base">
                        You are about to initiate a security scan. This action may generate significant network traffic and could potentially impact the target server's performance.
                    </p>

                    <div className="bg-slate-50/80 border border-slate-200/60 rounded-xl p-5 shadow-sm relative overflow-hidden group">
                        <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent pointer-events-none"></div>
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Legal Disclaimer</h4>
                        <div className="space-y-2 text-sm text-slate-600">
                            <p>
                                Unauthorized scanning of networks or systems is <span className="font-semibold text-red-600">illegal</span> and can lead to severe legal consequences.
                            </p>
                            <p>
                                By proceeding, you acknowledge that you are fully authorized to scan the target URL and accept complete responsibility for any actions taken by this tool.
                            </p>
                        </div>
                    </div>

                    <div
                        className={`flex items-start gap-3 p-4 border rounded-xl cursor-pointer transition-all duration-200 group ${isConfirmed
                                ? 'bg-red-50/80 border-red-200 shadow-sm'
                                : 'bg-white/50 border-slate-200 hover:bg-slate-50 hover:border-slate-300'
                            }`}
                        onClick={() => setIsConfirmed(!isConfirmed)}
                    >
                        <div className="flex-shrink-0 mt-0.5">
                            <input
                                type="checkbox"
                                id="confirmation_agree"
                                checked={isConfirmed}
                                onChange={(e) => setIsConfirmed(e.target.checked)}
                                className="h-5 w-5 text-red-600 rounded border-gray-300 focus:ring-red-500 cursor-pointer shadow-sm transition-transform group-active:scale-95"
                                onClick={(e) => e.stopPropagation()}
                            />
                        </div>
                        <label htmlFor="confirmation_agree" className="text-sm font-medium text-slate-700 cursor-pointer select-none leading-snug">
                            I confirm that I have explicit permission to scan this target and I accept full responsibility for all consequences of this scan.
                        </label>
                    </div>
                </div>

                <div className="px-6 py-5 bg-gray-50/50 backdrop-blur-sm flex justify-end gap-3 border-t border-gray-100">
                    <button
                        onClick={onClose}
                        className="px-5 py-2.5 text-slate-600 bg-white border border-slate-200/80 rounded-lg hover:bg-slate-50 hover:text-slate-800 transition-all shadow-sm hover:shadow-md font-medium text-sm"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={!isConfirmed}
                        className="px-5 py-2.5 bg-gradient-to-r from-red-600 to-red-500 text-white rounded-lg hover:from-red-500 hover:to-red-400 disabled:from-slate-300 disabled:to-slate-300 disabled:opacity-70 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-red-500/30 font-medium text-sm flex items-center gap-2 transform active:scale-95"
                    >
                        <span>Confirm & Start Scan</span>
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
}
