from dotenv import load_dotenv
from modules.AI.main import AI
from modules.videos.main import VideoProccesser
import os

load_dotenv()

URL = r"https://www.youtube.com/watch?v=OIenNRt2bjg"

def formatted_print(llm_output : dict) -> bool:
    try:
        title = llm_output["title"]
        summary = llm_output["summary"]
        key_points = llm_output["key_points"]
        action_items = llm_output["action_items"]
        print(f"# {title}")
        print(f"## Summary\n{summary}")
        
        print()
        
        print(f"## Key Points")
        for point in key_points:
            print(f"- {point}")
        
        print()
                
        print(f"## Key Points")
        
        for action in action_items:
            print(f"- {action}")
        
        
    except Exception as e:
        print("[-] Failed to print final output")
        return False    
    return True



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
    
    if not summary:
        return
    
    formatted_print(summary)


if __name__ == "__main__":
    main()