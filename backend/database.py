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
        CREATE TABLE IF NOT EXISTS database (
            hash BLOB,
            pdf_filename TEXT,
            step INTEGER,
            glb_filename TEXT,
            mp3_filename TEXT,
            instruction_filename TEXT,

            PRIMARY KEY (pdf_hash, step)
        )
    ''')
    con.commit()

def add_pdf_step(pdf_path: str, step: int, model_filename: str, voice_filename: str, instruction_filename: str):
    # 1. Calculate hash from the actual file
    pdf_hash_bytes = calculate_pdf_hash(pdf_path)
    
    if not pdf_hash_bytes:
        return # Stop if file not found

    # 2. Insert the bytes directly into the BLOB column
    # Note: We still store pdf_path as text for human reference, but it's not the PK
    con.execute('''
        INSERT INTO database (hash, pdf_filename, step, glb_filename, mp3_filename, instruction_filename)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (hash, pdf_filename, step, glb_filename, mp3_filename, instruction_filename))
    
    con.commit()
    print(f"Added step {step} for PDF (Hash: {pdf_hash_bytes.hex()[:8]}...)")

init_db()

con.close()
