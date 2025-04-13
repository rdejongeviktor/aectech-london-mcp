import viktor as vkt
from pathlib import Path
import json
import anthropic
import os
from datetime import date
import plotly.graph_objects as go
import io
from PIL import Image, ImageDraw, ImageFont


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
    return params.model.answer

class Parametrization(vkt.Parametrization):
    
    # todo: add intro
    # todo: add 'show_model'

    model = vkt.Step('GModel', views=['show_model'])
    model.query = vkt.TextField("Enter your query", default="What tools are available?", flex=50)
    model.ask = vkt.SetParamsButton('Ask', 'ask', flex=10)
    model.answer = vkt.HiddenField('j')
    model.answer_title = vkt.Text("**Last answer:**")
    model.anwerblock = MyText(value_func)

    analysis = vkt.Step('Analysis', views=['show_map', 'analysis_result'])
    analysis.location = vkt.GeoPointField('Location', default=vkt.GeoPoint(lat=51.4834, lon=-0.0106))

    report = vkt.Step('Report', views=['create_report'])
    report.building_name = vkt.TextField("Building name", default="Modern")
    report.customer_name = vkt.TextField('Customer name', default='Acme')

class Controller(vkt.Controller):
    parametrization = Parametrization

    def ask(self, params, **kwargs):
        answer = process_query(params.model.query)
        return vkt.SetParamsResult({'model':{'answer': answer}})

    @vkt.GeometryView('Model', duration_guess=4)
    def show_model(self, params, **kwargs):
        return vkt.GeometryResult(geometry=vkt.File.from_path(Path(__file__).parent / "towers.3dm"), geometry_type="3dm")

    @vkt.MapView('Location')
    def show_map(self, params, **kwargs):
        features = []
        if params.analysis.location is not None:
            features.append(vkt.MapPoint.from_geo_point(params.analysis.location))
        return vkt.MapResult(features)
    
    @vkt.GeometryView('Analysis result', duration_guess=4)
    def analysis_result(self, params, **kwargs):
        return vkt.GeometryResult(geometry=vkt.File.from_path(Path(__file__).parent / "towers.3dm"), geometry_type="3dm")
    
    @vkt.PDFView("Report", duration_guess=10)
    def create_report(self, params, **kwargs):
        building_name = params.report.building_name
        customer_name = params.report.customer_name
        today = date.today().strftime("%B %d, %Y")
        
        # Hard-coded parameters
        location = "London, UK"
        height = 120
        floors = 35
        building_type = "Office"
        
        wind_data = self.generate_wind_analysis()
        sunlight_data = self.generate_sunlight_analysis()
        
        report_image = self.create_report_image(building_name, customer_name, location, height, floors, building_type, today, wind_data, sunlight_data)
        pdf_file = self.image_to_pdf(report_image)
        
        return vkt.PDFResult(file=pdf_file)

    def create_report_image(self, building_name, customer_name, location, height, floors, building_type, date, wind_data, sunlight_data):
        img = Image.new('RGB', (2100, 2970), color='white')  # A4 size at 300 dpi
        d = ImageDraw.Draw(img)
        
        font_small = ImageFont.load_default().font_variant(size=28)
        font_medium = ImageFont.load_default().font_variant(size=36)
        font_large = ImageFont.load_default().font_variant(size=48)
        font_title = ImageFont.load_default().font_variant(size=60)

        # Title and Logo
        d.text((100, 100), "AEC Building Analysis Report", font=font_title, fill='black')
        d.text((100, 180), f"{building_name}", font=font_large, fill='black')
        d.text((100, 240), f"Prepared for: {customer_name}", font=font_medium, fill='black')
        d.text((100, 300), f"Generated on: {date}", font=font_medium, fill='black')

        # 1. Executive Summary
        d.text((100, 400), "1. Executive Summary", font=font_large, fill='black')
        summary_text = [
            f"This report presents a comprehensive analysis of {building_name}, a {height}m tall",
            f"{building_type.lower()} building located in {location}. With {floors} floors, this structure",
            "has been evaluated for its environmental impact, energy efficiency, and overall",
            "performance. Key findings and recommendations are outlined in the following sections.",
            f"This analysis has been prepared exclusively for {customer_name} to assist in",
            "decision-making processes related to the building's design and operation."
        ]
        for i, line in enumerate(summary_text):
            d.text((100, 460 + i*40), line, font=font_small, fill='black')

        # 2. Building Specifications
        d.text((100, 720), "2. Building Specifications", font=font_large, fill='black')
        specs = [
            f"Name: {building_name}",
            f"Location: {location}",
            f"Type: {building_type}",
            f"Height: {height} meters",
            f"Number of Floors: {floors}",
            f"Estimated Gross Floor Area: {floors * 1000} m²",
            f"Estimated Occupancy: {floors * 50} people"
        ]
        for i, spec in enumerate(specs):
            d.text((100, 780 + i*40), spec, font=font_small, fill='black')

        # 3. Environmental Analysis
        d.text((100, 1100), "3. Environmental Analysis", font=font_large, fill='black')
        
        # 3.1 Wind Analysis
        d.text((100, 1160), "3.1 Wind Analysis", font=font_medium, fill='black')
        wind_text = [
            "The wind rose diagram below illustrates the prevailing wind directions and speeds",
            "around the building. This analysis is crucial for understanding potential wind-related",
            "effects on the building's structure, energy performance, and pedestrian comfort in",
            "surrounding areas."
        ]
        for i, line in enumerate(wind_text):
            d.text((100, 1210 + i*40), line, font=font_small, fill='black')
        
        wind_img = Image.open(io.BytesIO(wind_data))
        img.paste(wind_img, (100, 1370))

        # 3.2 Sunlight Analysis
        d.text((100, 2020), "3.2 Sunlight Analysis", font=font_medium, fill='black')
        sunlight_text = [
            "The chart below shows the average daylight hours per month for the building's location.",
            "This information is valuable for assessing natural lighting potential, energy efficiency",
            "considerations, and the possible implementation of solar energy systems."
        ]
        for i, line in enumerate(sunlight_text):
            d.text((100, 2070 + i*40), line, font=font_small, fill='black')
        
        sunlight_img = Image.open(io.BytesIO(sunlight_data))
        img.paste(sunlight_img, (100, 2220))

        # 4. Recommendations
        d.text((100, 2770), "4. Recommendations", font=font_large, fill='black')
        recommendations = [
            "1. Implement wind deflection features on the building's facade to mitigate strong winds.",
            "2. Optimize window placement and sizing to maximize natural light and reduce energy costs.",
            "3. Consider installing solar panels on the roof to harness abundant sunlight.",
            "4. Develop a green roof system to improve building insulation and reduce urban heat island effect.",
            "5. Implement smart building systems to optimize energy usage based on occupancy and natural light."
        ]
        for i, rec in enumerate(recommendations):
            d.text((100, 2830 + i*40), rec, font=font_small, fill='black')

        return img

    def image_to_pdf(self, image):
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PDF')
        img_byte_arr.seek(0)
        return vkt.File.from_data(img_byte_arr.getvalue())

    def generate_wind_analysis(self):
        wind_directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        wind_speeds = [4, 3, 2, 4, 5, 3, 2, 1, 3, 4, 5, 3, 2, 3, 4, 2]

        fig = go.Figure(go.Barpolar(
            r=wind_speeds,
            theta=wind_directions,
            marker_color=vkt.Color(30, 144, 255).hex,
            marker_line_color="black",
            marker_line_width=1,
            opacity=0.8
        ))

        fig.update_layout(
            title="Wind Rose Diagram",
            font_size=16,
            polar=dict(
                radialaxis=dict(range=[0, 6], showticklabels=False, ticks=''),
                angularaxis=dict(showticklabels=True, ticks='')
            ),
            width=600,
            height=600
        )

        img_bytes = io.BytesIO()
        fig.write_image(img_bytes, format="png")
        img_bytes.seek(0)
        return img_bytes.getvalue()

    def generate_sunlight_analysis(self):
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        daylight_hours = [9.5, 10.5, 12, 13.5, 15, 15.5, 15, 14, 12.5, 11, 10, 9]

        fig = go.Figure(go.Bar(
            x=months,
            y=daylight_hours,
            marker_color=vkt.Color(255, 165, 0).hex,
            marker_line_color="black",
            marker_line_width=1,
            opacity=0.8
        ))

        fig.update_layout(
            title="Average Daylight Hours per Month",
            xaxis_title="Month",
            yaxis_title="Daylight Hours",
            font_size=16,
            width=800,
            height=500
        )

        img_bytes = io.BytesIO()
        fig.write_image(img_bytes, format="png")
        img_bytes.seek(0)
        return img_bytes.getvalue()
