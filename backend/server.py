"""
FastAPI server for on-demand PDF processing.
Provides REST API endpoints to trigger the processing pipeline.
"""

import asyncio
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
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
    update_mp3_filename_by_hash_hex,
    update_glb_filename,
    get_all_pdfs,
    get_pdf_filename_by_hash,
    get_file_info_by_hash_step,
    get_step_position
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
    generate_tts: Optional[bool] = True
    generate_3d: Optional[bool] = True


class ProcessResponse(BaseModel):
    success: bool
    message: str
    pdf_hash: str
    steps_processed: int
    tts_files_generated: Optional[int] = None
    models_generated: Optional[int] = None


class PDFInfo(BaseModel):
    hash: str
    pdf_filename: str
    step_count: int


class PDFListResponse(BaseModel):
    success: bool
    pdfs: list[PDFInfo]
    total_count: int


async def generate_tts_files(pdf_hash: bytes, hash_hex: str):
    """Generate TTS audio files for all instructions."""
    volume_dir = Path("volume")
    rows = get_instructions_by_hash(pdf_hash)

    print(f"\nGenerating TTS for {len(rows)} instructions...")

    # Check which TTS files already exist and which need to be generated
    tts_tasks = []
    skipped_count = 0

    for step, instruction_filename in rows:
        # Check if MP3 file already exists
        expected_mp3_filename = f"{hash_hex}-{step}.mp3"
        mp3_path = volume_dir / expected_mp3_filename

        if mp3_path.exists():
            # TTS already exists, just update database
            update_mp3_filename(pdf_hash, step, expected_mp3_filename)
            print(f"  Step {step}: Using existing TTS {expected_mp3_filename}")
            skipped_count += 1
        else:
            # TTS doesn't exist, create generation task
            # Read the instruction file
            instruction_path = volume_dir / instruction_filename

            with open(instruction_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            # Split into title and description (separated by \n\n)
            parts = content.split("\n\n", 1)
            description = parts[1] if len(parts) > 1 else parts[0]

            # Create async task
            task = tts(description, hash_hex, step)
            tts_tasks.append((step, task))

    # Execute all TTS tasks in parallel
    if tts_tasks:
        print(f"  Generating {len(tts_tasks)} new TTS files (skipped {skipped_count} existing)...")
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
    else:
        generated_count = 0
        print(f"  All {skipped_count} TTS files already exist, no generation needed")

    total_count = generated_count + skipped_count
    print(f"TTS generation complete! Generated {generated_count} new, reused {skipped_count} existing ({total_count} total)")
    return total_count


async def regenerate_single_tts(hash_hex: str, step: int, instruction_filename: str) -> str:
    """
    Regenerate TTS file for a single step using the same logic as generate_tts_files.

    Args:
        hash_hex: First 16 characters of the PDF hash
        step: Step number
        instruction_filename: Name of the instruction text file

    Returns:
        Generated MP3 filename
    """
    volume_dir = Path("volume")

    # Read the instruction file
    instruction_path = volume_dir / instruction_filename

    with open(instruction_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Split into title and description (separated by \n\n)
    parts = content.split("\n\n", 1)
    description = parts[1] if len(parts) > 1 else parts[0]

    # Generate TTS (same logic as generate_tts_files)
    mp3_filename = await tts(description, hash_hex, step)

    print(f"  Step {step}: {mp3_filename}")
    return mp3_filename


async def generate_3d_models(pdf_hash: bytes, hash_hex: str):
    """Generate 3D models for all instructional images."""
    volume_dir = Path("volume")
    image_rows = get_instructions_with_images(pdf_hash)

    print(f"\nGenerating 3D models for {len(image_rows)} instructions...")

    # Check which models already exist and which need to be generated
    tasks = []
    skipped_count = 0

    for step, image_filename in image_rows:
        # Check if GLB file already exists
        expected_glb_filename = f"{hash_hex}-{step}.glb"
        glb_path = volume_dir / expected_glb_filename

        if glb_path.exists():
            # Model already exists, just update database
            update_glb_filename(pdf_hash, step, expected_glb_filename)
            print(f"  Step {step}: Using existing model {expected_glb_filename}")
            skipped_count += 1
        else:
            # Model doesn't exist, create generation task
            image_path = volume_dir / image_filename
            task = image_to_model(str(image_path), hash_hex, step)
            tasks.append((step, task))

    # Execute all generation tasks in parallel
    if tasks:
        print(f"  Generating {len(tasks)} new models (skipped {skipped_count} existing)...")
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
    else:
        generated_count = 0
        print(f"  All {skipped_count} models already exist, no generation needed")

    total_count = generated_count + skipped_count
    print(f"3D model generation complete! Generated {generated_count} new, reused {skipped_count} existing ({total_count} total)")
    return total_count


async def process_pdf_pipeline(
    pdf_filename: str,
    generate_tts: bool = True,
    generate_3d: bool = True
) -> dict:
    """
    Main PDF processing pipeline.

    Args:
        pdf_filename: Name of the PDF file in the volume directory
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

    # Extract filenames and instructions with position data
    print("\n[1/4] Extracting PDF content...")
    image_filenames, instructions_filename, image_positions = extract_pdf_content(pdf_filename)
    print(f"  Extracted {len(image_filenames)} images")
    print(f"  Images with position data: {sum(1 for p in image_positions if p is not None)}")

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
        gemini_results=results,
        image_positions=image_positions
    )
    print(f"  Stored {len(instructional)} steps")

    # Generate TTS and 3D models based on flags
    print("\n[4/4] Generating assets...")
    tts_count = None
    model_count = None

    tasks = []
    if generate_tts:
        tasks.append(generate_tts_files(pdf_hash, hash_hex))
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


@app.get("/pdfs", response_model=PDFListResponse)
async def list_pdfs():
    """
    Get all PDFs currently in the database.

    Returns a list of PDFs with their hash, filename, and step count.
    """
    try:
        pdfs = get_all_pdfs()

        pdf_list = [
            PDFInfo(hash=hash_hex, pdf_filename=filename, step_count=count)
            for hash_hex, filename, count in pdfs
        ]

        return PDFListResponse(
            success=True,
            pdfs=pdf_list,
            total_count=len(pdf_list)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve PDFs: {str(e)}")


@app.post("/upload-and-process")
async def upload_and_process(
    file: UploadFile = File(...),
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


@app.get("/pdf/{hash}")
async def get_pdf(hash: str):
    """
    Get the original PDF file by hash.

    Args:
        hash: First 16 characters of the PDF hash
    """
    try:
        pdf_filename = get_pdf_filename_by_hash(hash)
        if not pdf_filename:
            raise HTTPException(status_code=404, detail=f"PDF with hash {hash} not found")

        volume_dir = Path("volume")
        pdf_path = volume_dir / pdf_filename

        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"PDF file {pdf_filename} not found on disk")

        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=pdf_filename
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve PDF: {str(e)}")


@app.get("/image/{hash}/{step}")
async def get_image(hash: str, step: int):
    """
    Get the image file for a specific step.

    Args:
        hash: First 16 characters of the PDF hash
        step: Step number
    """
    try:
        file_info = get_file_info_by_hash_step(hash, step)
        if not file_info or not file_info['image_filename']:
            raise HTTPException(status_code=404, detail=f"Image not found for hash {hash}, step {step}")

        volume_dir = Path("volume")
        image_path = volume_dir / file_info['image_filename']

        if not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image file {file_info['image_filename']} not found on disk")

        # Determine media type based on extension
        ext = image_path.suffix.lower()
        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = media_type_map.get(ext, 'application/octet-stream')

        return FileResponse(
            path=str(image_path),
            media_type=media_type,
            filename=file_info['image_filename']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")


@app.get("/glb/{hash}/{step}")
async def get_glb(hash: str, step: int):
    """
    Get the 3D model (GLB) file for a specific step.

    Args:
        hash: First 16 characters of the PDF hash
        step: Step number
    """
    try:
        file_info = get_file_info_by_hash_step(hash, step)
        if not file_info or not file_info['glb_filename']:
            raise HTTPException(status_code=404, detail=f"GLB not found for hash {hash}, step {step}")

        volume_dir = Path("volume")
        glb_path = volume_dir / file_info['glb_filename']

        if not glb_path.exists():
            raise HTTPException(status_code=404, detail=f"GLB file {file_info['glb_filename']} not found on disk")

        return FileResponse(
            path=str(glb_path),
            media_type="model/gltf-binary",
            filename=file_info['glb_filename']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve GLB: {str(e)}")


@app.get("/mp3/{hash}/{step}")
async def get_mp3(hash: str, step: int):
    """
    Get the audio (MP3) file for a specific step.
    If the MP3 file is not found, it will be automatically regenerated.

    Args:
        hash: First 16 characters of the PDF hash
        step: Step number
    """
    try:
        file_info = get_file_info_by_hash_step(hash, step)
        if not file_info:
            raise HTTPException(status_code=404, detail=f"No data found for hash {hash}, step {step}")

        volume_dir = Path("volume")

        # Check if MP3 exists, if not regenerate it
        mp3_filename = file_info.get('mp3_filename')
        mp3_path = volume_dir / mp3_filename if mp3_filename else None

        if not mp3_filename or not mp3_path or not mp3_path.exists():
            # MP3 is missing, regenerate it
            print(f"MP3 not found for hash {hash}, step {step}. Regenerating...")

            # Get instruction text from the instruction file
            instruction_filename = file_info.get('instruction_filename')
            if not instruction_filename:
                raise HTTPException(status_code=404, detail=f"No instruction file found for hash {hash}, step {step}")

            instruction_path = volume_dir / instruction_filename
            if not instruction_path.exists():
                raise HTTPException(status_code=404, detail=f"Instruction file {instruction_filename} not found on disk")

            # Regenerate MP3 using the same logic as generate_tts_files
            mp3_filename = await regenerate_single_tts(hash, step, instruction_filename)

            # Update database with new MP3 filename
            update_mp3_filename_by_hash_hex(hash, step, mp3_filename)

            mp3_path = volume_dir / mp3_filename
            print(f"MP3 regenerated successfully: {mp3_filename}")

        return FileResponse(
            path=str(mp3_path),
            media_type="audio/mpeg",
            filename=mp3_filename
        )
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve MP3: {str(e)}")


@app.get("/instruction/{hash}/{step}")
async def get_instruction(hash: str, step: int):
    """
    Get the instruction text file for a specific step.

    Args:
        hash: First 16 characters of the PDF hash
        step: Step number
    """
    try:
        file_info = get_file_info_by_hash_step(hash, step)
        if not file_info or not file_info['instruction_filename']:
            raise HTTPException(status_code=404, detail=f"Instruction not found for hash {hash}, step {step}")

        volume_dir = Path("volume")
        instruction_path = volume_dir / file_info['instruction_filename']

        if not instruction_path.exists():
            raise HTTPException(status_code=404, detail=f"Instruction file {file_info['instruction_filename']} not found on disk")

        return FileResponse(
            path=str(instruction_path),
            media_type="text/plain",
            filename=file_info['instruction_filename']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve instruction: {str(e)}")


@app.get("/step-position/{hash}/{step}")
async def get_step_position_endpoint(hash: str, step: int):
    """
    Get the page number and Y-percentage for a specific step.

    Args:
        hash: First 16 characters of the PDF hash
        step: Step number

    Returns:
        JSON with page_number and y_percentage (0-100% from top of page)
    """
    try:
        position = get_step_position(hash, step)
        if not position:
            raise HTTPException(
                status_code=404,
                detail=f"Position data not found for hash {hash}, step {step}"
            )

        return {
            "success": True,
            "page_number": position['page_number'],
            "y_percentage": position['y_percentage']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve position data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
