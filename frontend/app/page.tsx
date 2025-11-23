"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  FileText,
  ChevronRight,
  Loader2,
  Box,
  Plus
} from 'lucide-react';
import { fetchPDFs, uploadAndProcessPDF } from '@/lib/api';

interface Project {
  id: string;
  title: string;
  status: string;
  stepCount: number;
  thumbnail: string;
}

export default function Dashboard() {
  const [isUploading, setIsUploading] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch PDFs from backend on component mount
  useEffect(() => {
    loadPDFs();
  }, []);

  async function loadPDFs() {
    try {
      setIsLoading(true);
      const response = await fetchPDFs();

      // Transform backend data to project format
      const loadedProjects: Project[] = response.pdfs.map((pdf, index) => ({
        id: pdf.hash,
        title: pdf.pdf_filename.replace('.pdf', ''),
        status: 'Ready',
        stepCount: pdf.step_count,
        thumbnail: getRandomThumbnail(index)
      }));

      setProjects(loadedProjects);
      setError(null);
    } catch (err) {
      console.error('Failed to load PDFs:', err);
      setError('Failed to load projects. Make sure the backend server is running.');
    } finally {
      setIsLoading(false);
    }
  }

  function getRandomThumbnail(index: number): string {
    const colors = ['bg-orange-100', 'bg-indigo-100', 'bg-purple-100', 'bg-pink-100', 'bg-cyan-100'];
    return colors[index % colors.length];
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const file = files[0];

    setIsUploading(true);
    setError(null);

    try {
      // Upload and process the PDF
      const result = await uploadAndProcessPDF(file, true, true);

      // Add the new project to the list
      const newProject: Project = {
        id: result.pdf_hash,
        title: file.name.replace('.pdf', ''),
        status: 'Ready',
        stepCount: result.steps_processed,
        thumbnail: 'bg-indigo-100'
      };

      setProjects([newProject, ...projects]);
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 font-sans text-zinc-900 selection:bg-indigo-100">
      
      {/* 1. NAVBAR: Minimal and clean */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-zinc-200 px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-indigo-600 p-1.5 rounded-lg">
            <Box className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight text-zinc-800">3Docs</span>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-12">

        {/* 2. HERO SECTION: Value Prop */}
        <div className="mb-12">
          <h1 className="text-3xl md:text-4xl font-bold text-zinc-900 mb-3 tracking-tight">
            Turn static PDFs into <span
              className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600 selection:text-indigo-700">
              interactive 3D guides
            </span>.
          </h1>
          <p className="text-lg text-zinc-500 max-w-2xl">
            Upload your assembly manuals. Our AI parses instructions, generates 3D models, and creates voice-guided walkthroughs instantly.
          </p>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}
        </div>

        {/* 4. CONTENT GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">

          {/* CARD 1: THE UPLOAD ZONE (Modern 'New Item' Pattern) */}
          <div className="relative group min-h-[280px] rounded-2xl border-2 border-dashed border-zinc-300 hover:border-indigo-500 hover:bg-indigo-50/30 transition-all cursor-pointer flex flex-col items-center justify-center p-6 text-center overflow-hidden">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              disabled={isUploading}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
            />

            {isUploading ? (
              <div className="flex flex-col items-center animate-in fade-in zoom-in duration-300">
                <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mb-4" />
                <h3 className="text-zinc-900 font-medium">Analyzing PDF...</h3>
                <p className="text-xs text-zinc-500 mt-1">Generating 3D Assets</p>
              </div>
            ) : (
              <>
                <div className="w-12 h-12 bg-white rounded-full shadow-sm border border-zinc-100 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform text-indigo-600">
                  <Plus className="w-6 h-6" />
                </div>
                <h3 className="text-zinc-900 font-semibold mb-1">New Project</h3>
                <p className="text-sm text-zinc-500 max-w-[200px]">
                  Drag and drop a PDF manual, or click to browse.
                </p>
              </>
            )}
          </div>

          {/* Loading State */}
          {isLoading && !isUploading && (
            <div className="col-span-full flex justify-center items-center py-12">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
              <span className="ml-3 text-zinc-500">Loading projects...</span>
            </div>
          )}

          {/* CARD 2+: PROJECT ITEMS */}
          {!isLoading && projects.map((project) => (
            <Link key={project.id} href={`/workspace/${project.id}`} className="group block">
              <div className="bg-white rounded-2xl border border-zinc-200 overflow-hidden hover:shadow-xl hover:shadow-indigo-500/10 hover:border-indigo-200 transition-all duration-300 h-full flex flex-col">

                {/* Thumbnail Area */}
                <div className={`h-40 ${project.thumbnail} relative flex items-center justify-center`}>
                  {/* Decorative Icon */}
                  <FileText className="w-10 h-10 text-black/10 mix-blend-multiply" />

                  {/* Status Badge */}
                  <div className="absolute top-3 right-3">
                    <span className={`
                      inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border
                      ${project.status === 'Processing'
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : 'bg-emerald-50 text-emerald-700 border-emerald-200'}
                    `}>
                      {project.status === 'Processing' && <Loader2 className="w-3 h-3 mr-1 animate-spin" />}
                      {project.status}
                    </span>
                  </div>
                </div>

                {/* Content Area */}
                <div className="p-5 flex-1 flex flex-col">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-zinc-900 leading-tight group-hover:text-indigo-600 transition-colors">
                      {project.title}
                    </h3>
                  </div>

                  <div className="mt-auto pt-4 border-t border-zinc-100">
                    
                    <p className="text-xs text-zinc-500 flex items-center justify-between">
                      <span>{project.stepCount} steps</span>
                      <ChevronRight className="w-4 h-4 text-zinc-300 group-hover:text-indigo-500 transition-transform group-hover:translate-x-1" />
                    </p>
                    <p className="text-zinc-500 mb-1 text-xs">
                      <span className="font-mono">{project.id}</span>
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          ))}

        </div>
      </main>
    </div>
  );
}