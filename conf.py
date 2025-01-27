# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "granular-configuration-language"
copyright = "2025, Eric Jensen (lifedox@live.com)"
author = "Eric Jensen (lifedox@live.com)"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "doc_gen", "README_old.md"]
extensions = [
    "sphinx_rtd_dark_mode",
    "myst_parser",
    "sphinx.ext.autodoc",
    # "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    # "sphinx.ext.todo",
    # "sphinx.ext.coverage",
    # "sphinx.ext.mathjax",
    # "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
]

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": -1,
}
html_css_files = [
    "custom.css",
]
html_static_path = ["doc-spec/_static"]
default_dark_mode = False

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
suppress_warnings = ["myst.xref_missing"]

autodoc_type_aliases = {"Root": "Root"}
myst_heading_anchors = 7
