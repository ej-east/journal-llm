from dotenv import load_dotenv
from modules.AI.main import AI
from modules.videos.main import VideoProccesser
from modules.notion.main import NotionDB
import os, logging, argparse

load_dotenv()

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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
    if not os.path.exists(filepath):
        logger.error("File not found")
        return False
    if not os.path.isfile(filepath):
        logger.error(f"Path is not a file")
        return False
    if not os.access(filepath, os.R_OK):
        logger.error(f"File is not readable")
        return False
    return True

def main() -> None:
    args = load_argparse()
    using_notion = True
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not gemini_api_key:
        return
    
    using_notion = notion_api_key and notion_database_id
    
    
    videos = VideoProccesser()
    ai = AI(api_key=gemini_api_key)
    
    if notion_api_key and notion_database_id and using_notion:
        notion = NotionDB(api_key=notion_api_key, database_id=notion_database_id)

    if args.youtube:
        video_path = videos.download_video(url=args.youtube)
        if not video_path:
            return
    elif args.local:
        video_path = args.local
        if not validate_local_file(video_path):
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
    
    logger.info("Cleaning up uneeded files...")
    os.remove(video_path)
    os.remove(audio_path)
    logger.info("Successfully ran program...")
        
    

if __name__ == "__main__":
    main()