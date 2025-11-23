import sqlite3
import hashlib
from pathlib import Path

con = sqlite3.connect('./volume/instructions.db')

def init_db():
    con.execute('''
        CREATE TABLE IF NOT EXISTS instructions (
            hash BLOB,
            pdf_filename TEXT,
            step INTEGER,
            image_filename TEXT,
            glb_filename TEXT,
            mp3_filename TEXT,
            instruction_filename TEXT,

            PRIMARY KEY (hash, step)
        )
    ''')
    con.commit()

def calculate_pdf_hash(file_path: str) -> bytes:
    """Reads a file in chunks and returns its SHA-256 hash as raw bytes."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in 4K chunks to be memory efficient with large PDFs
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.digest() # Returns binary (bytes)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return b''

def store_gemini_results(
    pdf_hash_bytes: bytes,
    pdf_filename: str,
    image_filenames: list,
    gemini_results: dict
) -> bytes:
    """
    Store Gemini processing results in database.
    Only stores instructional images with sequential step numbers (0 to N, no gaps).
    Creates a separate instruction text file for each step.

    Args:
        pdf_hash_bytes: PDF hash as bytes
        pdf_filename: PDF filename (without volume/)
        image_filenames: List of all image filenames
        gemini_results: Results from Gemini processing

    Returns:
        PDF hash as bytes
    """

    if not pdf_hash_bytes:
        return b''

    # Check if this PDF already exists
    cursor = con.execute(
        'SELECT COUNT(*) FROM instructions WHERE hash = ?',
        (pdf_hash_bytes,)
    )
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        print(f"\nPDF already in database (Hash: {pdf_hash_bytes.hex()[:8]}...)")
        print(f"Skipping {existing_count} existing steps.")
        return pdf_hash_bytes

    # Filter only instructional images and store with sequential step numbers
    step_number = 0
    volume_dir = Path("volume")
    hash_hex = pdf_hash_bytes.hex()[:16]  # Use first 16 chars of hash

    for match in gemini_results.get("matches", []):
        if not match.get("is_instruction"):
            continue  # Skip non-instructional images

        title = match["instruction_title"]
        description = match["instruction_description"]

        image_index = match["image_index"]
        old_image_filename = image_filenames[image_index]

        # Get original image extension
        image_ext = Path(old_image_filename).suffix

        # Create new filenames using hash-step pattern
        new_image_filename = f"{hash_hex}-{step_number}{image_ext}"
        instruction_filename = f"{hash_hex}-{step_number}.txt"

        # Copy/rename image file to new naming scheme
        old_image_path = volume_dir / old_image_filename
        new_image_path = volume_dir / new_image_filename

        if old_image_path.exists():
            import shutil
            shutil.copy2(old_image_path, new_image_path)

        # Create instruction file for this step (title\n\ndescription)
        instruction_path = volume_dir / instruction_filename

        with open(instruction_path, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n{description}")

        # Insert row for this step
        con.execute('''
            INSERT INTO instructions (
                hash,
                pdf_filename,
                step,
                image_filename,
                glb_filename,
                mp3_filename,
                instruction_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            pdf_hash_bytes,
            pdf_filename,
            step_number,
            new_image_filename,
            None,  # glb added later
            None,  # mp3 added later
            instruction_filename
        ))

        step_number += 1

    con.commit()

    print(f"\nStored in database:")
    print(f"  PDF Hash: {pdf_hash_bytes.hex()[:16]}...")
    print(f"  PDF Filename: {pdf_filename}")
    print(f"  Steps: {step_number} (0 to {step_number - 1})")

    return pdf_hash_bytes

def get_instructions_by_hash(pdf_hash_bytes: bytes) -> list:
    """
    Get all instructions for a given PDF hash.

    Args:
        pdf_hash_bytes: PDF hash

    Returns:
        List of tuples (step, instruction_filename)
    """
    cursor = con.execute(
        'SELECT step, instruction_filename FROM instructions WHERE hash = ? ORDER BY step',
        (pdf_hash_bytes,)
    )
    return cursor.fetchall()

def update_mp3_filename(pdf_hash_bytes: bytes, step: int, mp3_filename: str):
    """
    Update the MP3 filename for a specific instruction in the database.

    Args:
        pdf_hash_bytes: PDF hash
        step: Step number
        mp3_filename: MP3 filename (without volume/)
    """
    con.execute(
        'UPDATE instructions SET mp3_filename = ? WHERE hash = ? AND step = ?',
        (mp3_filename, pdf_hash_bytes, step)
    )
    con.commit()

def update_glb_filename(pdf_hash_bytes: bytes, step: int, glb_filename: str):
    """
    Update the GLB filename for a specific instruction in the database.

    Args:
        pdf_hash_bytes: PDF hash
        step: Step number
        glb_filename: GLB filename (without volume/)
    """
    con.execute(
        'UPDATE instructions SET glb_filename = ? WHERE hash = ? AND step = ?',
        (glb_filename, pdf_hash_bytes, step)
    )
    con.commit()

def get_instructions_with_images(pdf_hash_bytes: bytes) -> list:
    """
    Get all instructions with their image filenames for a given PDF hash.

    Args:
        pdf_hash_bytes: PDF hash

    Returns:
        List of tuples (step, image_filename)
    """
    cursor = con.execute(
        'SELECT step, image_filename FROM instructions WHERE hash = ? ORDER BY step',
        (pdf_hash_bytes,)
    )
    return cursor.fetchall()
