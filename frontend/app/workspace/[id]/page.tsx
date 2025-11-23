"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  ArrowLeft, 
  ArrowRight, 
  ChevronRight, 
  Box, 
  Maximize2,
  PlayCircle,
  FileText,
  Volume2
} from 'lucide-react';
import AssemblyScene from '@/components/AssemblyScene';

// Mock Data
const MANUAL_DATA = {
  productName: "SANDSBERG Table",
  steps: [
    { stepNumber: 1, title: "Prepare Workspace", description: "Place the table frame upside down on a soft surface.", voiceGuidance: "Start by placing the table top upside down on a rug or carpet to prevent scratches.", pdfPage: 1 },
    { stepNumber: 2, title: "Insert Brackets", description: "Push the plastic corner brackets into the metal frame.", voiceGuidance: "Take the four plastic corner brackets and push them into the frame slots until they click.", pdfPage: 2 },
    { stepNumber: 3, title: "Secure Frame", description: "Align frame and tighten screws.", voiceGuidance: "Use the provided Allen key to firmly secure the frame using the ten medium-sized screws.", pdfPage: 3 },
    { stepNumber: 4, title: "Attach Legs", description: "Screw in the legs.", voiceGuidance: "Finally, screw the legs into the brackets. Hand tighten them first, then give them a final turn.", pdfPage: 4 },
  ]
};

export default function Workspace() {
  const [currentStep, setCurrentStep] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const totalSteps = MANUAL_DATA.steps.length;
  const activeStepData = MANUAL_DATA.steps[currentStep - 1];

  // Simulate Voice Playing (Duration logic)
  useEffect(() => {
    setIsPlaying(true);
    // Simulate length of audio (e.g., 4 seconds)
    const timer = setTimeout(() => setIsPlaying(false), 4000);
    return () => clearTimeout(timer);
  }, [currentStep]);

  return (
    <div className="h-screen w-full flex flex-col bg-zinc-900 font-sans text-white overflow-hidden">
      
      {/* 1. HEADER */}
      <header className="h-14 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between px-4 shrink-0 z-20">
        <div className="flex items-center gap-3">
          <Link href="/" className="p-2 hover:bg-zinc-800 rounded-lg transition-colors text-zinc-400 hover:text-white">
            <Box className="w-5 h-5" />
          </Link>
          <div className="h-4 w-[1px] bg-zinc-700 mx-1" />
          <nav className="flex items-center gap-2 text-sm">
            <span className="text-zinc-400">Dashboard</span>
            <ChevronRight className="w-4 h-4 text-zinc-600" />
            <span className="font-semibold text-zinc-100">{MANUAL_DATA.productName}</span>
          </nav>
        </div>
      </header>

      {/* 2. MAIN SPLIT VIEW */}
      <div className="flex-1 flex flex-row overflow-hidden">
        
        {/* LEFT PANEL: PDF VIEWER (50%) */}
        <div className="w-1/2 bg-zinc-800 border-r border-zinc-700 relative flex flex-col">
           {/* PDF Toolbar */}
           <div className="h-12 border-b border-zinc-700 flex items-center justify-between px-4 bg-zinc-800/50 backdrop-blur">
              <span className="text-xs font-medium text-zinc-400 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Original Manual.pdf
              </span>
              <span className="text-xs bg-black/30 px-2 py-1 rounded text-zinc-300">
                Page {activeStepData.pdfPage} / 12
              </span>
           </div>

           {/* PDF Content Area (Placeholder) */}
           <div className="flex-1 flex items-center justify-center bg-zinc-500/10 p-8 overflow-hidden">
              <div className="w-full h-full bg-white shadow-2xl rounded-sm flex items-center justify-center relative group">
                 {/* Simulate PDF Page Content */}
                 <div className="text-center opacity-30 group-hover:opacity-40 transition-opacity">
                    <FileText className="w-24 h-24 mx-auto text-zinc-900 mb-4" />
                    <p className="text-zinc-900 font-serif text-xl">PDF Page {activeStepData.pdfPage}</p>
                    <p className="text-zinc-600 text-sm mt-2">Diagrams and warnings would appear here.</p>
                 </div>
                 
                 {/* Highlight Box (Simulating AI detection on PDF) */}
                 <div className="absolute top-1/4 left-1/4 w-1/2 h-1/2 border-4 border-indigo-500/30 bg-indigo-500/5 rounded animate-pulse" />
              </div>
           </div>
        </div>


        {/* RIGHT PANEL: 3D SCENE + SUBTITLES (50%) */}
        <div className="w-1/2 bg-black relative">
          
          {/* The 3D Canvas */}
          <div className="absolute inset-0">
            <AssemblyScene currentStep={currentStep} />
          </div>

          {/* --- OVERLAY: SUBTITLES (Only shows when isPlaying is true) --- */}
          {isPlaying && (
            <div className="absolute bottom-32 left-8 right-8 z-20 flex justify-center pointer-events-none">
               <div className="bg-black/70 backdrop-blur-md border border-white/10 p-6 rounded-2xl shadow-2xl max-w-xl animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="flex items-center gap-3 mb-2">
                     <Volume2 className="w-4 h-4 text-indigo-400 animate-pulse" />
                     <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider">Voice Guide</span>
                  </div>
                  <p className="text-lg font-medium text-white leading-relaxed text-center">
                    "{activeStepData.voiceGuidance}"
                  </p>
               </div>
            </div>
          )}

          {/* FLOATING CONTROLS */}
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-zinc-900/90 backdrop-blur-md p-2 rounded-2xl shadow-2xl border border-white/10 z-30">
             <button 
               onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
               disabled={currentStep === 1}
               className="p-3 rounded-xl hover:bg-zinc-800 disabled:opacity-30 transition-all text-zinc-200"
             >
               <ArrowLeft className="w-6 h-6" />
             </button>

             <div className="h-8 w-[1px] bg-white/10 mx-2"></div>

             <div className="flex flex-col items-center px-2">
               <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Step</span>
               <span className="text-xl font-bold text-white tabular-nums leading-none">{currentStep}</span>
             </div>

             <div className="h-8 w-[1px] bg-white/10 mx-2"></div>

             <button 
               onClick={() => setCurrentStep(Math.min(totalSteps, currentStep + 1))}
               disabled={currentStep === totalSteps}
               className="group p-3 rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-30 transition-all shadow-lg shadow-indigo-900/20"
             >
               <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
             </button>
          </div>

          {/* Top Right Tools */}
          <div className="absolute top-6 right-6 flex gap-2 z-30">
             <button 
               onClick={() => setIsPlaying(true)} // Replay button
               className="p-2 bg-black/50 backdrop-blur hover:bg-indigo-600 rounded-lg border border-white/10 text-zinc-300 hover:text-white transition-all"
               title="Replay Instruction"
             >
               <PlayCircle className="w-5 h-5" />
             </button>
             <button className="p-2 bg-black/50 backdrop-blur hover:bg-zinc-800 rounded-lg border border-white/10 text-zinc-300 transition-all">
               <Maximize2 className="w-5 h-5" />
             </button>
          </div>

        </div>
      </div>
    </div>
  );
}