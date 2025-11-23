"""
FastAPI server for on-demand PDF processing.
Provides REST API endpoints to trigger the processing pipeline.
"""

import asyncio
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from preprocessing import extract_pdf_content
from gemini_service import process_manual_images
from database import (
    init_db,
    calculate_pdf_hash,
    store_gemini_results,
    get_instructions_by_hash,
    get_instructions_with_images,
    update_mp3_filename,
    update_glb_filename
)
from tts import tts
from tripo import image_to_model


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    print("Initializing database...")
    init_db()
    print("Server ready!")
    yield
    # Shutdown: cleanup if needed
    print("Shutting down server...")


app = FastAPI(
    title="3Docs PDF Processing API",
    description="Process PDF manuals with AI to generate instructions, TTS, and 3D models",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ProcessRequest(BaseModel):
    pdf_filename: str
    voice_id: Optional[str] = "zh_CN-female-1"
    generate_tts: Optional[bool] = True
    generate_3d: Optional[bool] = True


class ProcessResponse(BaseModel):
    success: bool
    message: str
    pdf_hash: str
    steps_processed: int
    tts_files_generated: Optional[int] = None
    models_generated: Optional[int] = None


async def generate_tts_files(pdf_hash: bytes, hash_hex: str, voice_id: str = "zh_CN-female-1"):
    """Generate TTS audio files for all instructions."""
    volume_dir = Path("volume")
    rows = get_instructions_by_hash(pdf_hash)

    print(f"\nGenerating TTS for {len(rows)} instructions with voice: {voice_id}...")

    # Create TTS tasks for parallel processing
    tts_tasks = []
    for step, instruction_filename in rows:
        # Read the instruction file
        instruction_path = volume_dir / instruction_filename

        with open(instruction_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Split into title and description (separated by \n\n)
        parts = content.split("\n\n", 1)
        title, description = parts

        # Create async task (pass voice_id if tts function supports it)
        task = tts(description, hash_hex, step)
        tts_tasks.append((step, task))

    # Execute all TTS tasks in parallel
    tts_results = await asyncio.gather(*[task for _, task in tts_tasks], return_exceptions=True)

    # Update database with MP3 filenames
    generated_count = 0
    for (step, _), result in zip(tts_tasks, tts_results):
        if isinstance(result, Exception):
            print(f"  Step {step}: Failed - {result}")
        elif result:
            update_mp3_filename(pdf_hash, step, result)
            print(f"  Step {step}: {result}")
            generated_count += 1
        else:
            print(f"  Step {step}: No MP3 generated")

    print(f"TTS generation complete! Generated {generated_count}/{len(rows)} files")
    return generated_count


async def generate_3d_models(pdf_hash: bytes, hash_hex: str):
    """Generate 3D models for all instructional images."""
    volume_dir = Path("volume")
    image_rows = get_instructions_with_images(pdf_hash)

    print(f"\nGenerating 3D models for {len(image_rows)} instructions...")

    # Create tasks for parallel processing
    tasks = []
    for step, image_filename in image_rows:
        image_path = volume_dir / image_filename
        task = image_to_model(str(image_path), hash_hex, step)
        tasks.append((step, task))

    # Execute all tasks in parallel
    task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

    # Update database with GLB filenames
    generated_count = 0
    for (step, _), result in zip(tasks, task_results):
        if isinstance(result, Exception):
            print(f"  Step {step}: Failed - {result}")
        elif result:
            update_glb_filename(pdf_hash, step, result)
            print(f"  Step {step}: {result}")
            generated_count += 1
        else:
            print(f"  Step {step}: No GLB generated")

    print(f"3D model generation complete! Generated {generated_count}/{len(image_rows)} files")
    return generated_count


async def process_pdf_pipeline(
    pdf_filename: str,
    voice_id: str = "zh_CN-female-1",
    generate_tts: bool = True,
    generate_3d: bool = True
) -> dict:
    """
    Main PDF processing pipeline.

    Args:
        pdf_filename: Name of the PDF file in the volume directory
        voice_id: Voice ID for TTS generation
        generate_tts: Whether to generate TTS audio files
        generate_3d: Whether to generate 3D models

    Returns:
        Dictionary with processing results
    """
    volume_dir = Path("volume")
    pdf_path = volume_dir / pdf_filename

    # Check if PDF exists
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_filename}")

    print(f"\n{'='*60}")
    print(f"Processing PDF: {pdf_filename}")
    print(f"{'='*60}")

    # Extract filenames and instructions
    print("\n[1/4] Extracting PDF content...")
    image_filenames, instructions_filename = extract_pdf_content(pdf_filename)
    print(f"  Extracted {len(image_filenames)} images")

    # Process with Gemini
    print("\n[2/4] Processing with Gemini AI...")
    results = process_manual_images(image_filenames, instructions_filename)
    instructional = [m for m in results.get("matches", []) if m.get("is_instruction")]
    print(f"  Found {len(instructional)} instructional steps")

    # Calculate PDF hash
    pdf_hash = calculate_pdf_hash(str(pdf_path))
    hash_hex = pdf_hash.hex()[:16]
    print(f"  PDF Hash: {hash_hex}")

    # Store results in database
    print("\n[3/4] Storing results in database...")
    store_gemini_results(
        pdf_hash_bytes=pdf_hash,
        pdf_filename=pdf_filename,
        image_filenames=image_filenames,
        gemini_results=results
    )
    print(f"  Stored {len(instructional)} steps")

    # Generate TTS and 3D models based on flags
    print("\n[4/4] Generating assets...")
    tts_count = None
    model_count = None

    tasks = []
    if generate_tts:
        tasks.append(generate_tts_files(pdf_hash, hash_hex, voice_id))
    if generate_3d:
        tasks.append(generate_3d_models(pdf_hash, hash_hex))

    if tasks:
        results = await asyncio.gather(*tasks)
        if generate_tts and generate_3d:
            tts_count, model_count = results
        elif generate_tts:
            tts_count = results[0]
        elif generate_3d:
            model_count = results[0]

    print(f"\n{'='*60}")
    print(f"Pipeline complete!")
    print(f"{'='*60}\n")

    return {
        "pdf_hash": hash_hex,
        "steps_processed": len(instructional),
        "tts_files_generated": tts_count,
        "models_generated": model_count
    }


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "3Docs PDF Processing API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    volume_dir = Path("volume")
    return {
        "status": "healthy",
        "database": "connected",
        "volume_directory": str(volume_dir.absolute()),
        "volume_exists": volume_dir.exists()
    }


@app.post("/process", response_model=ProcessResponse)
async def process_pdf(request: ProcessRequest):
    """
    Process a PDF file through the AI pipeline.

    Accepts a PDF filename and optional parameters, then:
    1. Extracts images and text from the PDF
    2. Processes content with Gemini AI
    3. Generates TTS audio files (optional)
    4. Generates 3D models (optional)
    5. Stores all results in the database
    """
    try:
        result = await process_pdf_pipeline(
            pdf_filename=request.pdf_filename,
            voice_id=request.voice_id,
            generate_tts=request.generate_tts,
            generate_3d=request.generate_3d
        )

        return ProcessResponse(
            success=True,
            message=f"Successfully processed {request.pdf_filename}",
            pdf_hash=result["pdf_hash"],
            steps_processed=result["steps_processed"],
            tts_files_generated=result["tts_files_generated"],
            models_generated=result["models_generated"]
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/upload-and-process")
async def upload_and_process(
    file: UploadFile = File(...),
    voice_id: str = Form("zh_CN-female-1"),
    generate_tts: bool = Form(True),
    generate_3d: bool = Form(True)
):
    """
    Upload a PDF file and process it immediately.

    This endpoint combines file upload with processing:
    1. Saves the uploaded file to the volume directory
    2. Triggers the processing pipeline
    3. Returns processing results
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Save uploaded file
        volume_dir = Path("volume")
        volume_dir.mkdir(exist_ok=True)

        file_path = volume_dir / file.filename

        # Write file in chunks
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        print(f"Uploaded file saved: {file.filename} ({len(content)} bytes)")

        # Process the uploaded file
        result = await process_pdf_pipeline(
            pdf_filename=file.filename,
            voice_id=voice_id,
            generate_tts=generate_tts,
            generate_3d=generate_3d
        )

        return ProcessResponse(
            success=True,
            message=f"Successfully uploaded and processed {file.filename}",
            pdf_hash=result["pdf_hash"],
            steps_processed=result["steps_processed"],
            tts_files_generated=result["tts_files_generated"],
            models_generated=result["models_generated"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload and processing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
