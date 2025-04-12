import viktor as vkt
from pathlib import Path
import json


class Parametrization(vkt.Parametrization):
    query = vkt.TextField("Ask a question")

class Controller(vkt.Controller):
    parametrization = Parametrization

    @vkt.WebView("Chat")
    def chat_interface(self, params, **kwargs):
        
        # get tools from mcp
        get_tools_analysis = vkt.external.GenericAnalysis(  
            files=[("input.json", vkt.File())], 
            executable_key="mcp",
            output_filenames=["output.json"]
        )
        get_tools_analysis.execute()
        tools = get_tools_analysis.get_output_file("output.json", as_file=True)
            
        # 


        # Read the HTML template file
        template_path = Path(__file__).parent / 'question_template.html'
        template = template_path.read_text()
        
        # Replace the placeholder with the actual query
        query_value = params.query if params.query else "No question asked yet."
        html = template.replace('{query}', query_value)
        
        return vkt.WebResult(html=html)
