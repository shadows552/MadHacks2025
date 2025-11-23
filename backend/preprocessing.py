"""
PDF preprocessing module to extract images and text.
Extracts all images and text from a PDF and saves them to the volume directory.
"""

import os
import uuid
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF
from PIL import Image
import io


def extract_pdf_content(pdf_path: str, output_dir: str = "volume") -> Tuple[List[str], str, List[dict]]:
    """
    Extract images and text from a PDF file with position data.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted content (default: "volume")

    Returns:
        Tuple of (list of image paths in order, path to instructions text file, list of position data)
        Position data includes: page_number and y_percentage (0-100% from top of page)
    """
    # Construct the PDF path within the volume directory
    pdf_path = Path("./volume") / pdf_path
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate unique identifier for this PDF extraction
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
    timestamp = str(int(Path(pdf_path).stat().st_mtime))  # Use PDF modification time

    # Use combination of timestamp and UUID for uniqueness
    file_prefix = f"{timestamp}_{unique_id}"

    # Open the PDF
    pdf_document = fitz.open(pdf_path)

    # Extract text from all pages
    full_text = []
    image_paths = []
    image_positions = []
    image_counter = 0

    print(f"Processing PDF: {pdf_path.name}")
    print(f"Total pages: {len(pdf_document)}")

    # Iterate through each page
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]

        # Extract text from this page
        text = page.get_text()
        if text.strip():
            full_text.append(f"Page {page_num + 1}:\n{text}\n")

        # Extract images from this page
        image_list = page.get_images(full=True)

        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]

            # Get the image data
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Skip images under 1KB (likely tiny icons or decorative elements)
            image_size_kb = len(image_bytes) / 1024
            if image_size_kb < 1:
                print(f"  Skipping small image from page {page_num + 1} ({image_size_kb:.2f} KB)")
                continue

            # Get position of the image on the page
            try:
                image_rects = page.get_image_rects(xref)
                if image_rects:
                    # Take the first occurrence if image appears multiple times
                    rect = image_rects[0]

                    # Convert to top-based Y coordinate
                    # PyMuPDF uses bottom-left origin, web uses top-left
                    page_height = page.rect.height
                    y_from_top = page_height - rect.y1

                    # Calculate percentage from top of page (0-100%)
                    # This is resolution-independent and works with any rendered size
                    y_percentage = (y_from_top / page_height) * 100

                    # Store position data as percentage only
                    position_data = {
                        'page_number': page_num,  # 0-indexed
                        'y_percentage': y_percentage  # Percentage from top
                    }
                else:
                    # No position data available
                    position_data = None
            except Exception as e:
                print(f"  Warning: Could not get position for image on page {page_num + 1}: {e}")
                position_data = None

            # Create unique filename for this image
            image_filename = f"{file_prefix}_img_{image_counter:03d}.{image_ext}"
            image_path = output_path / image_filename

            # Save the image
            try:
                # For some formats, we might need to convert using PIL
                if image_ext in ['png', 'jpg', 'jpeg', 'webp']:
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                else:
                    # Convert to PNG using PIL for unusual formats
                    img = Image.open(io.BytesIO(image_bytes))
                    image_path = output_path / f"{file_prefix}_img_{image_counter:03d}.png"
                    img.save(image_path, "PNG")

                # Append just the filename, not the full path with volume/
                image_paths.append(image_filename)
                image_positions.append(position_data)
                image_counter += 1

                if position_data:
                    print(f"  Extracted image {image_counter} from page {page_num + 1}: {image_path.name} ({image_size_kb:.1f} KB) at {position_data['y_percentage']:.1f}% from top")
                else:
                    print(f"  Extracted image {image_counter} from page {page_num + 1}: {image_path.name} ({image_size_kb:.1f} KB)")

            except Exception as e:
                print(f"  Warning: Could not save image from page {page_num + 1}: {e}")

    pdf_document.close()

    # Save the extracted text to a file
    instructions_filename = f"{file_prefix}_manual.txt"
    instructions_path = output_path / instructions_filename

    with open(instructions_path, "w", encoding="utf-8") as text_file:
        text_file.write("\n".join(full_text))

    print(f"\nExtraction complete:")
    print(f"  Images extracted: {len(image_paths)}")
    print(f"  Images with position data: {sum(1 for p in image_positions if p is not None)}")
    print(f"  Text saved to: {instructions_path.name}")
    print(f"  Total characters: {len(''.join(full_text))}")

    # Return just filenames, not full paths
    return image_paths, instructions_filename, image_positions