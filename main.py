from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print
from modules.logger import get_logger, setup_logging
from modules.config import Config, ConfigurationError
from modules.formatters import FormatterFactory
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

from pathlib import Path
from logging import INFO, WARNING
from typing import Optional
import os, argparse, sys

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
    
    # Output format options
    parser.add_argument(
        '--output-format',
        type=str,
        choices=['plain', 'markdown', 'json'],
        default='plain',
        help='Output format for the summary (default: plain)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        metavar='FILE',
        help='Save output to file instead of displaying'
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
        # Load and validate configuration
        try:
            config = Config.from_env()
            logger.debug(f"Configuration loaded: {config.summary()}")
        except ConfigurationError as e:
            logger.error(f"Configuration error: {str(e)}")
            sys.exit(1)
        except InvalidAPIKeyError as e:
            logger.error(f"API key error: {str(e)}")
            logger.error("Please check your .env file")
            sys.exit(1)
        
        setup_logging(level=config.ui.log_level)
        
        # Initialize modules with configuration
        try:
            videos = VideoProcessor(
                video_output_dir=config.video.video_output_dir,
                audio_output_dir=config.video.audio_output_dir
            )
        except Exception as e:
            logger.error(f"Failed to initialize VideoProcessor: {str(e)}")
            sys.exit(1)
        
        try:
            ai = AI(api_key=config.ai.gemini_api_key)
        except InvalidAPIKeyError as e:
            logger.error(f"Invalid Gemini API key: {str(e)}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize AI module: {str(e)}")
            sys.exit(1)
        
        notion = None
        if config.notion.enabled:
            try:
                notion = NotionDB(
                    api_key=config.notion.api_key,
                    database_id=config.notion.database_id
                )
            except NotionIntegrationError as e:
                logger.error(f"Failed to initialize Notion integration: {str(e)}")
                logger.info("Continuing without Notion integration...")
                config.notion.enabled = False
                notion = None
        with Progress(
        SpinnerColumn(spinner_name=config.ui.spinner_style, style=config.ui.spinner_color),
        TextColumn(f"[{config.ui.text_color}]{{task.description}}"), ) as progress:
            
            task = progress.add_task("Starting...", total=None)

            # Process video input
            if args.youtube:
                if not videos.is_valid_url(args.youtube):
                    logger.error(f"Invalid or unreachable URL: {args.youtube}")
                    sys.exit(1)
                if "youtube" not in args.youtube.lower() and "youtu.be" not in args.youtube.lower():
                    logger.error(f"URL does not appear to be a YouTube URL: {args.youtube}")
                    sys.exit(1)
                
                try:
                    progress.update(task, description="Grabbing YouTube video")
                    video_path = videos.download_youtube_video(url=args.youtube)
                except VideoProcessingError as e:
                    logger.error(f"YouTube download failed: {str(e)}")
                    sys.exit(1)
            elif args.local:
                progress.update(task, description="Loading Local Video")
                video_path = args.local
                if not validate_local_file(video_path):
                    logger.error(f"Invalid local file: {video_path}")
                    sys.exit(1)
            elif args.url:
                if not videos.is_valid_url(args.url):
                    logger.error(f"Invalid or unreachable URL: {args.url}")
                    sys.exit(1)
                
                try:
                    progress.update(task, description="Fetching remote video")
                    video_path = videos.download_video(args.url)
                except VideoProcessingError as e:
                    logger.error(f"Video download failed: {str(e)}")
                    sys.exit(1)

            else:
                logger.error("No valid input provided. Use --youtube, --local, or --url")
                sys.exit(1)
        
            # Extract audio from video
            progress.update(task, description="Extracting audio from video")
            try:
                audio_path = videos.extract_audio(video_path)
            except VideoProcessingError as e:
                logger.error(f"Audio extraction failed: {str(e)}")
                sys.exit(1)
            
            # Transcribe audio
            progress.update(task, description="Transcribing audio")
            try:
                transcription = ai.transcribe_audio(audio_path)
                logger.info(f"Transcription completed: {len(transcription)} characters")
            except AIProcessingError as e:
                logger.error(f"Transcription failed: {str(e)}")
                sys.exit(1)
            
            # Generate summary
            progress.update(task, description="Generating Summary")
            try:
                llm_output = ai.get_llm_summary(transcription)
                logger.info("Summary generated successfully")
            except AIProcessingError as e:
                logger.error(f"Summary generation failed: {str(e)}")
                sys.exit(1)
            
            # Save to Notion or display/save results
            if notion and config.notion.enabled:
                progress.update(task, description="Adding results to Notion")
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
                    output_results(llm_output, args.output_format, args.output)
            else:
                output_results(llm_output, args.output_format, args.output)
        
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
        if config.video.delete_files_after:
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
    print("[green]Program ran successfully[/]")


def output_results(llm_output: dict, format_type: str, output_file: Optional[str] = None) -> None:
    """Output the summarized results in the specified format.
    
    Args:
        llm_output: Dictionary containing the summary data
        format_type: Output format ('plain', 'markdown', 'json')
        output_file: Optional file path to save the output
    """
    try:
        formatter = FormatterFactory.create(format_type)
        
        if output_file:
            # Save to file
            formatter.save_to_file(llm_output, output_file)
            print(f"[green]✓ Output saved to: {output_file}[/green]")
        else:
            # Display to console
            formatted_output = formatter.format(llm_output)
            print(formatted_output)
            
    except ValueError as e:
        logger.error(f"Invalid output format: {str(e)}")
        # Fallback to plain text
        formatter = FormatterFactory.create('plain')
        print(formatter.format(llm_output))
    except IOError as e:
        logger.error(f"Failed to save output: {str(e)}")
        # Fallback to console display
        formatter = FormatterFactory.create(format_type)
        print(formatter.format(llm_output))


def display_results(llm_output: dict) -> None:
    """Legacy function for displaying results in plain text."""
    output_results(llm_output, 'plain', None)
        
    

if __name__ == "__main__":
    main()