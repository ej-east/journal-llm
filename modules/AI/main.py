from modules.logger import get_logger
from modules.exceptions import (
    TranscriptionError,
    SummarizationError,
    InvalidAPIKeyError,
    ModelLoadError
)
import whisper, warnings, json
from google import genai

logger = get_logger(__name__)

class AI:
    def __init__(self, api_key : str) -> None:
        logger.info("Loading AI module...")
        warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
        
        if not api_key:
            raise InvalidAPIKeyError("Gemini API key is required but not provided")
        
        try:
            logger.info("Loading Whisper model...")
            self.transcription_model = whisper.load_model("base")
        except Exception as e:
            raise ModelLoadError(f"Failed to load Whisper model: {str(e)}")
        
        try:
            logger.info("Initializing Gemini client...")
            self.gemini_client = genai.Client(api_key=api_key)
        except Exception as e:
            raise InvalidAPIKeyError(f"Failed to initialize Gemini client: {str(e)}")
        
        logger.info("AI module loaded successfully")
        
        self.summarize_prompt = """
            Analyze the following transcription and provide a structured summary in JSON format with these fields:
            - "title": A concise title for the content (max 100 characters)
            - "summary": A brief overview paragraph (2-3 sentences)
            - "key_points": The main topics or themes discussed (bullet points in markdown). This should be a list
            - "action_items": Any tasks, decisions, or next steps mentioned (bullet points in markdown, or "None identified" if none)
            
            Transcription: {transcription}
            
            Return only valid JSON.  For bulleted list only use - not *s
            """


    def transcribe_audio(self, filepath : str) -> str:
        logger.info(f"Starting audio transcription: {filepath}")
        try:
            results : dict = self.transcription_model.transcribe(filepath)
            
            if not results or "text" not in results:
                raise TranscriptionError(f"Transcription returned no results for: {filepath}")
            
            if not results["text"].strip():
                raise TranscriptionError(f"Transcription returned empty text for: {filepath}")
            
            logger.info(f"Transcription completed successfully ({len(results['text'])} characters)")
            return results["text"]
        except Exception as e:
            if isinstance(e, TranscriptionError):
                raise
            raise TranscriptionError(f"Failed to transcribe audio: {str(e)}")
    
    def get_llm_summary(self, transcription : str) -> dict:
        logger.info(f"Creating summary from transcription ({len(transcription)} characters)")
        
        if not transcription or not transcription.strip():
            raise SummarizationError("Cannot summarize empty transcription")
        
        try:
            response = self.gemini_client.models.generate_content(
                model = "gemini-2.5-flash",
                contents = self.summarize_prompt.format(transcription=transcription)
            )
            
            if not response or not response.text:
                raise SummarizationError("Gemini API returned empty response")
            
            # Clean and parse the JSON response
            cleaned_response = response.text.strip().replace("`", "").replace("json", "")
            
            try:
                summary_dict = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                raise SummarizationError(f"Failed to parse Gemini response as JSON: {str(e)}")
            
            # Validate required fields
            required_in_summary = ["title", "summary", "key_points", "action_items"]
            missing_keys = [key for key in required_in_summary if key not in summary_dict]
            
            if missing_keys:
                raise SummarizationError(f"Summary missing required keys: {', '.join(missing_keys)}")
            
            logger.info("Summary created successfully")
            return summary_dict
            
        except Exception as e:
            if isinstance(e, SummarizationError):
                raise
            raise SummarizationError(f"Unexpected error during summarization: {str(e)}")