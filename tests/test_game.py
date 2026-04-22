import chess
import pytest

from src.commands import handle_command
from src.game import Game


def make_scripted_game(inputs, vs_computer=False):
    """Build a Game whose input_fn reads from a scripted list and captures output."""
    it = iter(inputs)
    outputs: list[str] = []

    def fake_input(prompt: str = "") -> str:
        try:
            return next(it)
        except StopIteration:
            return ":quit"

    def fake_output(msg: str = "") -> None:
        outputs.append(msg)

    game = Game(
        vs_computer=vs_computer,
        input_fn=fake_input,
        output_fn=fake_output,
    )
    return game, outputs


def test_fools_mate_checkmate_detection():
    # Fool's mate: 1. f3 e5 2. g4 Qh4#
    moves = ["f3", "e5", "g4", "Qh4#"]
    game, outputs = make_scripted_game(moves)
    game.play()
    joined = "\n".join(outputs)
    assert "Checkmate!" in joined
    assert "Black wins" in joined


def test_illegal_move_is_rejected_and_prompts_again():
    # Try an illegal move first, then a legal one, then resign.
    moves = ["e5", "e4", ":resign"]
    game, outputs = make_scripted_game(moves)
    game.play()
    joined = "\n".join(outputs)
    assert "Illegal or unrecognized move" in joined
    # After resignation White's turn ends → Black wins (since white resigned on move 2).
    assert "resigns" in joined


def test_castling_kingside_is_accepted():
    # Prepare a board where white can castle kingside.
    board = chess.Board()
    for san in ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5"]:
        board.push_san(san)
    game, outputs = make_scripted_game(["O-O", ":quit"])
    game.board = board
    game.play()
    joined = "\n".join(outputs)
    # After O-O the king should be on g1.
    assert game.board.piece_at(chess.G1) and game.board.piece_at(chess.G1).piece_type == chess.KING


def test_stalemate_detection():
    # Set up a classic stalemate: black king on h8, white queen on g6, white king on f7, black to move.
    board = chess.Board("7k/5K2/6Q1/8/8/8/8/8 b - - 0 1")
    game, outputs = make_scripted_game([])
    game.board = board
    game.play()
    joined = "\n".join(outputs)
    assert "Stalemate" in joined


def test_en_passant_is_legal_via_san():
    board = chess.Board()
    for san in ["e4", "a6", "e5", "d5"]:
        board.push_san(san)
    # White should now be able to play exd6 en passant.
    move = board.parse_san("exd6")
    assert move in board.legal_moves


def test_help_command_returns_help_text():
    game, _ = make_scripted_game([])
    result = handle_command(game, ":help")
    assert result.handled
    assert ":resign" in result.message


def test_fen_command_returns_current_fen():
    game, _ = make_scripted_game([])
    result = handle_command(game, ":fen")
    assert result.handled
    assert result.message == game.board.fen()


def test_undo_reverts_last_move():
    game, _ = make_scripted_game([])
    game.board.push_san("e4")
    assert game.board.move_stack
    result = handle_command(game, ":undo")
    assert result.handled
    assert not game.board.move_stack


def test_history_reports_moves():
    game, _ = make_scripted_game([])
    for san in ["e4", "e5", "Nf3"]:
        game.board.push_san(san)
    result = handle_command(game, ":history")
    assert "e4" in result.message
    assert "Nf3" in result.message


def test_unknown_command_returns_error():
    game, _ = make_scripted_game([])
    result = handle_command(game, ":banana")
    assert result.handled
    assert "Unknown command" in result.message
