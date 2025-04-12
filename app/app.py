import viktor as vkt
from pathlib import Path
import json
import anthropic
import os


def list_tools():
    with open(Path(__file__).parent / "get_tools_output.json", "r") as f:
        response = json.load(f)
    return [{
        "name": tool["name"],
        "description": tool["description"],
        "input_schema": tool["inputSchema"]
    } for tool in response["tools"]]


def use_tool(tool_name: str, tool_args: dict):
    with open(Path(__file__).parent / "use_tool_output.json", "r") as f:
        response = json.load(f)

    # remove annotations from the content items
    if "content" in response and isinstance(response["content"], list):
        for item in response["content"]:
            if isinstance(item, dict) and "annotations" in item:
                del item["annotations"]
    return response


def process_query(query: str) -> str:
    """Process a query using Claude and available tools"""
    messages = [
        {
            "role": "user",
            "content": query
        }
    ]
    
    # Get the available tools from the MCP
    available_tools = list_tools()
    
    # Initial Claude API call
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=messages,
        tools=available_tools
    )

    # Process response and handle tool calls
    final_text = []

    assistant_message_content = []
    for content in response.content:
        if content.type == 'text':
            final_text.append(content.text)
            assistant_message_content.append(content)
        elif content.type == 'tool_use':
            tool_name = content.name
            tool_args = content.input

            # Execute tool call
            result = use_tool(tool_name, tool_args)
            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

            assistant_message_content.append(content)
            messages.append({
                "role": "assistant",
                "content": assistant_message_content
            })
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result["content"]
                    }
                ]
            })

           # Get next response from Claude
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=messages,
                tools=available_tools
            )

            final_text.append(response.content[0].text)

    return "\n".join(final_text)



class Parametrization(vkt.Parametrization):
    question = vkt.TextField("Ask a question", default="What tools are available?")
    download = vkt.DownloadButton("Download", "download")

class Controller(vkt.Controller):
    parametrization = Parametrization

    def download(self, params, **kwargs):
        from run_worker import execute
        output_file = execute()
        return vkt.DownloadResult(output_file, 'output.json')

    @vkt.WebView("Chat", duration_guess=4)
    def chat_interface(self, params, **kwargs):
        
        answer = process_query(params.question)

        # Read the HTML template file
        template_path = Path(__file__).parent / 'question_template.html'
        template = template_path.read_text()
        
        # Replace the placeholder with the actual query
        html = template.replace('{question}', answer)
        
        return vkt.WebResult(html=html)
