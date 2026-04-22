"""Thin Stockfish wrapper using python-chess's UCI support."""

from __future__ import annotations

import shutil
from dataclasses import dataclass

import chess
import chess.engine


class EngineUnavailable(RuntimeError):
    """Raised when no Stockfish binary can be located."""


@dataclass
class EngineConfig:
    skill: int = 10  # 0 (weakest) … 20 (strongest)
    move_time: float = 0.5  # seconds per move
    depth: int | None = None  # if set, overrides move_time


class Engine:
    """Context-manageable Stockfish wrapper.

    Usage:
        with Engine(EngineConfig(skill=8)) as eng:
            move = eng.get_move(board)
    """

    def __init__(self, config: EngineConfig | None = None, binary: str | None = None) -> None:
        self.config = config or EngineConfig()
        path = binary or shutil.which("stockfish")
        if path is None:
            raise EngineUnavailable(
                "stockfish binary not found on PATH. Install with `brew install stockfish` "
                "or download from https://stockfishchess.org/download/."
            )
        self._path = path
        self._engine: chess.engine.SimpleEngine | None = None

    def __enter__(self) -> "Engine":
        self._engine = chess.engine.SimpleEngine.popen_uci(self._path)
        skill = max(0, min(20, self.config.skill))
        try:
            self._engine.configure({"Skill Level": skill})
        except chess.engine.EngineError:
            pass
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._engine is not None:
            try:
                self._engine.quit()
            finally:
                self._engine = None

    def get_move(self, board: chess.Board) -> chess.Move:
        if self._engine is None:
            raise RuntimeError("Engine not started — use as a context manager.")
        if self.config.depth is not None:
            limit = chess.engine.Limit(depth=self.config.depth)
        else:
            limit = chess.engine.Limit(time=self.config.move_time)
        result = self._engine.play(board, limit)
        if result.move is None:
            raise RuntimeError("Engine returned no move.")
        return result.move
