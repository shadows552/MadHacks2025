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
            page_number INTEGER,
            y_percentage REAL,  -- Percentage (0-100%) from top of page

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
    gemini_results: dict,
    image_positions: list = None
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
        image_positions: Optional list of image position data with page_number and y_percentage

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

        # Get position data for this image if available
        position_data = None
        if image_positions and image_index < len(image_positions):
            position_data = image_positions[image_index]

        # Insert row for this step
        con.execute('''
            INSERT INTO instructions (
                hash,
                pdf_filename,
                step,
                image_filename,
                glb_filename,
                mp3_filename,
                instruction_filename,
                page_number,
                y_percentage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pdf_hash_bytes,
            pdf_filename,
            step_number,
            new_image_filename,
            None,  # glb added later
            None,  # mp3 added later
            instruction_filename,
            position_data.get('page_number') if position_data else None,
            position_data.get('y_percentage') if position_data else None
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

def get_all_pdfs() -> list:
    """
    Get all unique PDFs in the database.

    Returns:
        List of tuples (hash_hex, pdf_filename, step_count)
    """
    cursor = con.execute('''
        SELECT hash, pdf_filename, COUNT(*) as step_count
        FROM instructions
        GROUP BY hash, pdf_filename
        ORDER BY MAX(rowid) DESC
    ''')

    results = []
    for row in cursor.fetchall():
        hash_bytes, pdf_filename, step_count = row
        hash_hex = hash_bytes.hex()[:16]
        results.append((hash_hex, pdf_filename, step_count))

    return results

def get_pdf_filename_by_hash(hash_hex: str) -> str:
    """
    Get PDF filename by hash.

    Args:
        hash_hex: First 16 chars of PDF hash

    Returns:
        PDF filename or None if not found
    """
    # Convert hex string back to bytes (with full hash)
    # We only stored first 16 chars as hex, so we need to match with LIKE
    cursor = con.execute(
        'SELECT pdf_filename FROM instructions WHERE hex(hash) LIKE ? LIMIT 1',
        (hash_hex.upper() + '%',)
    )
    result = cursor.fetchone()
    return result[0] if result else None

def get_file_info_by_hash_step(hash_hex: str, step: int) -> dict:
    """
    Get all file information for a specific hash and step.

    Args:
        hash_hex: First 16 chars of PDF hash
        step: Step number

    Returns:
        Dictionary with filenames or None if not found
    """
    cursor = con.execute(
        '''SELECT image_filename, glb_filename, mp3_filename, instruction_filename
           FROM instructions
           WHERE hex(hash) LIKE ? AND step = ?''',
        (hash_hex.upper() + '%', step)
    )
    result = cursor.fetchone()

    if not result:
        return None

    return {
        'image_filename': result[0],
        'glb_filename': result[1],
        'mp3_filename': result[2],
        'instruction_filename': result[3]
    }

def get_step_position(hash_hex: str, step: int) -> dict:
    """
    Get page number and Y-percentage for a specific step.

    Args:
        hash_hex: First 16 chars of PDF hash
        step: Step number

    Returns:
        Dictionary with position data (page_number, y_percentage) or None if not found
    """
    cursor = con.execute(
        '''SELECT page_number, y_percentage
           FROM instructions WHERE hex(hash) LIKE ? AND step = ?''',
        (hash_hex.upper() + '%', step)
    )
    result = cursor.fetchone()
    if not result:
        return None

    return {
        'page_number': result[0],
        'y_percentage': result[1]
    }
