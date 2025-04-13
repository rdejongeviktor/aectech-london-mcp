import viktor as vkt
from pathlib import Path
import json
import anthropic
import os


def list_tools():
    """
    Retrieves a list of available tools from the MCP server.
    
    Returns:
        list: A list of dictionaries containing tool information with keys:
            - name: The name of the tool
            - description: A description of what the tool does
            - input_schema: The schema defining the tool's input parameters
    """
    from viktor.external.generic import GenericAnalysis

    input_get_tools = {
        'job': 'get-tools',
        'tool_name': None,
        'tool-args': None,
    }

    # Generate the input file(s)
    files = [
        ('input.json', vkt.File.from_data(json.dumps(input_get_tools))),
    ]

    # Run the analysis and obtain the output file.
    try:
        generic_analysis = GenericAnalysis(files=files, executable_key="mcp", output_filenames=["output.json"])
        generic_analysis.execute(timeout=60)
        output_file = generic_analysis.get_output_file("output.json")
        response = json.loads(output_file.getvalue())
    except ConnectionError:
        with open(Path(__file__).parent / "get_tools_output.json", "r") as f:
            response = json.load(f)

    return [{
        "name": tool["name"],
        "description": tool["description"],
        "input_schema": tool["inputSchema"]
    } for tool in response["tools"]]


def use_tool(tool_name: str, tool_args: dict):
    """
    Executes a specified tool with the provided arguments.
    
    Args:
        tool_name (str): The name of the tool to execute
        tool_args (dict): A dictionary containing the arguments to pass to the tool
        
    Returns:
        dict: The response from the tool execution, with annotations removed from content items
    """
    from viktor.external.generic import GenericAnalysis

    input_get_tools = {
        'job': 'use-tool',
        'tool_name': tool_name,
        'tool_args': tool_args,
    }

    # Generate the input file(s)
    files = [
        ('input.json', vkt.File.from_data(json.dumps(input_get_tools))),
    ]

    # Run the analysis and obtain the output file.
    try:
        generic_analysis = GenericAnalysis(files=files, executable_key="mcp", output_filenames=["output.json"])
        generic_analysis.execute(timeout=60)
        output_file = generic_analysis.get_output_file("output.json")
        response = json.loads(output_file.getvalue())
    except ConnectionError:
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
            final_text.append(f"\n[Calling tool {tool_name} with args {tool_args}]\n")

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


class MyText(vkt.Text):

    def __init__(self, value_func, *, visible = True, flex = 100):
        self._value_func = value_func
        super().__init__('', visible=visible, flex=flex)

    def _generate(self, *args, **kwargs):
        res = super()._generate(*args, **kwargs)
        # print(res['parametrization'].keys())

        params = args[1]
        res['parametrization']['value'] = self._value_func(params)

        return res


def value_func(params):
    return params.answer

class Parametrization(vkt.Parametrization):
    query = vkt.TextField("Enter your query", default="What tools are available?", flex=50)
    ask = vkt.SetParamsButton('Ask', 'ask', flex=10)
    answer = vkt.HiddenField('j')
    answer_title = vkt.Text("**Last answer:**")
    anwerblock = MyText(value_func)

class Controller(vkt.Controller):
    parametrization = Parametrization


    def ask(self, params, **kwargs):
        answer = process_query(params.query)
        return vkt.SetParamsResult({'answer': answer})

    @vkt.WebView("Responses", duration_guess=4)
    def chat_interface(self, params, **kwargs):
        """
        Renders the chat interface web view.
        
        Args:
            params: The parametrization parameters
            **kwargs: Additional keyword arguments
            
        Returns:
            vkt.WebResult: HTML content for the web view
        """
        
        answer = process_query(params.query)

        # Read the HTML template file
        template_path = Path(__file__).parent / 'response_template.html'
        template = template_path.read_text()
        
        # Replace the placeholder with the LLM response
        html = template.replace('{response}', answer)
        
        return vkt.WebResult(html=html)
