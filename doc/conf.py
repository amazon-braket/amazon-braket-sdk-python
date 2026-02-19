"""Sphinx configuration."""

import datetime
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

DOC_DIR = Path(__file__).parent
SCRIPT_PATH = DOC_DIR / "update_examples.py"

# Run update_examples.py to ensure example .rst files are up to date before Sphinx processes them
if SCRIPT_PATH.exists():
    print(f"--> Running example update script: {SCRIPT_PATH}")
    try:
        subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Pre-build Step Failed: {e}")
        sys.exit(1)
else:
    print(f"--> Warning: Could not find {SCRIPT_PATH}")

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
