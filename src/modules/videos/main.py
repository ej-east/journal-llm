from src.modules.logger import get_logger
from src.modules.exceptions import (
    VideoDownloadError,
    InvalidURLError,
    AudioExtractionError,
    FileNotFoundError as CustomFileNotFoundError
)
from os.path import getctime
from pathlib import Path
from tqdm import tqdm
import yt_dlp, ffmpeg, requests


logger = get_logger(__name__)

class VideoProcessor:
    def __init__(self, video_output_dir : str = "downloads", audio_output_dir : str = "audio") -> None:
        logger.info("Successfully loaded Video Proccesser module")
        
        self.video_output_dir = video_output_dir
        self.audio_output_dir = audio_output_dir
        
        self.youtube_options = {
            'outtmpl' : f'{self.video_output_dir}/%(title)s.%(ext)s',
            'format': 'best[height<=729]/best',
            'quiet': True,  # Suppress yt-dlp output
            'no_warnings': True,  # Suppress warnings
            'no_progress': True,  # Don't show download progress
        }
        
        self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        Path(self.video_output_dir).mkdir(exist_ok=True)
        Path(self.audio_output_dir).mkdir(exist_ok=True)
        
    def is_valid_url(self, url: str) -> bool:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"URL validation failed for '{url}': {str(e)}")
            return False
    
    def download_youtube_video(self, url : str) -> str:
        logger.info(f"Starting YouTube video download from: {url}")
        downloaded_file_path = None
        try:
            options_with_hook = self.youtube_options.copy()
            
            def progress_hook(d):
                nonlocal downloaded_file_path
                if d['status'] == 'finished':
                    downloaded_file_path = d['filename']
                    logger.debug(f"Download finished: {downloaded_file_path}")
            
            options_with_hook['progress_hooks'] = [progress_hook]
            
            with yt_dlp.YoutubeDL(options_with_hook) as youtube_downloader:
                info = youtube_downloader.extract_info(url, download=False)
                
                if not info:
                    raise VideoDownloadError(f"Could not extract video information from URL: {url}")
                
                video_title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                logger.info(f"Downloading video: '{video_title}' (duration: {duration}s)")
                
                info = youtube_downloader.extract_info(url, download=True)
                
                if downloaded_file_path and Path(downloaded_file_path).exists():
                    logger.info(f"Downloaded YouTube video: {downloaded_file_path}")
                    return str(downloaded_file_path)

                
                raise VideoDownloadError(f"Could not determine downloaded file path")
                
        except yt_dlp.utils.DownloadError as e:
            raise VideoDownloadError(f"YouTube download failed: {str(e)}")
        except Exception as e:
            if isinstance(e, VideoDownloadError):
                raise
            raise VideoDownloadError(f"Unexpected error during YouTube download: {str(e)}")
    
    def download_video(self, url : str, filename : str = "output.mp4") -> str:
        logger.info(f"Starting video download from: {url}")
        try:
            response = requests.get(url, stream=True, headers=self.headers, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            output_path = f"{self.video_output_dir}/{filename}"
            with open(output_path, 'wb') as file:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=self.video_output_dir) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            pbar.update(len(chunk))
            
            logger.info(f"Video downloaded successfully: {output_path}")
            return output_path
        except requests.exceptions.RequestException as e:
            raise VideoDownloadError(f"Failed to download video from {url}: {str(e)}")
        except IOError as e:
            raise VideoDownloadError(f"Failed to save video file: {str(e)}")
        
    
    def extract_audio(self, filepath : str) -> str:
        audio_format = ".wav"
        video_path = Path(filepath)
        audio_output_dir = Path(self.audio_output_dir)
        audio_output_path = audio_output_dir / f"{video_path.stem}{audio_format}"

        if not video_path or not video_path.exists():
            raise CustomFileNotFoundError(f"Video file not found: {filepath}")
        
        logger.info(f"Extracting audio from: {filepath}")
        try:
            ffmpeg.input(str(video_path)).output(
                str(audio_output_path), 
                acodec='pcm_s16le', 
                ac=1, 
                ar='16000'
            ).overwrite_output().run(quiet=True, capture_stderr=True)
            
            logger.info(f"Audio extracted successfully: {str(audio_output_path)}")
            return str(audio_output_path)
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown ffmpeg error"
            raise AudioExtractionError(f"Failed to extract audio from {filepath}: {error_msg}")
        except Exception as e:
            raise AudioExtractionError(f"Unexpected error during audio extraction: {str(e)}")
        
        