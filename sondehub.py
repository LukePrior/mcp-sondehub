from mcp.server.fastmcp import FastMCP
import json
from datetime import datetime
import httpx

mcp = FastMCP("sondehub")

SONDEHUB_API_BASE = "https://api.v2.sondehub.org/"

def format_api_response_for_llm(api_response):
    """
    Converts API response data to a natural language format optimized for LLM consumption
    via a Multi-Content Prompt (MCP) approach.
    
    Args:
        api_response (str): The JSON string from the API
        
    Returns:
        str: Formatted text in a structured, LLM-friendly format
    """
    try:
        # Parse the JSON response
        data = json.loads(api_response)
        
        if not data:
            return "No data found in the API response."
        
        formatted_results = []
        
        count = 0
        for item in data:
            count += 1
            # Format datetime to be more readable
            try:
                dt = datetime.fromisoformat(item.get("datetime", "").replace("Z", "+00:00"))
                formatted_date = dt.strftime("%B %d, %Y at %H:%M:%S UTC")
            except:
                formatted_date = item.get("datetime", "Unknown date")
            
            # Create a natural language description for each item with safe access to fields
            entry = f"""
Event Details:
- Date and Time: {formatted_date}
- Serial Number: {item.get("serial", "Unknown")}
- Location: Latitude {item.get("lat", "Unknown")}, Longitude {item.get("lon", "Unknown")}, Altitude {item.get("alt", "Unknown")} meters
- Recovery Status: {"Recovered" if item.get("recovered", False) else "Not Recovered"}
"""
            
            # Add optional fields if they have meaningful values
            if item.get("recovered", False) and item.get("recovered_by") and item.get("recovered_by") != "string":
                entry += f"- Recovered By: {item.get('recovered_by')}\n"
                
            if item.get("description") and item.get("description") != "string":
                entry += f"- Additional Details: {item.get('description')}\n"
                
            formatted_results.append(entry)

            if count == 10:
                break
        
        # Combine all formatted entries with a header
        header = f"# Data Report\nContaining {len(data)} event{'s' if len(data) > 1 else ''}.\n\n"
        final_output = header + "\n".join(formatted_results)
        
        return final_output
    
    except json.JSONDecodeError:
        return "Error: Invalid JSON in the API response."
    except Exception as e:
        return f"Error processing the API response: {str(e)}"

@mcp.tool()
async def get_recoveries() -> str:
    """
    Retrieves the latest recovery data from the SondeHub API.
    
    Returns:
        str: The formatted text containing the recovery data
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(SONDEHUB_API_BASE + "recovered")
            response.raise_for_status()
            return format_api_response_for_llm(response.text)
    
    except Exception as e:
        return f"Error: {str(e)}"