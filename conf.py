# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from __future__ import annotations

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = "granular-configuration-language"
copyright = "2025, Eric Jensen (eric.jensen42@gmail.com)"
author = "Eric Jensen (eric.jensen42@gmail.com)"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "doc_gen", "README_old.md"]
extensions = [
    "myst_parser",
    "sphinx_copybutton",
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

html_baseurl = "README.html"
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

autodoc_type_aliases = {
    "Root": "Root",
    "granular_configuration_language.yaml.classes.Root": "Root",
}
myst_heading_anchors = 7

nitpicky = True
nitpick_ignore = [
    ("py:class", "optional"),
    # From from collections.abc
    ("py:class", "(k, v), remove and return some (key, value) pair"),
    ("py:class", "a set-like object providing a view on D's items"),
    ("py:class", "a set-like object providing a view on D's keys"),
    ("py:class", "an object providing a view on D's values"),
    ("py:class", "D.get(k,d), also set D[k]=d if k not in D"),
    ("py:class", "D[k] if k in D, else d.  d defaults to None."),
    ("py:class", "None.  Remove all items from D."),
    ("py:class", "None.  Update D from mapping/iterable E and F."),
    ("py:class", "v, remove specified key and return the corresponding value."),
]

# Patching that makes sphinx 8.2.0 and 8.2.1 work

from sphinx.util import inspect  # noqa: E402

inspect.TypeAliasForwardRef.__repr__ = lambda self: self.name  # type: ignore
