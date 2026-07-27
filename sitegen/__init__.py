"""The display layer: parser output in, static HTML out.

Nothing in this package reads TEI. It consumes the plain dictionaries that
``pipeline.parse_tei`` produces -- and only what that module's docstring
promises -- so the whole package can be thrown away and rewritten without the
parser noticing. That separation is the point of the project.

Modules::

    html      escaping and element assembly, used by everything else
    dates     parser date dicts -> honest Danish date strings
    tei_html  a letter's body node tree -> HTML
    pages     whole HTML documents, as plain Python string functions
    site      what a build is: view models, file layout, writing the files
"""
