from dotenv import load_dotenv
from modules.AI.main import AI
from modules.videos.main import VideoProccesser
import os

load_dotenv()

URL = r"https://www.youtube.com/watch?v=OIenNRt2bjg"

def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return
    
    videos = VideoProccesser()
    ai = AI(api_key=api_key)
    
    video_path = videos.download_video(url=URL)
    if not video_path:
        return
    
    audio_path = videos.extract_audio(video_path)
    
    if not audio_path:
        return
    
    transcription = ai.transcribe_audio(audio_path)
    if not transcription:
        return
    
    summary = ai.get_llm_summary(transcription)
    
    print(summary)


if __name__ == "__main__":
    main()