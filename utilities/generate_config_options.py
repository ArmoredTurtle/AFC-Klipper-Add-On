#!/usr/bin/env python3

import os
import re

def extract_config_options(directory):
    config_options = {}
    config_pattern = re.compile(r'config\.\w+\(\s*[\'\"](\w+)[\'\"]\s*,\s*([^\)]+)\s*\)\s*#\s*(.*)')

    for filename in os.listdir(directory):
        if filename.endswith('.py'):
            with open(os.path.join(directory, filename), 'r') as file:
                content = file.read()
                matches = config_pattern.findall(content)
                if matches:
                    config_options[filename] = matches

    return config_options

def generate_documentation(config_options):
    documentation = "# Configuration Options Documentation\n\n"
    for filename, options in config_options.items():
        filename_without_extension = os.path.splitext(filename)[0]
        documentation += f"## {filename_without_extension}\n"
        for option, default, description in options:
            documentation += f"- `{option}` (default: `{default}`): {description}\n"
        documentation += "\n"
    return documentation

def main():
    directory = '../extras'
    config_options = extract_config_options(directory)
    documentation = generate_documentation(config_options)
    with open('../docs/CONFIGURATION_OPTIONS.md', 'w') as doc_file:
        doc_file.write(documentation)

if __name__ == "__main__":
    main()