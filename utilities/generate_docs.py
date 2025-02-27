#!/usr/bin/env python3

import ast
import os
import importlib.util
import sys


def extract_cmd_functions(file_path):
    cmd_functions = []
    try:
        with open(file_path, 'r') as file:
            tree = ast.parse(file.read(), filename=file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('cmd_'):
                docstring = ast.get_docstring(node)
                if docstring and "NO_DOC" not in docstring:
                    cmd_functions.append((node.name, docstring))
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return cmd_functions



def parse_macros(file_path):
    macros = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            current_macro = None
            for line in lines:
                if line.startswith('[gcode_macro '):
                    if current_macro:
                        macros.append(current_macro)
                    current_macro = {'name': line.strip()[1:-1], 'description': '', 'gcode': ''}
                elif current_macro:
                    if line.startswith('description:'):
                        current_macro['description'] = line.split(':', 1)[1].strip()
                    elif line.startswith('gcode:'):
                        current_macro['gcode'] = line.split(':', 1)[1].strip()
                    elif line.strip():
                        current_macro['gcode'] += '\n' + line.strip()
            if current_macro:
                macros.append(current_macro)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return macros


def generate_macro_docs(macros):
    markdown_lines = [
        "## AFC Macros\n",
        "\n",
        "The following macros are defined in the `config/macros/AFC_macros.cfg` file.\n",
        "These macros can be executed either from the console, called from another macro, or triggered through \n",
        "the Mainsail or Fluidd web interfaces.\n",
        "\n"
    ]
    for macro in macros:
        macro_name = macro['name'].replace('gcode_macro ', '')
        markdown_lines.append(f"### {macro_name}\n")
        markdown_lines.append(f"_Description_: {macro['description']}\n")
    return markdown_lines


def format_markdown(cmd_functions):
    markdown_lines = [
        "# AFC Klipper Add-On Command Reference\n",
        "\n",
        "## Built-in AFC Functions\n",
        "\n",
        "The following commands are built-in the AFC-Klipper-Add-On and are available through \n",
        "the Klipper console.\n",
        "\nNOTE: LANE/HUB/BUFFER etc. names are case sensitive and should exactly match the names defined in config files",
        "\n"
    ]
    for name, docstring in cmd_functions:
        description = docstring.split('\n\n')[0].replace("<nl>", "")
        command_name = name[4:].upper()  # Remove 'cmd_' prefix and convert to uppercase
        markdown_lines.append(f"### {command_name}\n")
        markdown_lines.append(f"_Description_: {description}  \n  \n")

        # Extract usage and example from docstring if available
        usage = ""
        example = ""
        for line in docstring.split('\n'):
            if line.strip().startswith("Usage:"):
                usage = line.strip().replace("Usage:", "").strip()
            if line.strip().startswith("Example:"):
                example = line.strip().replace("Example:", "").strip()

        if usage:
            markdown_lines.append(f"Usage: `{usage}`  \n")
        else:
            markdown_lines.append(f"Usage: `{command_name} LANE=<lane>`  \n")

        if example:
            markdown_lines.append(f"Example: `{example}`  \n")
        else:
            markdown_lines.append(f"Example: `{command_name} LANE=lane1`  \n")

        markdown_lines.append("\n")  # Add an extra newline for separation
    return markdown_lines

def write_markdown_file(markdown_lines, output_file):
    with open(output_file, 'w') as file:
        file.writelines(markdown_lines)


def check_ast_module():
    if importlib.util.find_spec("ast") is None:
        print("Error: The 'ast' module is not installed.")
        sys.exit(1)


def main():
    source_dir = '..'
    output_file = '../docs/command_reference.md'

    all_cmd_functions = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                cmd_functions = extract_cmd_functions(file_path)
                all_cmd_functions.extend(cmd_functions)

    all_cmd_functions.sort(key=lambda e: e[0])
    markdown_lines = format_markdown(all_cmd_functions)

    write_markdown_file(markdown_lines, output_file)

    macros = parse_macros('../config/macros/AFC_macros.cfg')
    macro_docs = generate_macro_docs(macros)

    # Append macro docs to the markdown file
    with open('../docs/command_reference.md', 'a') as md_file:
        md_file.writelines(macro_docs)

if __name__ == "__main__":
    check_ast_module()
    main()
