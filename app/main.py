"use client";

import { Award, Download, Lock, ShieldCheck, ExternalLink, Linkedin } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";

interface CertificateProps {
  isLocked: boolean;
  userName: string;
  certHash?: string;
  courseName?: string;
}

export function CertificateCard({ 
  isLocked, 
  userName, 
  certHash = "BP-VERIFY-2026",
  courseName = "Technical Portfolio Simulation" 
}: CertificateProps) {
  
  const verificationUrl = `https://bluepeak.com/verify/${certHash}`;

  return (
    <div className={`mt-12 transition-all relative rounded-[2.5rem] printable-certificate ${
      isLocked 
      ? "bg-slate-50 border-2 border-dashed border-slate-200 p-12 text-center" 
      : "bg-white border-[16px] border-slate-100 shadow-2xl p-1"
    }`}>
      
      {isLocked ? (
        /* LOCKED STATE UI */
        <div className="flex flex-col items-center justify-center py-10">
          <div className="w-16 h-16 bg-slate-200 rounded-full flex items-center justify-center mb-6 text-slate-400">
            <Lock size={32} />
          </div>
          <h3 className="text-xl font-black text-slate-400 uppercase tracking-widest">Credential Locked</h3>
        </div>
      ) : (
        /* PROFESSIONAL CERTIFICATE */
        <div className="border-[1px] border-slate-200 rounded-[2rem] p-10 md:p-16 relative bg-white overflow-hidden w-full max-w-[1100px] h-[750px] flex flex-col justify-between mx-auto">
          
          <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] pointer-events-none">
            <ShieldCheck size={500} />
          </div>

          <div className="relative z-10 h-full flex flex-col justify-between">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-indigo-600 rounded-2xl flex items-center justify-center text-white shadow-xl">
                  <ShieldCheck size={32} />
                </div>
                <div>
                  <h4 className="font-black text-slate-900 text-2xl tracking-tighter italic">BluePeak.</h4>
                  <p className="text-[10px] text-indigo-600 font-black uppercase tracking-[0.2em]">Official Verification</p>
                </div>
              </div>

              <div className="no-print">
                <button 
                  onClick={() => window.print()}
                  className="px-6 py-3 bg-slate-900 text-white rounded-xl font-bold text-xs hover:bg-indigo-600 transition-all shadow-md"
                >
                  <Download size={16} className="inline mr-2" /> Download PDF
                </button>
              </div>
            </div>

            {/* Body content */}
            <div className="text-center md:text-left">
              <h2 className="text-sm uppercase tracking-[0.5em] text-slate-400 font-black mb-10">Certificate of Completion</h2>
              <p className="text-slate-500 font-medium text-xl italic mb-4">This is to officially certify that</p> [cite: 3, 16, 28, 42]
              <h1 className="text-6xl font-black text-slate-900 tracking-tight capitalize border-b-8 border-indigo-50 inline-block pb-4 mb-8">
                {userName}
              </h1> [cite: 4, 16, 29, 42]
              <p className="text-slate-600 font-medium text-xl leading-relaxed max-w-2xl">
                Has successfully demonstrated technical proficiency in the <span className="text-indigo-600 font-black">{courseName}</span> by completing all performance audits and implementation milestones.
              </p> [cite: 5, 17, 30, 43]
            </div>

            {/* Footer */}
            <div className="mt-8 pt-8 border-t border-slate-100 flex justify-between items-end">
              <div className="space-y-4">
                <div>
                  <p className="text-[10px] uppercase font-black text-slate-300 tracking-widest mb-1">Credential ID</p> [cite: 7, 19, 32, 44]
                  <p className="text-sm font-mono font-bold text-slate-700">{certHash}</p> [cite: 8, 20, 33, 45]
                </div>
                <div>
                  <p className="text-[10px] uppercase font-black text-slate-300 tracking-widest mb-1">Date Issued</p> [cite: 9, 21, 34, 46]
                  <p className="text-sm font-mono font-bold text-slate-700">Jan 14, 2026</p> [cite: 10, 22, 35, 47]
                </div>
                <div className="text-xs font-mono text-indigo-600 font-bold">Verified at bluepeak.com/verify</div> [cite: 11, 23, 36, 48]
              </div>

              {/* Seal */}
              <div className="flex items-center gap-8">
                <div className="relative w-36 h-36 flex items-center justify-center">
                  <div className="absolute inset-0 bg-amber-100 rounded-full opacity-40"></div>
                  <div className="absolute inset-2 border-2 border-dashed border-amber-400 rounded-full"></div>
                  <div className="relative z-10 flex flex-col items-center text-amber-600">
                    <Award size={48} fill="currentColor" />
                    <span className="text-[10px] font-black uppercase tracking-tighter text-amber-700">OFFICIAL VERIFIED</span> 
                  </div>
                  <div className="absolute -bottom-2 bg-amber-500 h-12 w-5 left-12 rounded-b-sm"></div>
                  <div className="absolute -bottom-2 bg-amber-600 h-10 w-5 left-18 rounded-b-sm"></div>
                </div>
                <div className="p-2 bg-white rounded-xl shadow-lg border border-slate-100 flex flex-col items-center">
                  <QRCodeSVG value={verificationUrl} size={80} />
                  <p className="text-[8px] mt-2 font-black uppercase text-slate-400">SCAN TO VERIFY</p> [cite: 14, 26, 40]
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
