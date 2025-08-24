from dotenv import load_dotenv
from modules.AI.main import AI
from modules.videos.main import VideoProccesser
from modules.notion.main import NotionDB
import os

load_dotenv()

URL = r"https://www.youtube.com/watch?v=DIeP3Y5VdV8&pp=ygUHYXdzIHNhYQ%3D%3D"


def main() -> None:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not gemini_api_key:
        return
    
    if not notion_api_key or not notion_database_id:
        return
    
    
    videos = VideoProccesser()
    ai = AI(api_key=gemini_api_key)
    notion = NotionDB(api_key=notion_api_key, database_id=notion_database_id)
        
    video_path = videos.download_video(url=URL)
    if not video_path:
        return
    
    audio_path = videos.extract_audio(video_path)
    
    if not audio_path:
        return
    
    transcription = ai.transcribe_audio(audio_path)
    if not transcription:
        return
    
    llm_output = ai.get_llm_summary(transcription)
    
    if not llm_output:
        return
    
    notion.add_entry(
        title=llm_output["title"],
        summary=llm_output["summary"],
        key_points=llm_output["key_points"],
        action_items=llm_output["action_items"]
    )
    

if __name__ == "__main__":
    main()