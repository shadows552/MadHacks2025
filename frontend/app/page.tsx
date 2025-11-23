"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ChevronRight,
  Loader2,
  Plus
} from 'lucide-react';
import { fetchPDFs, uploadAndProcessPDF, getImageUrl } from '@/lib/api';

interface Project {
  id: string;
  title: string;
  stepCount: number;
  thumbnailUrl: string;
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
      const loadedProjects: Project[] = response.pdfs.map((pdf) => ({
        id: pdf.hash,
        title: pdf.pdf_filename.replace('.pdf', ''),
        stepCount: pdf.step_count,
        thumbnailUrl: getImageUrl(pdf.hash, 0) // Use first image as thumbnail
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
        stepCount: result.steps_processed,
        thumbnailUrl: getImageUrl(result.pdf_hash, 0) // Use first image as thumbnail
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
<<<<<<< Updated upstream
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

=======
    <div className="min-h-screen bg-zinc-900 font-sans text-white selection:bg-indigo-900">
>>>>>>> Stashed changes
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">

          {/* Loading State */}
          {isLoading && !isUploading && (
            <div className="col-span-full flex justify-center items-center py-12">
              <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
              <span className="ml-3 text-zinc-400">Loading projects...</span>
            </div>
          )}

          {/* PROJECT ITEMS */}
          {!isLoading && projects.map((project) => (
            <Link key={project.id} href={`/workspace/${project.id}`} className="group block">
              <div className="bg-zinc-800 rounded-2xl border border-zinc-700 overflow-hidden hover:shadow-xl hover:shadow-indigo-500/20 hover:border-indigo-500 transition-all duration-300 h-full flex flex-col">

                {/* Thumbnail Area */}
                <div className="h-40 relative flex items-center justify-center bg-zinc-900 overflow-hidden">
                  {/* Thumbnail Image */}
                  <img
                    src={project.thumbnailUrl}
                    alt={`${project.title} thumbnail`}
                    className="w-full h-full object-cover relative z-10"
                    onError={(e) => {
                      // Fallback to icon if image fails to load
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                </div>

                {/* Content Area */}
                <div className="p-5 flex-1 flex flex-col">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-white leading-tight group-hover:text-indigo-400 transition-colors">
                      {project.title}
                    </h3>
                  </div>

                  <div className="mt-auto pt-4 border-t border-zinc-700">

                    <p className="text-xs text-zinc-400 flex items-center justify-between">
                      <span>{project.stepCount} steps</span>
                      <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-indigo-500 transition-transform group-hover:translate-x-1" />
                    </p>
                    <p className="text-zinc-500 mb-1 text-xs">
                      <span className="font-mono">{project.id}</span>
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          ))}

          {/* UPLOAD ZONE - New Project Card (Last) */}
          {!isLoading && (
            <div className="relative group min-h-[280px] rounded-2xl border-2 border-dashed border-zinc-700 hover:border-indigo-500 hover:bg-indigo-900/30 transition-all cursor-pointer flex flex-col items-center justify-center p-6 text-center overflow-hidden">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                disabled={isUploading}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              />

              {isUploading ? (
                <div className="flex flex-col items-center animate-in fade-in zoom-in duration-300">
                  <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mb-4" />
                  <h3 className="text-white font-medium">Analyzing PDF...</h3>
                  <p className="text-xs text-zinc-400 mt-1">Generating 3D Assets</p>
                </div>
              ) : (
                <>
                  <div className="w-12 h-12 bg-zinc-800 rounded-full shadow-sm border border-zinc-700 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform text-indigo-500">
                    <Plus className="w-6 h-6" />
                  </div>
                  <h3 className="text-white font-semibold mb-1">New Project</h3>
                  <p className="text-sm text-zinc-400 max-w-[200px]">
                    Drag and drop a PDF manual, or click to browse.
                  </p>
                </>
              )}
            </div>
          )}

        </div>
      </main>
    </div>
  );
}