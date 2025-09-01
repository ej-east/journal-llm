from modules.logger import get_logger, setup_logging
from modules.videos.main import VideoProcessor
from modules.notion.main import NotionDB
from modules.AI.main import AI
from modules.exceptions import (
    JournalLLMError,
    VideoProcessingError,
    InvalidURLError,
    AIProcessingError,
    NotionIntegrationError,
    InvalidAPIKeyError
)
from dotenv import load_dotenv
from pathlib import Path
from logging import INFO
import os, argparse, sys

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
    
    input_group.add_argument(
        '-u', '--url',
        type=str,
        help='Remote video URL to process'
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
    video_path = None
    audio_path = None
    
    try:
        # Load environment variables
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        notion_api_key = os.getenv("NOTION_API_KEY")
        notion_database_id = os.getenv("NOTION_DATABASE_ID")
        
        if not gemini_api_key:
            logger.error("GEMINI_API_KEY environment variable not found. Please set it in your .env file.")
            sys.exit(1)
        
        using_notion = bool(notion_api_key and notion_database_id)
        
        if not using_notion:
            logger.info("Notion integration disabled (API key or database ID not configured)")
        
        # Initialize modules
        try:
            videos = VideoProcessor()
        except Exception as e:
            logger.error(f"Failed to initialize VideoProcessor: {str(e)}")
            sys.exit(1)
        
        try:
            ai = AI(api_key=gemini_api_key)
        except InvalidAPIKeyError as e:
            logger.error(f"Invalid Gemini API key: {str(e)}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize AI module: {str(e)}")
            sys.exit(1)
        
        notion = None
        if using_notion:
            try:
                notion = NotionDB(api_key=notion_api_key, database_id=notion_database_id)
            except NotionIntegrationError as e:
                logger.error(f"Failed to initialize Notion integration: {str(e)}")
                logger.info("Continuing without Notion integration...")
                using_notion = False
                notion = None

        # Process video input
        if args.youtube:
            if not videos.is_valid_url(args.youtube):
                logger.error(f"Invalid or unreachable URL: {args.youtube}")
                sys.exit(1)
            if "youtube" not in args.youtube.lower() and "youtu.be" not in args.youtube.lower():
                logger.error(f"URL does not appear to be a YouTube URL: {args.youtube}")
                sys.exit(1)
            
            try:
                video_path = videos.download_youtube_video(url=args.youtube)
            except VideoProcessingError as e:
                logger.error(f"YouTube download failed: {str(e)}")
                sys.exit(1)
        elif args.local:
            video_path = args.local
            if not validate_local_file(video_path):
                logger.error(f"Invalid local file: {video_path}")
                sys.exit(1)
        elif args.url:
            if not videos.is_valid_url(args.url):
                logger.error(f"Invalid or unreachable URL: {args.url}")
                sys.exit(1)
            
            try:
                video_path = videos.download_video(args.url)
            except VideoProcessingError as e:
                logger.error(f"Video download failed: {str(e)}")
                sys.exit(1)

        else:
            logger.error("No valid input provided. Use --youtube, --local, or --url")
            sys.exit(1)
        
        # Extract audio from video
        try:
            audio_path = videos.extract_audio(video_path)
        except VideoProcessingError as e:
            logger.error(f"Audio extraction failed: {str(e)}")
            sys.exit(1)
        
        # Transcribe audio
        try:
            transcription = ai.transcribe_audio(audio_path)
            logger.info(f"Transcription completed: {len(transcription)} characters")
        except AIProcessingError as e:
            logger.error(f"Transcription failed: {str(e)}")
            sys.exit(1)
        
        # Generate summary
        try:
            llm_output = ai.get_llm_summary(transcription)
            logger.info("Summary generated successfully")
        except AIProcessingError as e:
            logger.error(f"Summary generation failed: {str(e)}")
            sys.exit(1)
        
        # Save to Notion or display results
        if notion and using_notion:
            try:
                page_id = notion.add_entry(
                    title=llm_output["title"],
                    summary=llm_output["summary"],
                    key_points=llm_output["key_points"],
                    action_items=llm_output["action_items"]
                )
                logger.info(f"Results saved to Notion (Page ID: {page_id})")
            except NotionIntegrationError as e:
                logger.error(f"Failed to save to Notion: {str(e)}")
                logger.info("Displaying results to console instead...")
                display_results(llm_output)
        else:
            display_results(llm_output)
    
    except JournalLLMError as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup temporary files if configured
        if bool(os.getenv("DELETE_UNNEEDED_FILES")):
            logger.info("Cleaning up temporary files...")
            try:
                if video_path and os.path.exists(video_path):
                    os.remove(video_path)
                    logger.info(f"Removed video file: {video_path}")
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
                    logger.info(f"Removed audio file: {audio_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up some files: {str(e)}")
        
        logger.info("Program completed successfully")


def display_results(llm_output: dict) -> None:
    """Display the summarized results to console."""
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
        
    

if __name__ == "__main__":
    main()