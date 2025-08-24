from modules.logger import get_logger
import whisper, warnings, json
from google import genai

logger = get_logger(__name__)

class AI:
    def __init__(self, api_key : str) -> None:
        logger.info("Successfully loaded AI module")
        warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
        
        self.transcription_model = whisper.load_model("base")
        self.gemini_client = genai.Client(api_key=api_key)
        
        self.summarize_prompt = """
            Analyze the following transcription and provide a structured summary in JSON format with these fields:
            - "title": A concise title for the content (max 100 characters)
            - "summary": A brief overview paragraph (2-3 sentences)
            - "key_points": The main topics or themes discussed (bullet points in markdown). This should be a list
            - "action_items": Any tasks, decisions, or next steps mentioned (bullet points in markdown, or "None identified" if none)
            
            Transcription: {transcription}
            
            Return only valid JSON.  For bulleted list only use - not *s
            """


    def transcribe_audio(self, filepath : str) -> str | None:
        logger.info("Transcribing audio from video")
        results : dict = self.transcription_model.transcribe(filepath)
        
        if not results:
            logger.warning("Transcription failed")
            return 

        return results["text"]
    
    def get_llm_summary(self, transcription : str) -> dict | None:
        logger.info("Creating summary from transcription")
        response = self.gemini_client.models.generate_content(
            model = "gemini-2.5-flash",
            contents = self.summarize_prompt.format(transcription=transcription)
        )
        
        if not response or not response.text:
            logger.warning("Transcription failed")
            return
        
        
        summary_dict = json.loads(response.text.strip().replace("`", "",).replace("json",""))
        required_in_summary = ["title", "summary", "key_points", "action_items"]
        if not all(key in summary_dict for key in required_in_summary):
            logger.warning("Summary missing required keys")
            return
    
        return summary_dict