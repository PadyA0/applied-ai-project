"""Tests for render_table -- the ASCII table renderer in main.py.

render_table wraps any cell wider than its column and stacks the wrapped lines
so columns stay aligned. These tests cover the structural output and the
wrapping branch.
"""

from src.main import render_table


def test_headers_and_values_appear():
    table = render_table(["A", "B"], [["one", "two"]], [5, 5])
    assert "A" in table
    assert "one" in table
    assert "two" in table


def test_has_border_and_header_separator():
    table = render_table(["A"], [["x"]], [3])
    lines = table.splitlines()
    assert lines[0].startswith("+") and lines[0].endswith("+")
    # The header underline uses '=' instead of '-'.
    assert any(set(line) <= {"+", "="} and "=" in line for line in lines)


def test_long_cell_wraps_onto_multiple_lines():
    # "aaaa bbbb" is 9 chars; a width-4 column forces two physical lines.
    table = render_table(["H"], [["aaaa bbbb"]], [4])
    assert "aaaa" in table
    assert "bbbb" in table
    # The wrapped word should land on its own line, not the header's.
    lines = table.splitlines()
    aaaa_line = next(i for i, l in enumerate(lines) if "aaaa" in l)
    bbbb_line = next(i for i, l in enumerate(lines) if "bbbb" in l)
    assert bbbb_line == aaaa_line + 1


def test_empty_rows_still_render_header():
    table = render_table(["Only"], [], [4])
    assert "Only" in table


def test_row_count_reflected_in_dividers():
    # One divider on top, one after the header, one after each row.
    table = render_table(["H"], [["a"], ["b"], ["c"]], [3])
    divider_lines = [l for l in table.splitlines() if set(l) <= {"+", "-", "="}]
    assert len(divider_lines) == 2 + 3  # top + header sep + one per row
