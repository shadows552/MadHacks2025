import sqlite3
import hashlib

con = sqlite3.connect('/.tmp/instructions.db')

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

def store_gemini_results(
    pdf_path: str,
    pdf_filename: str,
    instructions_filename: str,
    image_filenames: list,
    gemini_results: dict
) -> bytes:
    """
    Store Gemini processing results in database.
    Only stores instructional images with sequential step numbers (0 to N, no gaps).

    Args:
        pdf_path: Full path to PDF file (for hash calculation)
        pdf_filename: PDF filename (without volume/)
        instructions_filename: Instructions text filename (without volume/)
        image_filenames: List of all image filenames
        gemini_results: Results from Gemini processing

    Returns:
        PDF hash as bytes
    """
    # Calculate hash from the actual file
    pdf_hash_bytes = calculate_pdf_hash(pdf_path)

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

    # Create instruction file with titles and descriptions (newline separated)
    # Filter only instructional images and store with sequential step numbers
    step_number = 0
    titles = []
    descriptions = []

    for match in gemini_results.get("matches", []):
        if not match.get("is_instruction"):
            continue  # Skip non-instructional images

        titles.append(match["instruction_title"])
        descriptions.append(match["instruction_description"])

        image_index = match["image_index"]
        image_filename = image_filenames[image_index]

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
            image_filename,
            None,  # glb added later
            None,  # mp3 added later
            instructions_filename
        ))

        step_number += 1

    con.commit()

    # Write titles and descriptions to instruction file
    instruction_content = "\n".join(titles) + "\n\n" + "\n".join(descriptions)
    instruction_path = Path("volume") / instructions_filename
    with open(instruction_path, "w", encoding="utf-8") as f:
        f.write(instruction_content)

    print(f"\nStored in database:")
    print(f"  PDF Hash: {pdf_hash_bytes.hex()[:16]}...")
    print(f"  PDF Filename: {pdf_filename}")
    print(f"  Steps: {step_number} (0 to {step_number - 1})")

    return pdf_hash_bytes

init_db()

con.close()
