"""Slash commands available during play."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

import chess
import chess.pgn

if TYPE_CHECKING:
    from .game import Game


HELP_TEXT = """\
Commands:
  :help          Show this help
  :history       List moves played so far
  :fen           Print current FEN
  :pgn           Print game history as PGN
  :undo          Undo last move (or last two vs computer)
  :resign        Resign the game
  :quit          Exit without resigning

Move entry uses Standard Algebraic Notation:
  e4, Nf3, Bxe5, exd5, O-O, O-O-O, e8=Q, Qxd5+, Raxe1#
"""


@dataclass
class CommandResult:
    handled: bool
    message: str = ""
    should_exit: bool = False
    resigned: bool = False


def _history(game: "Game") -> str:
    if not game.board.move_stack:
        return "(no moves yet)"
    # Reconstruct SAN history by replaying from the initial position.
    replay = chess.Board()
    sans: list[str] = []
    for move in game.board.move_stack:
        sans.append(replay.san(move))
        replay.push(move)

    lines: list[str] = []
    for i in range(0, len(sans), 2):
        move_no = i // 2 + 1
        white = sans[i]
        black = sans[i + 1] if i + 1 < len(sans) else ""
        lines.append(f"{move_no:>3}. {white:<8} {black}")
    return "\n".join(lines)


def _pgn(game: "Game") -> str:
    pgn_game = chess.pgn.Game()
    pgn_game.headers["Event"] = "Terminal Chess"
    node: chess.pgn.GameNode = pgn_game
    replay = chess.Board()
    for move in game.board.move_stack:
        node = node.add_variation(move)
        replay.push(move)
    return str(pgn_game)


def _undo(game: "Game") -> str:
    if not game.board.move_stack:
        return "Nothing to undo."
    steps = 2 if game.vs_computer and len(game.board.move_stack) >= 2 else 1
    for _ in range(steps):
        if game.board.move_stack:
            game.board.pop()
    return f"Undid {steps} move{'s' if steps > 1 else ''}."


COMMANDS: dict[str, Callable[["Game"], CommandResult]] = {
    ":help": lambda g: CommandResult(True, HELP_TEXT),
    ":history": lambda g: CommandResult(True, _history(g)),
    ":fen": lambda g: CommandResult(True, g.board.fen()),
    ":pgn": lambda g: CommandResult(True, _pgn(g)),
    ":undo": lambda g: CommandResult(True, _undo(g)),
    ":resign": lambda g: CommandResult(True, "", should_exit=True, resigned=True),
    ":quit": lambda g: CommandResult(True, "", should_exit=True, resigned=False),
    ":exit": lambda g: CommandResult(True, "", should_exit=True, resigned=False),
}


def handle_command(game: "Game", text: str) -> CommandResult:
    if not text.startswith(":"):
        return CommandResult(handled=False)
    key = text.strip().split()[0].lower()
    handler = COMMANDS.get(key)
    if handler is None:
        return CommandResult(True, f"Unknown command: {key}. Try :help.")
    return handler(game)
