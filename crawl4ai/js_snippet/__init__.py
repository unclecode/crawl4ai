import os


# Create a function get name of a js script, then load from the CURRENT folder of this script and return its content as string, make sure its error free
def load_js_script(script_name):
    # Get the path of the current script
    current_script_path = os.path.dirname(os.path.realpath(__file__))
    # Get the path of the script to load
    script_path = os.path.join(current_script_path, script_name + ".js")
    # Check if the script exists
    if not os.path.exists(script_path):
        raise ValueError(
            f"Script {script_name} not found in the folder {current_script_path}"
        )
    # Load the content of the script
    with open(script_path, "r") as f:
        script_content = f.read()
    return script_content
