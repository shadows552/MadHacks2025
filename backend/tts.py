import aiohttp
import os

API_URL = "https://api.fish.audio/v1/tts"


async def tts(text, pdf_hash_hex, step_number, output_dir="volume", voice_id="zh_CN-female-1"):
    api_key = os.getenv("FISH_AUDIO_API_KEY")
    if not api_key:
        raise ValueError("FISH_AUDIO_API_KEY environment variable is not set")

    # output format: <hash>-<step>.mp3
    output_filename = f"{pdf_hash_hex}-{step_number}.mp3"
    output_file = f"{output_dir}/{output_filename}"

    payload = {
        "text": text,
        "model": "fish-speech-1",
        "voice": voice_id,
        "format": "mp3"
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                error_text_lower = error_text.lower()
                if "voice" in error_text_lower:
                    raise ValueError(f"Invalid voice ID: {voice_id}")
                raise RuntimeError(
                    f"API Error ({response.status}): {error_text}"
                )

            # Write output MP3
            content = await response.read()
            with open(output_file, "wb") as f:
                f.write(content)

    print(f"Audio saved to {output_file}")
    return output_filename


async def tts_from_file(input_text_file, pdf_hash_hex, step_number, output_dir="volume", voice_id="zh_CN-female-1"):
    with open(input_text_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    return await tts(text, pdf_hash_hex, step_number, output_dir, voice_id)
