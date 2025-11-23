"""
Main pipeline for processing PDF manuals with Gemini AI.
"""

from pathlib import Path
from preprocessing import extract_pdf_content
from gemini_service import process_manual_images
from database import init_db, calculate_pdf_hash, store_gemini_results, get_instructions_by_hash, update_mp3_filename
from tts import tts

if __name__ == "__main__":
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

    # Store results in database
    store_gemini_results(
        pdf_hash_bytes=pdf_hash,
        pdf_filename=pdf_filename,
        image_filenames=image_filenames,
        gemini_results=results
    )

    # Generate TTS audio files
    volume_dir = Path("volume")

    # Get all instructions for this PDF hash
    rows = get_instructions_by_hash(pdf_hash)

    print(f"\nGenerating TTS for {len(rows)} instructions...")

    for step, instruction_filename in rows:
        # Read the instruction file
        instruction_path = volume_dir / instruction_filename

        with open(instruction_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Split into title and description (separated by \n\n)
        parts = content.split("\n\n", 1)

        title, description = parts

        # Generate MP3 filename based on instruction filename
        instruction_stem = Path(instruction_filename).stem
        mp3_filename = f"{instruction_stem}.mp3"
        mp3_path = volume_dir / mp3_filename

        # Generate TTS for the description
        try:
            tts(description, output_file=str(mp3_path))

            # Update database with MP3 filename
            update_mp3_filename(pdf_hash, step, mp3_filename)

            print(f"  Step {step}: {mp3_filename}")
        except Exception as e:
            print(f"  Step {step}: Failed - {e}")

    print(f"\nPipeline complete!")
