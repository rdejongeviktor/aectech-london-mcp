import viktor as vkt
import json

def execute():

    from viktor.external.generic import GenericAnalysis

    input_dict = {
        'job': 'get-tools',
        'tool_name': None,
        'tool-args': None,
    }

    # Generate the input file(s)
    files = [
        ('input.json', vkt.File.from_data(json.dumps(input_dict))),
    ]

    # Run the analysis and obtain the output file.
    generic_analysis = GenericAnalysis(files=files, executable_key="mcp", output_filenames=["output.json"])
    generic_analysis.execute(timeout=60)
    output_file = generic_analysis.get_output_file("output.json")

    return output_file
