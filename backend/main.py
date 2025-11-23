"""
Main pipeline for processing PDF manuals with Gemini AI.
"""

import asyncio
from pathlib import Path
from preprocessing import extract_pdf_content
from gemini_service import process_manual_images
from database import init_db, calculate_pdf_hash, store_gemini_results, get_instructions_by_hash, get_instructions_with_images, update_mp3_filename, update_glb_filename
from tts import tts
from tripo import image_to_model

async def generate_tts_files(pdf_hash: bytes, hash_hex: str):
    """Generate TTS audio files for all instructions."""
    volume_dir = Path("volume")
    rows = get_instructions_by_hash(pdf_hash)

    print(f"\nGenerating TTS for {len(rows)} instructions...")

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

        # Create async task
        task = tts(description, hash_hex, step)
        tts_tasks.append((step, task))

    # Execute all TTS tasks in parallel
    tts_results = await asyncio.gather(*[task for _, task in tts_tasks], return_exceptions=True)

    # Update database with MP3 filenames
    for (step, _), result in zip(tts_tasks, tts_results):
        if isinstance(result, Exception):
            print(f"  Step {step}: Failed - {result}")
        elif result:
            update_mp3_filename(pdf_hash, step, result)
            print(f"  Step {step}: {result}")
        else:
            print(f"  Step {step}: No MP3 generated")

    print(f"TTS generation complete!")

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
    for (step, _), result in zip(tasks, task_results):
        if isinstance(result, Exception):
            print(f"  Step {step}: Failed - {result}")
        elif result:
            update_glb_filename(pdf_hash, step, result)
            print(f"  Step {step}: {result}")
        else:
            print(f"  Step {step}: No GLB generated")

    print(f"3D model generation complete!")

async def main():
    """Main pipeline execution."""
    # Initialize database
    init_db()

    # Hardcoded PDF for now - will be replaced with Flask endpoint
    pdf_filename = "test.pdf"

    # Extract filenames and instructions
    image_filenames, instructions_filename = extract_pdf_content(pdf_filename)

    # Process with Gemini
    results = process_manual_images(image_filenames, instructions_filename)

    # Print simplified results
    instructional = [m for m in results.get("matches", []) if m.get("is_instruction")]

    # Calculate PDF hash
    pdf_path = Path("volume") / pdf_filename
    pdf_hash = calculate_pdf_hash(str(pdf_path))
    hash_hex = pdf_hash.hex()[:16]

    # Store results in database
    store_gemini_results(
        pdf_hash_bytes=pdf_hash,
        pdf_filename=pdf_filename,
        image_filenames=image_filenames,
        gemini_results=results
    )

    # Generate TTS and 3D models in parallel
    await asyncio.gather(
        generate_tts_files(pdf_hash, hash_hex),
        generate_3d_models(pdf_hash, hash_hex)
    )

    print(f"\nPipeline complete!")

if __name__ == "__main__":
    asyncio.run(main())
