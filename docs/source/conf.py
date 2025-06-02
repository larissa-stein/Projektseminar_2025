# Configuration file for the Sphinx documentation builder.

import os
import sys

# -- Path setup --------------------------------------------------------------

sys.path.insert(0, os.path.abspath('../..'))  # Projektroot hinzufügen
sys.path.insert(0, os.path.abspath('../../src')) # Add the 'src' directory to sys.path so modules can be imported directly

# -- Project information -----------------------------------------------------

project = 'Projektseminar'
copyright = '2025, Larissa Stein'
author = 'Larissa Stein'
release = '1.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',     # Automatic documentation from docstrings
    'sphinx.ext.napoleon',    # Support for Google and NumPy style docstrings
    'sphinx_rtd_theme',       # Read the Docs theme
    'sphinxcontrib.mermaid',  # Mermaid diagrams
    'sphinx.ext.viewcode',    # Add links to source code
]

templates_path = ['_templates']
exclude_patterns = []

# Sort members in the order they appear in the source code
autodoc_member_order = 'bysource'

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
