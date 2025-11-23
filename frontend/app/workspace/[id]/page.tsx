"use client";
import React, { useState, useEffect, use, useRef } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  ArrowRight,
  ChevronRight,
  Box,
  PlayCircle,
  FileText,
  Volume2,
  Loader2
} from 'lucide-react';
import { Document, Page, pdfjs } from 'react-pdf';
import AssemblyScene from '@/components/AssemblyScene';
import {
  fetchPDFInfo,
  fetchPDFSteps,
  fetchInstructionData,
  fetchStepPosition,
  getPDFUrl,
  getImageUrl,
  getGLBUrl,
  getMP3Url,
  type StepPosition
} from '@/lib/api';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

// --- TYPES ---
interface ManualStep {
  stepNumber: number;
  title: string;
  description: string;
  imageUrl: string;
  modelUrl: string;
  audioUrl: string;
  position: StepPosition | null;
}

interface ManualData {
  productName: string;
  pdfHash: string;
  pdfUrl: string;
  steps: ManualStep[];
}

interface WorkspaceProps {
  params: Promise<{
    id: string;
  }>;
}

/**
 * Fetch manual data from backend using the PDF hash
 */
const fetchManualData = async (hash: string): Promise<ManualData> => {
  // Fetch PDF info
  const pdfInfo = await fetchPDFInfo(hash);
  if (!pdfInfo) {
    throw new Error(`PDF with hash ${hash} not found`);
  }

  // Fetch all step numbers
  const stepNumbers = await fetchPDFSteps(hash);

  // Fetch instruction data and position data for all steps in parallel
  const stepDataPromises = stepNumbers.map(async (stepNum) => {
    const [instructionData, position] = await Promise.all([
      fetchInstructionData(hash, stepNum),
      fetchStepPosition(hash, stepNum)
    ]);

    return {
      stepNumber: stepNum,
      title: instructionData.title,
      description: instructionData.description,
      imageUrl: getImageUrl(hash, stepNum),
      modelUrl: getGLBUrl(hash, stepNum),
      audioUrl: getMP3Url(hash, stepNum),
      position: position
    };
  });

  const steps = await Promise.all(stepDataPromises);

  return {
    productName: pdfInfo.pdf_filename.replace('.pdf', ''),
    pdfHash: hash,
    pdfUrl: getPDFUrl(hash),
    steps
  };
};

