"""
Main pipeline for processing PDF manuals with Gemini AI.
"""

from preprocessing import extract_pdf_content
from gemini_service import process_manual_images

if __name__ == "__main__":
    # Hardcoded PDF for now - will be replaced with Flask endpoint
    pdf_filename = "test.pdf"

    print("Processing PDF...")
    # Extract filenames and instructions
    image_filenames, instructions_filename = extract_pdf_content(pdf_filename)

    # Process with Gemini, returns 
    results = process_manual_images(image_filenames, instructions_filename)

    # Print simplified results
    instructional = [m for m in results.get("matches", []) if m.get("is_instruction")]

    print(f"\nFound {len(instructional)} instructional images:")
    for match in instructional:
        print(f"\n{match['instruction_title']}")
        print(f"  {match['instruction_description'][:100]}...")

    print(f"\nTotal: {len(results.get('matches', []))} images")
