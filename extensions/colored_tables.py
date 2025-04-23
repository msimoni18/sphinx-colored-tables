import csv
from docutils import nodes
from docutils.parsers.rst.directives.tables import CSVTable
from sphinx.util import logging
from sphinx.writers.html import HTMLTranslator
from sphinx.writers.latex import LaTeXTranslator as BaseLaTeXTranslator

logger = logging.getLogger(__name__)


class ColoredCSVTable(CSVTable):
    option_spec = dict(CSVTable.option_spec)
    option_spec["color-column"] = str
    option_spec["color-map"] = lambda x: dict(
        item.strip().split("=") for item in x.split(",")
    )

    def run(self):

        table_nodes = super().run()

        color_col = self.options.get("color-column")
        if color_col is None:
            logger.warning("Missing 'color-column' option for csv-table.")
            return table_nodes

        color_map = self.options.get("color-map", {})

        # Find the table node
        table = None
        for node in table_nodes:
            if isinstance(node, nodes.table):
                table = node
                break

        if table is None:
            return table_nodes  # Fallback in case structure changed

        # Find column index
        header_row = table.traverse(nodes.thead)[0][0]
        header_cells = [cell.astext() for cell in header_row.traverse(nodes.entry)]
        try:
            color_col_index = int(color_col)
        except ValueError:
            if color_col not in header_cells:
                logger.warning(f"Color column '{color_col}' not found in header.")
                return table_nodes
            color_col_index = header_cells.index(color_col)

        # Modify tbody entries
        for row in table.traverse(nodes.tbody)[0].traverse(nodes.row):
            entries = row.traverse(nodes.entry)
            if color_col_index < len(entries):
                cell = entries[color_col_index]
                category = cell.astext().strip()
                css_class = f"color-{category.lower().replace(' ', '-')}"
                cell["classes"].append(css_class)
                cell["latex_color"] = color_map.get(category, "gray!20")

        return table_nodes

    def _read_csv(self, filename):
        """Read and process CSV data."""
        try:
            with open(filename, encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                return list(reader)
        except Exception as err:
            logger.error("Error reading CSV file: %s", err)
            return []


# HTML hooks
def visit_entry_html(self, node):
    classes = node.get("classes", [])
    class_attr = f' class="{" ".join(classes)}"' if classes else ""
    self.body.append(f"<td{class_attr}>")


def depart_entry_html(self, node):
    self.body.append("</td>\n")


# Patch LaTeX hook safely
def setup(app):
    app.add_directive("colored-csv-table", ColoredCSVTable)

    HTMLTranslator.visit_entry = visit_entry_html
    HTMLTranslator.depart_entry = depart_entry_html

    original_visit_entry = BaseLaTeXTranslator.visit_entry

    def patched_visit_entry(self, node):
        if "latex_color" in node:
            for i, child in enumerate(node):
                if isinstance(child, nodes.paragraph):
                    # NOTE: If there's more than one child,
                    # only the last will be used.
                    # TODO: Figure out cases where more than
                    # one child is expected and how to handle
                    # them.
                    for _, text in enumerate(child):
                        para = nodes.raw(
                            "",
                            rf"\cellcolor{{{node['latex_color']}}} {text}",
                            format="latex",
                        )
                    child[i] = para

        original_visit_entry(self, node)

    BaseLaTeXTranslator.visit_entry = patched_visit_entry

    def add_latex_package(app, config):
        preamble = app.config.latex_elements.get("preamble", "")
        if "xcolor" not in preamble:
            app.config.latex_elements["preamble"] = (
                preamble + "\n\\usepackage[table]{xcolor}"
            )

    app.connect("config-inited", add_latex_package)

    return {
        "version": "0.5",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