export default function Workspace({ params }: WorkspaceProps) {
  // Unwrap the params Promise using 'use'
  const { id } = use(params);

  const [manualData, setManualData] = useState<ManualData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [leftPanelWidth, setLeftPanelWidth] = useState<number>(66.66); // 2/3 in percentage
  const [isResizing, setIsResizing] = useState<boolean>(false);

  // PDF viewer state
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pdfWidth, setPdfWidth] = useState<number>(600);
  const pdfContainerRef = React.useRef<HTMLDivElement>(null);

  // Update PDF width based on container size
  useEffect(() => {
    const updatePdfWidth = () => {
      if (pdfContainerRef.current) {
        const containerWidth = pdfContainerRef.current.offsetWidth;
        setPdfWidth(Math.min(containerWidth - 32, 800)); // Max 800px, 32px for padding
      }
    };

    updatePdfWidth();
    window.addEventListener('resize', updatePdfWidth);
    return () => window.removeEventListener('resize', updatePdfWidth);
  }, []);

  // --- FETCH DATA ---
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        // Fetch real data from backend using the hash (id)
        const data = await fetchManualData(id);
        setManualData(data);
      } catch (err) {
        console.error("Failed to load manual", err);
        setError("Failed to load instruction manual. Make sure the backend server is running.");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]); // Depend on the unwrapped id

  // Steps are 0-indexed in backend, but we display as 1-indexed
  const activeStepData = manualData ? manualData.steps[currentStep - 1] : null;
  const totalSteps = manualData ? manualData.steps.length : 0;

  // Audio playback reference
  const audioRef = React.useRef<HTMLAudioElement | null>(null);

  // --- AUDIO PLAYBACK ---
  useEffect(() => {
    if (!activeStepData) return;

    // Create and play audio
    if (audioRef.current) {
      audioRef.current.pause();
    }

    const audio = new Audio(activeStepData.audioUrl);
    audioRef.current = audio;

    audio.onplay = () => setIsPlaying(true);
    audio.onended = () => setIsPlaying(false);
    audio.onerror = () => {
      console.error('Failed to load audio');
      setIsPlaying(false);
    };

    // Auto-play audio when step changes
    audio.play().catch(err => {
      console.error('Audio playback failed:', err);
      setIsPlaying(false);
    });

    return () => {
      audio.pause();
      audioRef.current = null;
    };
  }, [currentStep, activeStepData]);

  // Refs for PDF pages (for scrolling)
  const pageRefs = useRef<(HTMLDivElement | null)[]>([]);

  // --- PDF AUTO-SCROLL ---
  useEffect(() => {
    if (!activeStepData?.position || !pdfContainerRef.current) return;

    const { page_number, y_coordinate } = activeStepData.position;

    // Get the page element
    const pageElement = pageRefs.current[page_number];
    if (!pageElement) return;

    // Calculate scroll position
    const pageTop = pageElement.offsetTop;

    // Calculate scale factor (rendered PDF size vs original)
    // Standard PDF page width is 612 points
    const scaleFactor = pdfWidth / 612; // Approximate scale

    // Apply scale to Y coordinate
    const scaledY = y_coordinate * scaleFactor;

    // Calculate target scroll position (with 100px offset to center better)
    const targetScrollTop = pageTop + scaledY - 100;

    // Smooth scroll to position
    pdfContainerRef.current.scrollTo({
      top: targetScrollTop,
      behavior: 'smooth'
    });
  }, [currentStep, activeStepData, pdfWidth]);

  // --- RESIZE HANDLERS ---
  const handleMouseDown = () => {
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = (e.clientX / window.innerWidth) * 100;
      if (newWidth > 20 && newWidth < 80) {
        setLeftPanelWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

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
            <Link href="/" className="text-zinc-400 hover:text-zinc-200 transition-colors">
              Dashboard
            </Link>
            <ChevronRight className="w-4 h-4 text-zinc-600" />
            <span className="font-semibold text-zinc-100">{manualData.productName}</span>
          </nav>
        </div>
        <div className="text-xs text-zinc-500 font-mono">
          {manualData.pdfHash}
        </div>
      </header>

      {/* MAIN SPLIT VIEW */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">

        {/* LEFT PANEL: DYNAMIC 3D SCENE (2/3 width) */}
        <div
          className="w-full bg-black relative h-1/2 md:h-full"
          style={{ width: `${leftPanelWidth}%` }}
        >

          <div className="absolute inset-0 z-0">
            <AssemblyScene modelUrl={activeStepData.modelUrl} />
          </div>

          {/* SUBTITLES */}
          {isPlaying && (
            <div className="absolute bottom-32 left-8 right-8 z-20 flex justify-center pointer-events-none">
               <div className="bg-black/20 backdrop-blur-md border border-white/10 p-4 md:p-6 rounded-2xl shadow-xl max-w-xl animate-in fade-in slide-in-from-bottom-4 duration-500 pointer-events-auto">
                  <div className="flex items-center gap-3 mb-2">
                     <Volume2 className="w-4 h-4 text-indigo-400 animate-pulse" />
                     <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider">Voice Guide</span>
                  </div>
                  <p className="text-base md:text-lg font-medium text-white leading-relaxed text-center">
                    "{activeStepData.description}"
                  </p>
               </div>
            </div>
          )}

          {/* CONTROLS (moved to bottom right) */}
          <div className="absolute bottom-8 right-8 flex items-center gap-4 bg-zinc-900/90 backdrop-blur-md p-2 rounded-2xl shadow-2xl border border-white/10 z-30">
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
               onClick={() => {
                 if (audioRef.current) {
                   audioRef.current.currentTime = 0;
                   audioRef.current.play();
                 }
               }}
               className="p-2 bg-black/50 backdrop-blur hover:bg-indigo-600 rounded-lg border border-white/10 text-zinc-300 hover:text-white transition-all"
               title="Replay audio"
             >
               <PlayCircle className="w-5 h-5" />
             </button>
          </div>

        </div>

        {/* RESIZABLE DIVIDER */}
        <div
          className="hidden md:block w-1 bg-zinc-700 hover:bg-indigo-500 cursor-col-resize transition-colors relative z-40"
          onMouseDown={handleMouseDown}
          style={{ cursor: isResizing ? 'col-resize' : 'col-resize' }}
        >
          <div className="absolute inset-y-0 -left-1 -right-1" />
        </div>

        {/* RIGHT PANEL: PDF VIEWER (1/3 width) */}
        <div
          className="w-full bg-zinc-800 border-b md:border-b-0 md:border-l border-zinc-700 relative flex flex-col h-1/2 md:h-full"
          style={{ width: `${100 - leftPanelWidth}%` }}
        >
           <div className="h-12 border-b border-zinc-700 flex items-center justify-between px-4 bg-zinc-800/50 backdrop-blur shrink-0">
              <span className="text-xs font-medium text-zinc-400 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                {manualData.productName}
              </span>
              <span className="text-xs bg-black/30 px-2 py-1 rounded text-zinc-300">
                Step {currentStep} of {totalSteps}
              </span>
           </div>

           {/* PDF VIEWER CONTAINER */}
           <div ref={pdfContainerRef} className="flex-1 bg-zinc-900 relative overflow-y-auto">
              <div className="flex flex-col items-center py-4">
                <Document
                  file={manualData.pdfUrl}
                  onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                  loading={
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                    </div>
                  }
                  error={
                    <div className="flex items-center justify-center py-12 text-red-500">
                      Failed to load PDF
                    </div>
                  }
                >
                  {numPages && Array.from(new Array(numPages), (_, index) => (
                    <div
                      key={`page_${index + 1}`}
                      ref={(el) => { pageRefs.current[index] = el; }}
                    >
                      <Page
                        pageNumber={index + 1}
                        width={pdfWidth}
                        renderTextLayer={false}
                        renderAnnotationLayer={false}
                        className="mb-4"
                      />
                    </div>
                  ))}
                </Document>
              </div>
           </div>
        </div>

      </div>
    </div>
  );
}