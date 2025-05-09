import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Awaitable
import aiohttp
import re
from datetime import datetime, timedelta

from agent.tools import FederalRegistryTools
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent')

class OllamaAgent:
    """Agent that uses Ollama for LLM inference and tools for information retrieval."""
    
    def __init__(self):
        self.tools = FederalRegistryTools()
        self.ollama_base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.chat_history = []
        
        # Register tools
        self.available_tools = {
            "search_documents": self.tools.search_documents,
            "get_recent_documents": self.tools.get_recent_documents,
            "get_document_by_id": self.tools.get_document_by_id,
            "get_document_types": self.tools.get_document_types,
            "get_agencies": self.tools.get_agencies,
            "get_topics": self.tools.get_topics,
            "get_presidential_document_types": self.tools.get_presidential_document_types,
            "search_recent_executive_orders": self.tools.search_recent_executive_orders,
            "search_documents_by_date_range": self.tools.search_documents_by_date_range,
            "search_by_agency_and_topic": self.tools.search_by_agency_and_topic
        }
        
        # Tool descriptions for the model
        self.tool_descriptions = [
            {
                "name": "search_documents",
                "description": "Search for documents in the Federal Registry database based on various criteria",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "Search terms to look for in title and abstract"
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Start date for publication_date filter (YYYY-MM-DD)"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "End date for publication_date filter (YYYY-MM-DD)"
                        },
                        "document_type": {
                            "type": "string",
                            "description": "Filter by document type"
                        },
                        "agency": {
                            "type": "string",
                            "description": "Filter by agency name"
                        },
                        "topic": {
                            "type": "string",
                            "description": "Filter by topic name"
                        },
                        "presidential_doc_type": {
                            "type": "string",
                            "description": "Filter by presidential document type"
                        },
                        "executive_order": {
                            "type": "string",
                            "description": "Filter by executive order number"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return"
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Offset for pagination"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_recent_documents",
                "description": "Get the most recent documents in the Federal Registry",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of documents to return"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_document_by_id",
                "description": "Get a document by its ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "integer",
                            "description": "The document ID"
                        }
                    },
                    "required": ["document_id"]
                }
            },
            {
                "name": "get_document_types",
                "description": "Get all document types in the database",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_agencies",
                "description": "Get all agencies in the database",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_topics",
                "description": "Get all topics in the database",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_presidential_document_types",
                "description": "Get all presidential document types in the database",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "search_recent_executive_orders",
                "description": "Search for recent executive orders",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days in the past to search"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "search_documents_by_date_range",
                "description": "Search for documents within a date range",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return"
                        }
                    },
                    "required": ["start_date", "end_date"]
                }
            },
            {
                "name": "search_by_agency_and_topic",
                "description": "Search for documents by agency and topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agency": {
                            "type": "string",
                            "description": "Agency name"
                        },
                        "topic": {
                            "type": "string",
                            "description": "Topic name"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return"
                        }
                    },
                    "required": ["agency", "topic"]
                }
            }
        ]
    
    async def init(self):
        """Initialize the agent and connect to the database."""
        await self.tools.connect()
    
    async def close(self):
        """Close the agent's resources."""
        await self.tools.close()
    
    async def _ollama_chat_completion(self, messages):
        """
        Send a request to Ollama API for chat completion.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Response from Ollama API
        """
        endpoint = f"{self.ollama_base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,  # Explicitly disable streaming
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 1000
            }
        }
        
        try:
            logger.info(f"Sending request to Ollama API: {endpoint}")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    logger.info(f"Received response from Ollama: {json.dumps(data, indent=2)}")
                    
                    # Handle both streaming and non-streaming responses
                    if isinstance(data, dict) and 'message' in data:
                        return {
                            "message": {
                                "content": data['message'].get('content', ''),
                                "role": data['message'].get('role', 'assistant')
                            }
                        }
                    return data
        except Exception as e:
            logger.error(f"Error in Ollama API call: {str(e)}")
            raise
    
    async def _execute_tool(self, tool_name, parameters):
        """
        Execute a tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            
        Returns:
            Result of the tool execution
        """
        logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")
        
        if tool_name not in self.available_tools:
            return {"error": f"Tool not found: {tool_name}"}
        
        try:
            tool_func = self.available_tools[tool_name]
            result = await tool_func(**parameters)
            
            # Convert result to a more concise format if it's a list of documents
            if isinstance(result, list) and result and isinstance(result[0], dict) and 'document_number' in result[0]:
                simplified_result = []
                for doc in result:
                    simplified_doc = {
                        'id': doc.get('id'),
                        'document_number': doc.get('document_number'),
                        'document_type': doc.get('document_type'),
                        'title': doc.get('title'),
                        'publication_date': doc.get('publication_date'),
                        'abstract': doc.get('abstract')
                    }
                    
                    # Include presidential document info if available
                    if doc.get('presidential_document_type'):
                        simplified_doc['presidential_document_type'] = doc.get('presidential_document_type')
                    if doc.get('executive_order_number'):
                        simplified_doc['executive_order_number'] = doc.get('executive_order_number')
                    
                    # Add agencies and topics
                    if 'agencies' in doc:
                        simplified_doc['agencies'] = doc.get('agencies')
                    if 'topics' in doc:
                        simplified_doc['topics'] = doc.get('topics')
                    
                    simplified_result.append(simplified_doc)
                
                return simplified_result
            
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {"error": f"Error executing tool {tool_name}: {str(e)}"}
    
    def _extract_tool_calls(self, text):
        """
        Extract tool calls from the model's response text.
        
        Args:
            text: Model's response text
            
        Returns:
            List of tool call dictionaries
        """
        # Pattern to match a JSON object (handles nested objects too)
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        
        # Find all JSON blocks in the text
        matches = re.findall(json_pattern, text)
        
        tool_calls = []
        for match in matches:
            try:
                # Parse the JSON
                tool_call = json.loads(match)
                
                # Check if it has required tool call fields
                if isinstance(tool_call, dict) and 'name' in tool_call and 'parameters' in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON: {match}")
                continue
        
        return tool_calls
    
    async def process_message(self, message, chat_id=None):
        """
        Process a user message and return the agent's response.
        
        Args:
            message: User message text
            chat_id: Chat ID for conversation tracking
            
        Returns:
            Agent's response
        """
        # Initialize chat history if it's a new conversation
        if chat_id not in self.chat_history:
            self.chat_history = []
        
        # Create the system message
        system_message = {
            "role": "system",
            "content": """You are a helpful assistant that can access and search through the Federal Registry database.
            Your goal is to help users find information about federal documents, executive orders, rules, and notices.
            
            You have access to the following tools:
            1. search_documents - Search for documents with various filters
               Parameters: keywords, date_from, date_to, document_type, agency, topic, presidential_doc_type, executive_order, limit, offset
            2. get_recent_documents - Get the most recent documents
               Parameters: limit
            3. get_document_by_id - Get a specific document by ID
               Parameters: document_id
            4. get_document_types - Get all document types
            5. get_agencies - Get all agencies
            6. get_topics - Get all topics
            7. get_presidential_document_types - Get all presidential document types
            8. search_recent_executive_orders - Search for recent executive orders
               Parameters: days, limit
            9. search_documents_by_date_range - Search documents within a date range
               Parameters: start_date, end_date, limit
            10. search_by_agency_and_topic - Search documents by agency and topic
                Parameters: agency, topic, limit

            To use a tool, format your tool call as follows:
            ```json
            {
                "name": "tool_name",
                "parameters": {
                    "param1": "value1",
                    "param2": "value2"
                }
            }
            ```

            Examples:
            1. To search documents from a specific date:
            ```json
            {
                "name": "search_documents",
                "parameters": {
                    "date_from": "2025-01-01",
                    "date_to": "2025-01-31"
                }
            }
            ```

            2. To search recent executive orders:
            ```json
            {
                "name": "search_recent_executive_orders",
                "parameters": {
                    "days": 30,
                    "limit": 10
                }
            }
            ```

            Always use these exact tool names and parameters. Do not invent new tool names.
            The current date is """ + datetime.now().strftime("%Y-%m-%d") + """.
            """
        }
        
        # Add user message to the conversation
        self.chat_history.append({"role": "user", "content": message})
        
        # Prepare messages for the chat completion
        messages = [system_message] + self.chat_history
        
        try:
            # Get the model's response
            response = await self._ollama_chat_completion(messages)
            model_response = response.get("message", {}).get("content", "")
            
            # Extract tool calls from the response
            tool_calls = self._extract_tool_calls(model_response)
            
            # If there are tool calls, execute them
            if tool_calls:
                tool_results = []
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name")
                    parameters = tool_call.get("parameters", {})
                    
                    # Execute the tool
                    result = await self._execute_tool(tool_name, parameters)
                    
                    # Add result to the list
                    tool_results.append({
                        "tool_name": tool_name,
                        "parameters": parameters,
                        "result": result
                    })
                
                # Add tool results to the conversation
                tool_results_message = {
                    "role": "system",
                    "content": f"Tool call results: {json.dumps(tool_results, default=str)}"
                }
                
                self.chat_history.append({"role": "assistant", "content": model_response})
                self.chat_history.append(tool_results_message)
                
                # Get the final response from the model with the tool results
                final_response = await self._ollama_chat_completion(messages + [
                    {"role": "assistant", "content": model_response},
                    tool_results_message
                ])
                
                # Update conversation history
                assistant_message = final_response.get("message", {}).get("content", "")
                self.chat_history.append({"role": "assistant", "content": assistant_message})
                
                return assistant_message
            else:
                # If there are no tool calls, just return the model's response
                self.chat_history.append({"role": "assistant", "content": model_response})
                return model_response
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return f"I'm sorry, but I encountered an error while processing your request. Please try again later."
    
    def reset_chat(self):
        """Reset the chat history."""
        self.chat_history = []