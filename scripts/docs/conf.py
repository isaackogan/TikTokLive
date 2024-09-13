# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import importlib
import json
# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

manifest = json.loads(open("../../manifest.json", "r").read())
version = "v" + manifest["version"]

sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------

project = 'TikTokLive'
copyright = '2022, Isaac Kogan'
author = 'Isaac Kogan'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "myst_parser",
    "sphinx_rtd_theme",
    'sphinx_search.extension',
]

html_logo = "logo.png"

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

html_theme = "furo"
html_title = project + " " + version

print("Building for version", html_title)

html_theme_options = {
    "light_css_variables": {
    },
    "dark_css_variables": {
        "color-problematic": "#80aeef",
        "sidebar-filter": "invert(0.95)"
    }
}

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', "tiktok_schema_pb2.py", "./README.md"]

# -- Options for HTML output -------------------------------------------------

html_css_files = [
    "css/custom.css"
]
html_js_files = [
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['static']
html_permalinks_icon = "#"

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown"
}
