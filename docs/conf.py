import importlib.metadata

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

templates_path = []

source_suffix = '.rst'
master_doc = 'index'

project = 'aetcd3'
copyright = '2020, Andrey Martyanov'
author = 'Andrey Martyanov'

version = release = importlib.metadata.version('aetcd3')

autodoc_member_order = 'bysource'

html_theme = 'sphinx_rtd_theme'
html_theme_options = {}
html_static_path = []
