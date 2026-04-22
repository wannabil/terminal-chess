"""Board rendering with Unicode pieces and coordinate labels."""

from __future__ import annotations

import chess

UNICODE_PIECES = {
    chess.PAWN: ("♙", "♟"),
    chess.KNIGHT: ("♘", "♞"),
    chess.BISHOP: ("♗", "♝"),
    chess.ROOK: ("♖", "♜"),
    chess.QUEEN: ("♕", "♛"),
    chess.KING: ("♔", "♚"),
}

EMPTY_SQUARE = "·"


def piece_glyph(piece: chess.Piece) -> str:
    white, black = UNICODE_PIECES[piece.piece_type]
    return white if piece.color == chess.WHITE else black


def render_board(
    board: chess.Board,
    *,
    perspective: chess.Color = chess.WHITE,
    last_move: chess.Move | None = None,
    use_color: bool = False,
) -> str:
    ranks = range(7, -1, -1) if perspective == chess.WHITE else range(0, 8)
    files = range(0, 8) if perspective == chess.WHITE else range(7, -1, -1)

    file_labels = "  " + " ".join("abcdefgh"[f] for f in files)
    lines: list[str] = [file_labels]

    highlight_squares: set[int] = set()
    if last_move is not None:
        highlight_squares.add(last_move.from_square)
        highlight_squares.add(last_move.to_square)

    for rank in ranks:
        row_cells: list[str] = []
        for file in files:
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            glyph = piece_glyph(piece) if piece else EMPTY_SQUARE
            if use_color and square in highlight_squares:
                glyph = f"\x1b[33m{glyph}\x1b[0m"
            row_cells.append(glyph)
        rank_label = str(rank + 1)
        lines.append(f"{rank_label} {' '.join(row_cells)} {rank_label}")

    lines.append(file_labels)
    return "\n".join(lines)
