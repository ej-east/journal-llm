from src.modules.logger import get_logger
from src.modules.exceptions import (
    NotionAPIError,
    NotionDatabaseError,
    InvalidAPIKeyError
)
from datetime import datetime
from notion_client import Client
from notion_client.errors import APIResponseError
import re

logger = get_logger(__name__)

class NotionDB:
    def __init__(self, api_key : str, database_id : str) -> None:
        logger.info("Loading NotionDB module...")
        
        if not api_key:
            raise InvalidAPIKeyError("Notion API key is required but not provided")
        
        if not database_id:
            raise NotionDatabaseError("Notion database ID is required but not provided")
        
        self.database_id = database_id
        
        try:
            self.notion_client = Client(auth=api_key)
            logger.info("NotionDB module loaded successfully")
        except Exception as e:
            raise InvalidAPIKeyError(f"Failed to initialize Notion client: {str(e)}")
    
    def parse_markdown_to_rich_text(self, text: str) -> list:
        rich_text = []
        

        pattern = r'\*\*([^*]+)\*\*|\*([^*]+)\*|([^*]+)'
        
        matches = re.finditer(pattern, text)
        
        for match in matches:
            if match.group(1):  # Bold text
                rich_text.append({
                    "type": "text",
                    "text": {
                        "content": match.group(1)
                    },
                    "annotations": {
                        "bold": True
                    }
                })
            elif match.group(2):  # Italic text
                rich_text.append({
                    "type": "text",
                    "text": {
                        "content": match.group(2)
                    },
                    "annotations": {
                        "italic": True
                    }
                })
            elif match.group(3):  # Regular text
                rich_text.append({
                    "type": "text",
                    "text": {
                        "content": match.group(3)
                    }
                })
        
        if not rich_text:
            rich_text.append({
                "type": "text",
                "text": {
                    "content": text
                }
            })
        
        return rich_text
    
    def create_bulleted_list_item(self, text: str) -> dict:
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": self.parse_markdown_to_rich_text(text.lstrip("- "))
            }
        }
    
    def add_entry(self, title : str, summary : str, key_points : list[str], action_items: list[str]) -> str:
        logger.info(f"Adding entry to Notion: '{title}'")
        
        if not title:
            raise NotionDatabaseError("Title cannot be empty")
        
        if not summary:
            raise NotionDatabaseError("Summary cannot be empty")
        
        try:
            new_page = self.notion_client.pages.create(
                parent={
                    "database_id": self.database_id
                },
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    },
                    "Date": {  # Or whatever your date property is called
                        "date": {
                            "start": datetime.now().strftime("%Y-%m-%d")
                        }
                     },
                    "Is Read": {
                        "checkbox" : False
                    }
                 },
                children=[
                    # Main title (H1)
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": title
                                    }
                                }
                            ]
                        }
                    },
        
                # Summary section (H2)
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Summary"
                                }
                            }
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": self.parse_markdown_to_rich_text(summary)
                    }
                },
                
                # Key Points section (H2)
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Key Points"
                                }
                            }
                        ]
                    }
                },
        
                # Key points as bulleted list items with markdown support
                *[self.create_bulleted_list_item(point) for point in key_points],
        
                # Action Items section (H2)
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Action Items"
                                }
                            }
                        ]
                    }
                },
                
                # Action items as bulleted list items with markdown support
                *[self.create_bulleted_list_item(action) for action in action_items],
                
                # Divider
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                
                # Footer note
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "This was generated by journal-llm"
                                },
                                "annotations": {
                                    "italic": True,
                                    "color": "gray"
                                }
                            }
                        ]
                    }
                }
            ])
            
            page_id = new_page.get('id', 'unknown')
            logger.info(f"Successfully added entry '{title}' to Notion database (ID: {page_id})")
            return page_id
            
        except APIResponseError as e:
            error_msg = f"Notion API error: {e.status} - {e.message}"
            logger.error(error_msg)
            raise NotionAPIError(error_msg)
        except Exception as e:
            error_msg = f"Failed to add entry to Notion: {str(e)}"
            logger.error(error_msg)
            raise NotionDatabaseError(error_msg)