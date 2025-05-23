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
myst_enable_extensions = [
    "colon_fence",
    "attrs_inline",
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

autodoc_type_aliases = {
    "Root": "Root",
    "granular_configuration_language.yaml.classes.Root": "Root",
}
myst_heading_anchors = 7
myst_footnote_sort = False

# Looks better that single wrapping, but how line length calculation is obtuse and aggressive.
#
# 90 seems like the HTML width, but
# 55 gets `granular_configuration_language.yaml.file_ops.EagerIOTextFile` to multi-line, but
# `Configuration.__getattr__` wraps even at 80
python_maximum_signature_line_length = 55

# add_module_names = False

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
# Done weirding to hide the evil from pyright and mypy
import importlib  # noqa: E402

importlib.import_module("sphinx.util").inspect.TypeAliasForwardRef.__repr__ = lambda self: self.name
