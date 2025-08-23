from dotenv import load_dotenv
from modules.AI.main import AI
import os

load_dotenv()

def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return
    
    ai = AI(api_key=api_key)
    transcription = ai.transcribe_audio("voice.wav")
    if not transcription:
        return
    
    summary = ai.get_llm_summary(transcription)
    
    print(summary)


if __name__ == "__main__":
    main()