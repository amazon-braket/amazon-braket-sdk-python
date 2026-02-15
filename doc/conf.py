"""Sphinx configuration."""

import datetime
from importlib.metadata import version



# Sphinx configuration below.
import os
import sys

# Configure sys.path so we can import our generator script
conf_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, conf_dir)

try:
    import generate_examples
    # Generate example RST files from ENTRIES.json
    print("Generating example RST files from ENTRIES.json...")
    entries = generate_examples.fetch_entries()
    generate_examples.generate_rst(entries, conf_dir)
    print("Successfully generated example RST files.")
except Exception as e:
    print(f"Error generating examples: {e}")

project = "amazon-braket-sdk"
version = version(project)
release = version
copyright = f"{datetime.datetime.now().year}, Amazon.com"

extensions = [
    "sphinxcontrib.apidoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx_autodoc_typehints",
]

source_suffix = ".rst"
root_doc = "index"

autoclass_content = "both"
autodoc_member_order = "bysource"
default_role = "py:obj"

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "prev_next_buttons_location": "both",
}
htmlhelp_basename = f"{project}doc"

language = "en"

napoleon_use_rtype = False
napoleon_google_docstring = True
napoleon_numpy_docstring = False

apidoc_module_dir = "../src/braket"
apidoc_output_dir = "_apidoc"
apidoc_excluded_paths = ["../test"]
apidoc_separate_modules = True
apidoc_module_first = True
apidoc_extra_args = ["-f", "--implicit-namespaces", "-H", "API Reference"]

typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True