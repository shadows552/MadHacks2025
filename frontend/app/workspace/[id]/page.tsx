"use client";
// 1. Add 'use' to imports
import React, { useState, useEffect, use, useRef } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  ArrowRight,
  ChevronRight,
  Box,
  Maximize2,
  PlayCircle,
  FileText,
  Volume2,
  Loader2
} from 'lucide-react';
import AssemblyScene from '@/components/AssemblyScene';
import { Document, Page, pdfjs } from 'react-pdf';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

// --- TYPES ---
interface ManualStep {
  stepNumber: number;
  title: string;
  description: string;
  voiceGuidance: string;
  pdfPage: number;
  modelUrl: string;
}

interface ManualData {
  productName: string;
  pdfTitle: string;
  steps: ManualStep[];
}

// 2. Update Interface: params is now a Promise
interface WorkspaceProps {
  params: Promise<{
    id: string;
  }>;
}

const mockFetchManualData = async (id: string): Promise<ManualData> => {
  await new Promise(resolve => setTimeout(resolve, 1500));
  return {
    productName: "SANDSBERG Table",
    pdfTitle: "SANDSBERG_assembly_instructions.pdf",
    steps: [
      { 
        stepNumber: 1, 
        title: "Prepare Workspace", 
        description: "Place the table frame upside down on a soft surface.", 
        voiceGuidance: "Start by placing the table top upside down on a rug or carpet to prevent scratches.", 
        pdfPage: 1,
        modelUrl: "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Box/glTF-Binary/Box.glb"
      },
      { 
        stepNumber: 2, 
        title: "Insert Brackets", 
        description: "Push the plastic corner brackets into the metal frame.", 
        voiceGuidance: "Take the four plastic corner brackets and push them into the frame slots until they click.", 
        pdfPage: 2,
        modelUrl: "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/main/2.0/ToyCar/glTF-Binary/ToyCar.glb"
      },
      { 
        stepNumber: 3, 
        title: "Secure Frame", 
        description: "Align frame and tighten screws.", 
        voiceGuidance: "Use the provided Allen key to firmly secure the frame using the ten medium-sized screws.", 
        pdfPage: 3,
        modelUrl: "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Lantern/glTF-Binary/Lantern.glb"
      },
      { 
        stepNumber: 4, 
        title: "Attach Legs", 
        description: "Screw in the legs.", 
        voiceGuidance: "Finally, screw the legs into the brackets. Hand tighten them first, then give them a final turn.", 
        pdfPage: 4,
        modelUrl: "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Avocado/glTF-Binary/Avocado.glb"
      },
    ]
  };
};

