import chess

from src.render import render_board


def test_starting_position_contains_all_pieces():
    board = chess.Board()
    out = render_board(board)
    # White and black pieces present.
    for glyph in "♖♘♗♕♔♙♜♞♝♛♚♟":
        assert glyph in out
    # File labels on top and bottom.
    assert out.startswith("  a b c d e f g h")
    assert out.strip().endswith("a b c d e f g h")
    # Exactly 10 lines: 8 ranks + two file-label rows.
    assert len(out.splitlines()) == 10


def test_perspective_black_flips_file_order():
    board = chess.Board()
    white_view = render_board(board, perspective=chess.WHITE).splitlines()[0]
    black_view = render_board(board, perspective=chess.BLACK).splitlines()[0]
    assert white_view != black_view
    assert black_view.strip().split() == list("hgfedcba")


def test_empty_square_glyph():
    board = chess.Board()
    # The middle ranks should contain the empty-square marker.
    out = render_board(board)
    assert "·" in out
