from datetime import datetime
from notion_client import Client
import logging
import re

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class NotionDB:
    def __init__(self, api_key : str, database_id : str) -> None:
        logger.info("Successfully loaded NotionDB module")
        
        self.database_id = database_id
        self.notion_client = Client(auth=api_key)
    
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
    
    def add_entry(self, title : str, summary : str, key_points : list[str], action_items: list[str]) -> str | None:
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
        
        logger.info(f"Added entry, {title}, to notion database")
