#!/usr/bin/env python3
"""
Gemini service for processing manual images and instructions.
Analyzes images to determine if they're instructional and matches them with manual text.
"""

import os
import json
import subprocess
import google.generativeai as genai
from pathlib import Path
from PIL import Image
import io
from typing import List, Dict, Any


def batch_resize_images_ffmpeg(image_paths: List[Path], volume_dir: Path, max_size_mb: int = 1) -> List[Path]:
    """
    Batch resize images using ffmpeg for better performance.

    Args:
        image_paths: List of image paths to resize
        volume_dir: Directory where images are stored
        max_size_mb: Maximum file size in megabytes

    Returns:
        List of paths to resized images (temp files or originals)
    """
    temp_files = []
    processed_paths = []

    for img_path in image_paths:
        file_size = os.path.getsize(img_path)
        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size <= max_size_bytes:
            processed_paths.append(img_path)
            continue

        # Create temp output path
        temp_path = volume_dir / f"temp_{img_path.stem}.jpg"
        
        # Use ffmpeg to resize - much faster than PIL
        # Start with quality 85, adjust if needed
        quality = 85
        subprocess.run(
            [
                'ffmpeg', '-y', '-i', str(img_path),
                '-q:v', str(quality),
                '-vf', 'scale=iw:ih',
                str(temp_path)
            ],
            capture_output=True,
            check=True
        )

        # Check if still too large, reduce quality further
        temp_size = os.path.getsize(temp_path)
        if temp_size > max_size_bytes:
            # Reduce quality more aggressively
            quality = 60
            subprocess.run(
                [
                    'ffmpeg', '-y', '-i', str(img_path),
                    '-q:v', str(quality),
                    '-vf', 'scale=iw*0.8:ih*0.8',
                    str(temp_path)
                ],
                capture_output=True,
                check=True
            )

        temp_files.append(temp_path)
        processed_paths.append(temp_path)
        print(f"  Resized with ffmpeg: {img_path.name} -> {os.path.getsize(temp_path) / 1024:.1f}KB")

    return processed_paths, temp_files

def process_manual_images(
    image_filenames: List[str],
    instructions_filename: str,
    volume_dir: str = "volume"
) -> Dict[str, Any]:
    """
    Process manual images with Gemini to identify instructional content.

    Args:
        image_filenames: List of image filenames (without volume/ prefix)
        instructions_filename: Instructions text filename (without volume/ prefix)
        volume_dir: Directory where files are stored (default: "volume")

    Returns:
        Dictionary containing the parsed results from Gemini

    Raises:
        ValueError: If GEMINI_API_KEY is not set
        FileNotFoundError: If any image or instructions file is not found
    """
    # Configure Gemini API
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY environment variable")

    genai.configure(api_key=api_key)

    # Initialize the model
    model = genai.GenerativeModel('gemini-3-pro-preview')

    # Construct full paths
    volume_path = Path(volume_dir)
    instructions_path = volume_path / instructions_filename

    # Read instructions
    if not instructions_path.exists():
        raise FileNotFoundError(f"Instructions file not found: {instructions_path}")

    with open(instructions_path, "r", encoding="utf-8") as f:
        instructions_text = f.read()

    print(f"\nProcessing {len(image_filenames)} images...")

    # Build full paths
    image_paths = []
    for img_filename in image_filenames:
        img_path = volume_path / img_filename
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")
        image_paths.append(img_path)

    # Batch resize with ffmpeg (much faster)
    processed_paths, temp_files = batch_resize_images_ffmpeg(image_paths, volume_path, max_size_mb=1)

    # Load images directly (much faster than upload_file)
    print(f"\nLoading {len(processed_paths)} images...")
    images = []
    for processed_path in processed_paths:
        # Open image with PIL and pass directly to Gemini
        img = Image.open(processed_path)
        images.append(img)

    # Create the prompt
    prompt = f"""You are given images extracted from a service manual PDF.
When PDFs are parsed, ALL images are extracted, including both useful instructional images and non-instructional images.

NON-INSTRUCTIONAL images include:
- Icons and symbols (warning icons, info icons, lightbulb icons, etc.)
- Individual screws or small components shown in isolation
- Decorative elements
- Simple diagrams showing only screw types or part numbers
- Header/footer graphics
- Logos or branding elements

INSTRUCTIONAL images include:
- Step-by-step assembly/disassembly photos showing hands or tools
- Diagrams showing where components are located in the computer
- Before/after comparison images
- Annotated photos showing specific parts to remove/install
- Multi-step procedure illustrations

Here are the instructions from the manual:
{instructions_text}

Your task is to:
1. Analyze each image in the order they were provided
2. Determine if the image is an actual instruction (step-by-step photo or useful diagram) or just a non-instructional graphic (icon, logo, isolated component)
3. For instructional images, identify which specific instruction or procedure it corresponds to and provide a clear description
4. For non-instructional images, mark is_instruction as false and use N/A for all other fields

Please output your response as a valid JSON object. For each image provided, add one entry to the matches array.
{{
  "matches": [
    {{
      "image_index": 0,
      "is_instruction": true/false,
      "instruction_title": "Title or name of the instruction, or N/A if not an instruction",
      "instruction_description": "Clear, user-friendly description of what to do in this step (2-3 sentences, suitable for text-to-speech). For non-instructional images, use N/A.",
      "instruction_reference": "Line numbers or section reference from the manual, or N/A if not an instruction",
      "confidence": "high/medium/low",
      "reasoning": "Brief explanation of why this is or isn't an instructional image"
    }},
    ... (one entry per image)
  ]
}}

Guidelines for instruction_description:
- Write in clear, simple language suitable for audio playback
- Use second person (e.g., "Remove the screw..." not "The screw is removed...")
- Be specific about what action to take
- Include relevant safety warnings if visible in the image
- Keep it concise (2-3 sentences maximum)
- For non-instructional images, just use "N/A"
Example: "Remove the M2x3.5 screw that secures the solid-state drive to the system board. Slide the drive out at a 45-degree angle from the connector. Be careful not to touch the gold contacts on the drive."

Only return the JSON object, no additional text."""

    # Prepare content with images
    content = [prompt]
    for i, img in enumerate(images):
        content.append(f"\n\nImage {i+1}:")
        content.append(img)

    print("\n" + "=" * 80)
    print("Sending request to Gemini API...")
    print(f"Images: {len(images)}")
    print(f"Instructions length: {len(instructions_text)} characters")
    print("=" * 80 + "\n")

    try:
        # Generate response
        print("Calling model.generate_content()...")
        print(f"Content parts: {len(content)} (1 prompt + {len(images)} images)")
        response = model.generate_content(content)
        print("Response received!")

        # Parse the response
        print("Parsing response text...")
        response_text = response.text.strip()
        print(f"Response length: {len(response_text)} characters")

        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        result = json.loads(response_text.strip())

        print("\n" + "=" * 80)
        print("PROCESSING COMPLETE")
        print("=" * 80)
        print(f"Total images analyzed: {len(result.get('matches', []))}")
        instructional_count = sum(1 for m in result.get('matches', []) if m.get('is_instruction'))
        print(f"Instructional images found: {instructional_count}")
        print(f"Non-instructional images: {len(result.get('matches', [])) - instructional_count}")

        return result

    except json.JSONDecodeError as e:
        print(f"\nError: Could not parse Gemini response as JSON: {e}")
        print(f"Raw response: {response.text}")
        raise

    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()
                print(f"Cleaned up temp file: {temp_file.name}")
