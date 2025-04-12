from multiprocessing import process
from matplotlib.style import available
import viktor as vkt
from pathlib import Path
import json


def list_tools():
    with open(Path(__file__).parent / "get_tools_output.json", "r") as f:
        response = json.load(f)
    return [{
        "name": tool["name"],
        "description": tool["description"],
        "input_schema": tool["inputSchema"]
    } for tool in response["tools"]]


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
    response = self.anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=messages,
        tools=available_tools
    )

    # Process response and handle tool calls
    # final_text = []

    # assistant_message_content = []
    # for content in response.content:
    #     if content.type == 'text':
    #         final_text.append(content.text)
    #         assistant_message_content.append(content)
    #     elif content.type == 'tool_use':
    #         tool_name = content.name
    #         tool_args = content.input

    #         # Execute tool call
    #         result = await self.session.call_tool(tool_name, tool_args)
    #         final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

    #         assistant_message_content.append(content)
    #         messages.append({
    #             "role": "assistant",
    #             "content": assistant_message_content
    #         })
    #         messages.append({
    #             "role": "user",
    #             "content": [
    #                 {
    #                     "type": "tool_result",
    #                     "tool_use_id": content.id,
    #                     "content": result.content
    #                 }
    #             ]
    #         })

    #         # Get next response from Claude
    #         response = self.anthropic.messages.create(
    #             model="claude-3-5-sonnet-20241022",
    #             max_tokens=1000,
    #             messages=messages,
    #             tools=available_tools
    #         )

    #         final_text.append(response.content[0].text)

    # return "\n".join(final_text)



class Parametrization(vkt.Parametrization):
    question = vkt.TextField("Ask a question")
    download = vkt.DownloadButton("Download", "download")

class Controller(vkt.Controller):
    parametrization = Parametrization

    def download(self, params, **kwargs):
        from .run_worker import execute
        execute()
        return vkt.DownloadResult(file_content="")

    @vkt.WebView("Chat")
    def chat_interface(self, params, **kwargs):
        
        process_query(params.question)


        # Read the HTML template file
        template_path = Path(__file__).parent / 'question_template.html'
        template = template_path.read_text()
        
        # Replace the placeholder with the actual query
        question_value = params.question if params.question else "No question asked yet."
        html = template.replace('{question}', question_value)
        
        return vkt.WebResult(html=html)
