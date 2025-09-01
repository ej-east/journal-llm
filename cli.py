#!/usr/bin/env python3
"""Command-line interface for Journal LLM."""

import argparse
import sys
from pathlib import Path
from typing import Optional
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print
from logging import WARNING

from src.modules import (
    Config,
    ConfigurationError,
    get_logger,
    setup_logging,
    FormatterFactory,
    JournalLLMError,
    VideoProcessingError,
    AIProcessingError,
    NotionIntegrationError,
    InvalidAPIKeyError
)
from src.modules.videos import VideoProcessor
from src.modules.notion import NotionDB
from src.modules.AI import AI


logger = get_logger(__name__)


class JournalLLMCLI:
    """Command-line interface for Journal LLM application."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.config = None
        self.args = None
        
    def parse_arguments(self) -> argparse.Namespace:
        """Parse command-line arguments.
        
        Returns:
            Parsed arguments namespace
        """
        parser = argparse.ArgumentParser(
            description='Process videos from YouTube URLs or local files, transcribe, summarize, and optionally save to Notion.',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
                Examples:
                %(prog)s --youtube "https://www.youtube.com/watch?v=VIDEO_ID"
                %(prog)s --local "/path/to/video.mp4"
                %(prog)s -y "https://youtu.be/VIDEO_ID" --output-format markdown --output summary.md
                """
        )
        
        # Input source (mutually exclusive)
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
        
        # Verbose/debug options
        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--no-notion',
            action='store_true',
            help='Disable Notion integration even if configured'
        )
        
        return parser.parse_args()
    
    def load_configuration(self) -> Config:
        """Load and validate configuration.
        
        Returns:
            Validated configuration object
            
        Raises:
            SystemExit: If configuration is invalid
        """
        try:
            config = Config.from_env()
            logger.debug(f"Configuration loaded: {config.summary()}")
            return config
        except ConfigurationError as e:
            logger.error(f"Configuration error: {str(e)}")
            sys.exit(1)
        except InvalidAPIKeyError as e:
            logger.error(f"API key error: {str(e)}")
            logger.error("Please check your .env file")
            sys.exit(1)
    
    def validate_local_file(self, filepath: str) -> bool:
        """Validate that a local file exists and is accessible.
        
        Args:
            filepath: Path to the file
            
        Returns:
            True if file is valid, False otherwise
        """
        file = Path(filepath)
        if not file.exists():
            logger.error(f"File not found: {filepath}")
            return False
        if not file.is_file():
            logger.error(f"Path is not a file: {filepath}")
            return False
        return True
    
    def process_video_input(self, videos: VideoProcessor, progress, task) -> str:
        """Process the video input based on arguments.
        
        Args:
            videos: VideoProcessor instance
            progress: Rich progress instance
            task: Progress task ID
            
        Returns:
            Path to the video file
            
        Raises:
            SystemExit: If video processing fails
        """
        if self.args.youtube:
            if not videos.is_valid_url(self.args.youtube):
                logger.error(f"Invalid or unreachable URL: {self.args.youtube}")
                sys.exit(1)
            if "youtube" not in self.args.youtube.lower() and "youtu.be" not in self.args.youtube.lower():
                logger.error(f"URL does not appear to be a YouTube URL: {self.args.youtube}")
                sys.exit(1)
            
            try:
                progress.update(task, description="Grabbing YouTube video")
                return videos.download_youtube_video(url=self.args.youtube)
            except VideoProcessingError as e:
                logger.error(f"YouTube download failed: {str(e)}")
                sys.exit(1)
                
        elif self.args.local:
            progress.update(task, description="Loading Local Video")
            video_path = self.args.local
            if not self.validate_local_file(video_path):
                logger.error(f"Invalid local file: {video_path}")
                sys.exit(1)
            return video_path
            
        elif self.args.url:
            if not videos.is_valid_url(self.args.url):
                logger.error(f"Invalid or unreachable URL: {self.args.url}")
                sys.exit(1)
            
            try:
                progress.update(task, description="Fetching remote video")
                return videos.download_video(self.args.url)
            except VideoProcessingError as e:
                logger.error(f"Video download failed: {str(e)}")
                sys.exit(1)
        else:
            logger.error("No valid input provided. Use --youtube, --local, or --url")
            sys.exit(1)
    
    def output_results(self, llm_output: dict) -> None:
        """Output the results in the specified format.
        
        Args:
            llm_output: Dictionary containing the summary data
        """
        try:
            formatter = FormatterFactory.create(self.args.output_format)
            
            if self.args.output:
                # Save to file
                formatter.save_to_file(llm_output, self.args.output)
                print(f"[green]✓ Output saved to: {self.args.output}[/green]")
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
            formatter = FormatterFactory.create(self.args.output_format)
            print(formatter.format(llm_output))
    
    def run(self) -> None:
        """Run the CLI application."""
        # Parse arguments
        self.args = self.parse_arguments()
        
        # Setup logging
        log_level = WARNING
        if self.args.verbose:
            from logging import INFO
            log_level = INFO
        
        # Initialize variables for cleanup
        video_path = None
        audio_path = None
        
        try:
            # Load configuration
            self.config = self.load_configuration()
            setup_logging(level=log_level)
            
            # Initialize modules
            videos = VideoProcessor(
                video_output_dir=self.config.video.video_output_dir,
                audio_output_dir=self.config.video.audio_output_dir
            )
            
            ai = AI(api_key=self.config.ai.gemini_api_key)
            
            # Initialize Notion if enabled and not disabled via CLI
            notion = None
            use_notion = self.config.notion.enabled and not self.args.no_notion
            if use_notion:
                try:
                    notion = NotionDB(
                        api_key=self.config.notion.api_key,
                        database_id=self.config.notion.database_id
                    )
                except NotionIntegrationError as e:
                    logger.error(f"Failed to initialize Notion integration: {str(e)}")
                    logger.info("Continuing without Notion integration...")
                    use_notion = False
                    notion = None
            
            # Process with progress indicator
            with Progress(
                SpinnerColumn(spinner_name=self.config.ui.spinner_style, style=self.config.ui.spinner_color),
                TextColumn(f"[{self.config.ui.text_color}]{{task.description}}"),
            ) as progress:
                
                task = progress.add_task("Starting...", total=None)
                
                # Process video input
                video_path = self.process_video_input(videos, progress, task)
                
                # Extract audio
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
                
                # Save to Notion or output results
                if notion and use_notion:
                    progress.update(task, description="Adding results to Notion")
                    try:
                        page_id = notion.add_entry(
                            title=llm_output["title"],
                            summary=llm_output["summary"],
                            key_points=llm_output["key_points"],
                            action_items=llm_output["action_items"]
                        )
                        logger.info(f"Results saved to Notion (Page ID: {page_id})")
                        # Also output if file specified
                        if self.args.output:
                            self.output_results(llm_output)
                    except NotionIntegrationError as e:
                        logger.error(f"Failed to save to Notion: {str(e)}")
                        logger.info("Displaying results instead...")
                        self.output_results(llm_output)
                else:
                    self.output_results(llm_output)
        
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
            if self.config and self.config.video.delete_files_after:
                logger.info("Cleaning up temporary files...")
                try:
                    import os
                    if video_path and os.path.exists(video_path) and not self.args.local:
                        os.remove(video_path)
                        logger.info(f"Removed video file: {video_path}")
                    if audio_path and os.path.exists(audio_path):
                        os.remove(audio_path)
                        logger.info(f"Removed audio file: {audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up some files: {str(e)}")
            
            logger.info("Program completed successfully")
            print("[green]Program ran successfully[/]")


def main():
    """Entry point for the CLI."""
    cli = JournalLLMCLI()
    cli.run()


if __name__ == "__main__":
    main()