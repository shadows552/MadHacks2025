import requests
from secret import API_KEY

API_URL = "https://api.fish.audio/v1/tts"

def tts(text, voice_id="zh_CN-female-1", output_file="output.wav"):
    if not API_KEY:
        raise ValueError("API key is missing in secret.py")

    payload = {
        "text": text,
        "model": "fish-speech-1",
        "voice": voice_id,
        "format": "wav"
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(API_URL, json=payload, headers=headers)

    if response.status_code != 200:
        error_text = response.text.lower()
        if "voice" in error_text:
            raise ValueError(f"Invalid voice ID: {voice_id}")
        raise RuntimeError(f"API Error ({response.status_code}): {response.text}")

    with open(output_file, "wb") as f:
        f.write(response.content)

    print(f"Audio saved to {output_file}")
    return output_file


def tts_from_file(input_file, voice_id="zh_CN-female-1", output_file="output.wav"):
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    return tts(text, voice_id=voice_id, output_file=output_file)
