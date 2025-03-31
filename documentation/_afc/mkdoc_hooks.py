import logging
import re
import os

logger = logging.getLogger("mkdocs.mkdocs_hooks.post_page")

def post_page(output: str, page, config):
    modified_output = re.sub(r"cmd_(\w+)", r"\1", output)
    logger.debug(f"[mkdocs_hooks] removed cmd_ from {page.file.src_path}")
    return modified_output

def force_reload(server, config, builder):
    """Force reload if markdown files are changed."""
    markdown_dir = os.path.join(config['docs_dir'])

    def reload_on_markdown_change(filepath):
        if filepath.endswith('.md'):
            logger.info(f"[mkdocs_hooks] Markdown file changed: {filepath}. Forcing reload.")
            builder() # Force a rebuild
    server.watch(markdown_dir, reload_on_markdown_change)
    return server