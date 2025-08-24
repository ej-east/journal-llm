from modules.logger import get_logger
from os.path import getctime
from pathlib import Path
import yt_dlp, ffmpeg


logger = get_logger(__name__)

class VideoProcessor:
    def __init__(self, video_output_dir : str = "downloads", audio_output_dir : str = "audio") -> None:
        logger.info("Successfully loaded Video Proccesser module")
        
        self.video_output_dir = video_output_dir
        self.audio_output_dir = audio_output_dir
        
        self.youtube_options = {
            'outtmpl' : f'{self.video_output_dir}/%(title)s.%(ext)s',
            'format': 'best[height<=729]/best'
        }
        
        Path(self.video_output_dir).mkdir(exist_ok=True)
        Path(self.audio_output_dir).mkdir(exist_ok=True)

    def download_video(self, url : str) -> str | None:
        logger.info("Starting YouTube video download")
        with yt_dlp.YoutubeDL(self.youtube_options) as youtube_downloader:
            info = youtube_downloader.extract_info(url, download=False)
            
            if not info:
                logger.warning("No information on YouTube video found")
                return
            
        video_title = info.get('title', 'Unknown')
        duration = info.get('duration', 0)
        
        youtube_downloader.download([url])
        
        # Now we need to figure which file we just downloaded....
        
        ## First approach is to list all of the files and see if it matches what we expect the filename to be
        for file in tuple(Path(self.video_output_dir).iterdir()):
            if file and file.is_file() and video_title.replace('/', '_') in file.stem:
                logger.info(f"Downloaded YouTube Video: {file}")
                return str(file)
        
        ## Second approach is to get the file that is the youngest
        files = list(Path(self.video_output_dir).iterdir())
        if files:
            latest_file = max(files, key=getctime)
            logger.info(f"Downloaded YouTube Video: {latest_file}")
            return str(file)
        return
    
    def extract_audio(self, filepath : str) -> str | None:
        audio_format = ".wav"
        video_path = Path(filepath)
        audio_output_dir = Path(self.audio_output_dir)
        audio_output_path = audio_output_dir / f"{video_path.stem}{audio_format}"

        if not video_path or not video_path.exists():
            logger.warning("Video file was not found")
            return
        
        logger.info("Extracting audio")
        ffmpeg.input(str(video_path)).output(str(audio_output_path), acodec='pcm_s16le', ac=1, ar='16000').overwrite_output().run(quiet=True, capture_stderr=True)
        
        logger.info(f"Extracted Audio - Filename: {str(audio_output_path)}")
        return str(audio_output_path)
        
        