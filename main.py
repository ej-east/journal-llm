from modules.logger import get_logger, setup_logging
from modules.videos.main import VideoProcessor
from modules.notion.main import NotionDB
from modules.AI.main import AI
from dotenv import load_dotenv
from pathlib import Path
from logging import INFO
import os, argparse

load_dotenv()

setup_logging(
    level=INFO,
)

logger = get_logger(__name__)

def load_argparse():
    parser = argparse.ArgumentParser(
        description='Process videos from YouTube URLs or local files, transcribe, summarize, and optionally save to Notion.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            %(prog)s --youtube "https://www.youtube.com/watch?v=VIDEO_ID"
            %(prog)s --local "/path/to/video.mp4"
            %(prog)s -y "https://youtu.be/VIDEO_ID"
            """
    )
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '-y', '--youtube',
        type=str,
        help='YouTube URL to process'
    )
    input_group.add_argument(
        '-l', '--local',
        type=str,
        help='Local video file path to process'
    )
    
    return parser.parse_args()

def validate_local_file(filepath :str) -> bool:
    file = Path(filepath)
    if not file.exists():
        logger.error("File not found")
        return False
    if not file.is_file():
        logger.error(f"Path is not a file")
        return False
    return True

def main() -> None:
    args = load_argparse()
    using_notion = True
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not gemini_api_key:
        logger.error("Gemini key not found")
        return
    
    using_notion = notion_api_key and notion_database_id
    
    if not using_notion:
        logger.info("Not using Notion as database...")
    
    videos = VideoProcessor()
    ai = AI(api_key=gemini_api_key)
    
    if notion_api_key and notion_database_id and using_notion:
        notion = NotionDB(api_key=notion_api_key, database_id=notion_database_id)

    if args.youtube and videos.is_valid_url(args.youtube) and ("youtube" in args.youtube):
        video_path = videos.download_video(url=args.youtube)
        if not video_path:
            logger.error("YouTube download failed")
            return
    elif args.local:
        video_path = args.local
        if not validate_local_file(video_path):
            logger.error("Could not validate local file")
            return
    
    audio_path = videos.extract_audio(video_path)
    
    if not audio_path:
        logger.error("Could not convert file to audio")
        return
    
    transcription = ai.transcribe_audio(audio_path)
    if not transcription:
        logger.error("Could not transcribe")
        return
    
    llm_output = ai.get_llm_summary(transcription)
    
    if not llm_output:
        logger.error("Could not generate LLM Output")
        return
    
    if notion_api_key and notion_database_id and using_notion:
        notion.add_entry(
            title=llm_output["title"],
            summary=llm_output["summary"],
            key_points=llm_output["key_points"],
            action_items=llm_output["action_items"]
        )
    else:
        print("\n" + "="*50)
        print(f"TITLE: {llm_output['title']}")
        print("="*50)
        print(f"\nSUMMARY:\n{llm_output['summary']}")
        print("\nKEY POINTS:")
        for point in llm_output['key_points']:
            print(f"  • {point}")
        print("\nACTION ITEMS:")
        for item in llm_output['action_items']:
            print(f"  □ {item}")
        print("="*50 + "\n")
    
    if bool(os.getenv("DELETE_UNEEDED_FILES")):
        logger.info("Cleaning up uneeded files...")
        os.remove(video_path)
        os.remove(audio_path)
    logger.info("Successfully ran program...")
        
    

if __name__ == "__main__":
    main()