export default function Workspace({ params }: WorkspaceProps) {
  // 3. Unwrap the params Promise using 'use'
  // This extracts 'id' safely for use in the component
  const { id } = use(params);

  const [manualData, setManualData] = useState<ManualData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // PDF state
  const [numPages, setNumPages] = useState<number | null>(null);
  const pdfContainerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  // --- FETCH DATA ---
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        // Use the unwrapped 'id' variable here
        const data = await mockFetchManualData(id);
        setManualData(data);
      } catch (err) {
        console.error("Failed to load manual", err);
        setError("Failed to load instruction manual.");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]); // Depend on the unwrapped id

  const activeStepData = manualData ? manualData.steps[currentStep - 1] : null;
  const totalSteps = manualData ? manualData.steps.length : 0;

  // --- VOICE SIMULATION ---
  useEffect(() => {
    if (!activeStepData) return;
    setIsPlaying(true);
    const timer = setTimeout(() => setIsPlaying(false), 4000);
    return () => clearTimeout(timer);
  }, [currentStep, activeStepData]);

  // --- PDF SCROLL EFFECT ---
  useEffect(() => {
    if (!activeStepData) return;
    const targetPage = activeStepData.pdfPage;
    const pageElement = pageRefs.current.get(targetPage);

    if (pageElement && pdfContainerRef.current) {
      pageElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [currentStep, activeStepData]);

  if (loading) {
    return (
      <div className="h-screen w-full flex flex-col items-center justify-center bg-zinc-900 text-white">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-500 mb-4" />
        <h2 className="text-xl font-semibold">Loading 3D Manual...</h2>
        <p className="text-zinc-500">Fetching assets and instructions</p>
      </div>
    );
  }

  if (error || !manualData || !activeStepData) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-zinc-900 text-white">
        <div className="text-center">
          <h2 className="text-xl font-bold text-red-500 mb-2">Error</h2>
          <p>{error || "Manual not found"}</p>
          <a href="/" className="mt-4 inline-block text-indigo-400 hover:underline">Return to Dashboard</a>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full flex flex-col bg-zinc-900 font-sans text-white overflow-hidden">
      
      {/* HEADER */}
      <header className="h-14 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between px-4 shrink-0 z-20">
        <div className="flex items-center gap-3">
          <Link href="/" className="p-2 hover:bg-zinc-800 rounded-lg transition-colors text-zinc-400 hover:text-white">
            <Box className="w-5 h-5" />
          </Link>
          <div className="h-4 w-[1px] bg-zinc-700 mx-1" />
          <nav className="flex items-center gap-2 text-sm">
            <span className="text-zinc-400">Dashboard</span>
            <ChevronRight className="w-4 h-4 text-zinc-600" />
            <span className="font-semibold text-zinc-100">{manualData.productName}</span>
          </nav>
        </div>
      </header>

      {/* MAIN SPLIT VIEW WITH RESIZABLE PANELS */}
      <div className="flex-1 overflow-hidden">
        <PanelGroup direction="horizontal">
          {/* LEFT PANEL: PDF VIEWER */}
          <Panel defaultSize={50} minSize={30}>
            <div className="w-full h-full bg-zinc-800 border-r border-zinc-700 relative flex flex-col">
              <div className="h-12 border-b border-zinc-700 flex items-center justify-between px-4 bg-zinc-800/50 backdrop-blur shrink-0">
                <span className="text-xs font-medium text-zinc-400 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  {manualData.pdfTitle}
                </span>
                <span className="text-xs bg-black/30 px-2 py-1 rounded text-zinc-300">
                  Page {activeStepData.pdfPage}
                </span>
              </div>

              {/* PDF DOCUMENT CONTAINER WITH SCROLLING */}
              <div
                ref={pdfContainerRef}
                className="flex-1 bg-zinc-900 relative overflow-auto"
              >
                <Document
                  file="/sample.pdf"
                  onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                  loading={
                    <div className="flex items-center justify-center h-full">
                      <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                    </div>
                  }
                >
                  {numPages &&
                    Array.from(new Array(numPages), (el, index) => (
                      <div
                        key={`page_${index + 1}`}
                        ref={(el) => {
                          if (el) pageRefs.current.set(index + 1, el);
                        }}
                        className="mb-4"
                      >
                        <Page
                          pageNumber={index + 1}
                          renderTextLayer={true}
                          renderAnnotationLayer={true}
                          className="mx-auto"
                          width={Math.min(window.innerWidth * 0.4, 800)}
                        />
                      </div>
                    ))}
                </Document>
              </div>
            </div>
          </Panel>

          {/* RESIZE HANDLE */}
          <PanelResizeHandle className="w-1 bg-zinc-700 hover:bg-indigo-500 transition-colors cursor-col-resize" />

          {/* RIGHT PANEL: DYNAMIC 3D SCENE */}
          <Panel defaultSize={50} minSize={30}>
            <div className="w-full h-full bg-black relative">
          
          <div className="absolute inset-0 z-0">
            <AssemblyScene modelUrl={activeStepData.modelUrl} />
          </div>

          {/* SUBTITLES */}
          {isPlaying && (
            <div className="absolute bottom-32 left-8 right-8 z-20 flex justify-center pointer-events-none">
               <div className="bg-black/70 backdrop-blur-md border border-white/10 p-4 md:p-6 rounded-2xl shadow-2xl max-w-xl animate-in fade-in slide-in-from-bottom-4 duration-500 pointer-events-auto">
                  <div className="flex items-center gap-3 mb-2">
                     <Volume2 className="w-4 h-4 text-indigo-400 animate-pulse" />
                     <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider">Voice Guide</span>
                  </div>
                  <p className="text-base md:text-lg font-medium text-white leading-relaxed text-center">
                    "{activeStepData.voiceGuidance}"
                  </p>
               </div>
            </div>
          )}

          {/* CONTROLS */}
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-zinc-900/90 backdrop-blur-md p-2 rounded-2xl shadow-2xl border border-white/10 z-30">
             <button 
               onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
               disabled={currentStep === 1}
               className="p-3 rounded-xl hover:bg-zinc-800 disabled:opacity-30 transition-all text-zinc-200"
             >
               <ArrowLeft className="w-6 h-6" />
             </button>

             <div className="flex flex-col items-center px-4">
               <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Step</span>
               <span className="text-xl font-bold text-white tabular-nums leading-none">{currentStep}</span>
             </div>

             <button 
               onClick={() => setCurrentStep(Math.min(totalSteps, currentStep + 1))}
               disabled={currentStep === totalSteps}
               className="group p-3 rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-30 transition-all shadow-lg shadow-indigo-900/20"
             >
               <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
             </button>
          </div>

          <div className="absolute top-6 right-6 flex gap-2 z-30">
             <button 
               onClick={() => setIsPlaying(true)}
               className="p-2 bg-black/50 backdrop-blur hover:bg-indigo-600 rounded-lg border border-white/10 text-zinc-300 hover:text-white transition-all"
             >
               <PlayCircle className="w-5 h-5" />
             </button>
             <button className="p-2 bg-black/50 backdrop-blur hover:bg-zinc-800 rounded-lg border border-white/10 text-zinc-300 transition-all">
               <Maximize2 className="w-5 h-5" />
             </button>
          </div>

            </div>
          </Panel>
        </PanelGroup>
      </div>
    </div>
  );
}