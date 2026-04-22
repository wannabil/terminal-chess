"""Game loop, mode selection, and end-condition handling."""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

import chess

from .commands import handle_command
from .engine import Engine, EngineConfig, EngineUnavailable
from .render import render_board


BANNER = """\
┌──────────────────────────────────┐
│       Terminal Chess v0.1        │
└──────────────────────────────────┘"""


def _color_name(color: chess.Color) -> str:
    return "White" if color == chess.WHITE else "Black"


_SAN_PARSE_ERRORS = (
    ValueError,
    chess.IllegalMoveError,
    chess.AmbiguousMoveError,
    chess.InvalidMoveError,
)


def _normalize_san(raw: str) -> str | None:
    """Return a case-normalized SAN variant, or None if no change applies.

    - Castling: `o-o`, `0-0`, `o-o-o`, `0-0-0` (plus check/mate suffixes) → `O-O` / `O-O-O`.
    - Piece moves: lowercase leading piece letter (`nf3`, `bxe5`, `qd4`) → capitalized.
    """
    s = raw.strip()
    if not s:
        return None

    castling_check = s.upper().replace("0", "O")
    bare = castling_check.rstrip("+#")
    if bare in ("O-O", "O-O-O") and castling_check != s:
        return castling_check

    if s[0] in "nbrqk":
        return s[0].upper() + s[1:]

    return None


def parse_move(board: chess.Board, raw: str) -> chess.Move:
    """Parse SAN, accepting lowercase piece letters and `o-o` castling forms."""
    try:
        return board.parse_san(raw)
    except _SAN_PARSE_ERRORS:
        normalized = _normalize_san(raw)
        if normalized is None or normalized == raw:
            raise
        return board.parse_san(normalized)


@dataclass
class Game:
    board: chess.Board = field(default_factory=chess.Board)
    vs_computer: bool = False
    human_color: chess.Color = chess.WHITE
    engine: Optional[Engine] = None
    use_color: bool = False
    input_fn: Callable[[str], str] = input
    output_fn: Callable[[str], None] = print

    def say(self, msg: str = "") -> None:
        self.output_fn(msg)

    def ask(self, prompt: str) -> str:
        try:
            return self.input_fn(prompt)
        except EOFError:
            return ":quit"

    def render(self, last_move: chess.Move | None = None) -> None:
        perspective = self.human_color if self.vs_computer else self.board.turn
        self.say(
            render_board(
                self.board,
                perspective=perspective,
                last_move=last_move,
                use_color=self.use_color,
            )
        )

    def end_condition_message(self) -> str | None:
        if self.board.is_checkmate():
            winner = _color_name(not self.board.turn)
            return f"Checkmate! {winner} wins."
        if self.board.is_stalemate():
            return "Stalemate. Draw."
        if self.board.is_insufficient_material():
            return "Draw by insufficient material."
        if self.board.is_fivefold_repetition():
            return "Draw by fivefold repetition."
        if self.board.is_seventyfive_moves():
            return "Draw by 75-move rule."
        return None

    def _offer_claimable_draw(self) -> bool:
        if self.board.can_claim_threefold_repetition():
            ans = self.ask("Threefold repetition available. Claim draw? (y/N): ").strip().lower()
            if ans == "y":
                self.say("Draw by threefold repetition.")
                return True
        if self.board.can_claim_fifty_moves():
            ans = self.ask("Fifty-move rule available. Claim draw? (y/N): ").strip().lower()
            if ans == "y":
                self.say("Draw by fifty-move rule.")
                return True
        return False

    def _human_turn(self) -> bool:
        """Return True if the game should end after this turn."""
        while True:
            prompt = f"{_color_name(self.board.turn)} to move (e.g. e4, Nf3, O-O): "
            raw = self.ask(prompt).strip()
            if not raw:
                continue

            if raw.startswith(":"):
                result = handle_command(self, raw)
                if result.message:
                    self.say(result.message)
                if result.should_exit:
                    if result.resigned:
                        winner = _color_name(not self.board.turn)
                        self.say(f"{_color_name(self.board.turn)} resigns. {winner} wins.")
                    else:
                        self.say("Goodbye.")
                    return True
                if raw.lower().startswith(":undo"):
                    self.render()
                continue

            try:
                move = parse_move(self.board, raw)
            except _SAN_PARSE_ERRORS as exc:
                self.say(f"Illegal or unrecognized move: {exc}")
                continue

            self.board.push(move)
            self.render(last_move=move)
            if self.board.is_check() and not self.board.is_checkmate():
                self.say("Check!")
            return False

    def _engine_turn(self) -> bool:
        assert self.engine is not None
        self.say(f"{_color_name(self.board.turn)} (computer) thinking…")
        move = self.engine.get_move(self.board)
        san = self.board.san(move)
        self.board.push(move)
        self.say(f"Computer plays: {san}")
        self.render(last_move=move)
        if self.board.is_check() and not self.board.is_checkmate():
            self.say("Check!")
        return False

    def play(self) -> None:
        self.render()
        while True:
            end = self.end_condition_message()
            if end:
                self.say(end)
                return
            if self._offer_claimable_draw():
                return

            is_human_turn = (not self.vs_computer) or self.board.turn == self.human_color
            if is_human_turn:
                should_end = self._human_turn()
            else:
                should_end = self._engine_turn()

            if should_end:
                return


# ------------------------------- Setup flow -------------------------------- #


def _prompt_int(ask: Callable[[str], str], prompt: str, default: int, lo: int, hi: int) -> int:
    while True:
        raw = ask(prompt).strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError:
            print(f"Enter an integer between {lo} and {hi}.")
            continue
        if not (lo <= value <= hi):
            print(f"Out of range; expected {lo}-{hi}.")
            continue
        return value


def _prompt_color(ask: Callable[[str], str]) -> chess.Color:
    while True:
        raw = ask("Play as (w)hite / (b)lack / (r)andom: ").strip().lower()
        if raw in ("w", "white", ""):
            return chess.WHITE
        if raw in ("b", "black"):
            return chess.BLACK
        if raw in ("r", "random"):
            return random.choice([chess.WHITE, chess.BLACK])
        print("Please enter w, b, or r.")


def run_interactive(
    mode: str | None = None,
    skill: int | None = None,
    color: str | None = None,
    use_color: bool = False,
) -> int:
    print(BANNER)

    chosen_mode = mode
    if chosen_mode is None:
        print("Select mode:")
        print("  1) Two-player (hotseat)")
        print("  2) One-player vs computer")
        raw = input("> ").strip()
        chosen_mode = "2" if raw in ("2", "vs", "computer", "ai") else "1"

    vs_computer = chosen_mode in ("2", "vs", "computer", "ai")

    game = Game(vs_computer=vs_computer, use_color=use_color)

    if vs_computer:
        chosen_skill = skill if skill is not None else _prompt_int(
            input, "Difficulty (1-20, default 10): ", 10, 1, 20
        )
        if color is None:
            game.human_color = _prompt_color(input)
        elif color.lower().startswith("w"):
            game.human_color = chess.WHITE
        elif color.lower().startswith("b"):
            game.human_color = chess.BLACK
        elif color.lower().startswith("r"):
            game.human_color = random.choice([chess.WHITE, chess.BLACK])
        else:
            game.human_color = chess.WHITE

        try:
            with Engine(EngineConfig(skill=chosen_skill)) as engine:
                game.engine = engine
                game.play()
        except EngineUnavailable as exc:
            print(f"Cannot start computer opponent: {exc}")
            print("Falling back to two-player mode.")
            game.vs_computer = False
            game.engine = None
            game.play()
    else:
        game.play()

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run_interactive())
