from tts import tts

def test_basic():
    print("Running basic TTS test...")

    try:
        output_file = tts("This is a test message.", voice_id="en_US-female-1", output_file="test_output.wav")
        print("TTS generated successfully:", output_file)
    except Exception as e:
        print("❌ Test failed:", e)


if __name__ == "__main__":
    test_basic()
