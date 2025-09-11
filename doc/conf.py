"""Sphinx configuration."""

import datetime
from importlib.metadata import version

# Sphinx configuration below.
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
