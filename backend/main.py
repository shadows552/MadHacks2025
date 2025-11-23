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

async def main(
    pdf_filename: str = "test.pdf",
    voice_id: str = "zh_CN-female-1",
    generate_tts: bool = True,
    generate_3d: bool = True
):
    """
    Main pipeline execution.

    Args:
        pdf_filename: Name of the PDF file in the volume directory
        voice_id: Voice ID for TTS generation (not currently used in tts function)
        generate_tts: Whether to generate TTS audio files
        generate_3d: Whether to generate 3D models
    """
    # Initialize database
    init_db()

    # Validate PDF exists
    pdf_path = Path("volume") / pdf_filename
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_filename}")
        return

    print(f"\n{'='*60}")
    print(f"Processing PDF: {pdf_filename}")
    print(f"Voice ID: {voice_id}")
    print(f"Generate TTS: {generate_tts}")
    print(f"Generate 3D: {generate_3d}")
    print(f"{'='*60}\n")

    # Extract filenames and instructions
    print("[1/4] Extracting PDF content...")
    image_filenames, instructions_filename = extract_pdf_content(pdf_filename)
    print(f"  Extracted {len(image_filenames)} images")

    # Process with Gemini
    print("\n[2/4] Processing with Gemini AI...")
    results = process_manual_images(image_filenames, instructions_filename)

    # Print simplified results
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
    tasks = []
    if generate_tts:
        tasks.append(generate_tts_files(pdf_hash, hash_hex))
    if generate_3d:
        tasks.append(generate_3d_models(pdf_hash, hash_hex))

    if tasks:
        await asyncio.gather(*tasks)

    print(f"\n{'='*60}")
    print(f"Pipeline complete!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process PDF manuals with AI")
    parser.add_argument(
        "--pdf",
        type=str,
        default="test.pdf",
        help="PDF filename in the volume directory (default: test.pdf)"
    )
    parser.add_argument(
        "--voice-id",
        type=str,
        default="zh_CN-female-1",
        help="Voice ID for TTS generation (default: zh_CN-female-1)"
    )
    parser.add_argument(
        "--no-tts",
        action="store_true",
        help="Skip TTS generation"
    )
    parser.add_argument(
        "--no-3d",
        action="store_true",
        help="Skip 3D model generation"
    )

    args = parser.parse_args()

    asyncio.run(main(
        pdf_filename=args.pdf,
        voice_id=args.voice_id,
        generate_tts=not args.no_tts,
        generate_3d=not args.no_3d
    ))