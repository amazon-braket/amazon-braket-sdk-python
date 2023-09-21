"""Sphinx configuration."""
import datetime

import pkg_resources

# Sphinx configuration below.
project = "amazon-braket-sdk"
version = pkg_resources.require(project)[0].version
release = version
copyright = "{}, Amazon.com".format(datetime.datetime.now().year)

extensions = [
    "sphinxcontrib.apidoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "nbsphinx",
    "myst_nb",
    "sphinx_design",
]

nb_execution_mode = 'off'

myst_enable_extensions = ["colon_fence"]

source_suffix = ['.rst', '.md']
master_doc = "index"

autoclass_content = "both"
autodoc_member_order = "bysource"
default_role = "py:obj"

html_static_path = ["_static"]
html_theme = "sphinx_book_theme"
html_logo = "_static/aws.png"
html_title = "Amazon Braket Python SDK"
htmlhelp_basename = "{}doc".format(project)

language = "en"

napoleon_use_rtype = False

apidoc_module_dir = "../src/braket"
apidoc_output_dir = "_apidoc"
apidoc_excluded_paths = ["../test"]
apidoc_separate_modules = True
apidoc_module_first = True
apidoc_extra_args = ["-f", "--implicit-namespaces", "-H", "API Reference"]
