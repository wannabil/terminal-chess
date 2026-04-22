"""CLI entry point for terminal-chess."""

from __future__ import annotations

import sys

import click

from .game import run_interactive


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--mode",
    type=click.Choice(["two", "vs", "1", "2"], case_sensitive=False),
    default=None,
    help="Game mode: 'two' for two-player, 'vs' for vs-computer. Prompts if omitted.",
)
@click.option(
    "--skill",
    type=click.IntRange(1, 20),
    default=None,
    help="Stockfish skill level 1-20 (only with --mode vs).",
)
@click.option(
    "--color",
    type=click.Choice(["white", "black", "random", "w", "b", "r"], case_sensitive=False),
    default=None,
    help="Which side to play vs the computer.",
)
@click.option("--no-color", is_flag=True, help="Disable last-move highlighting.")
@click.option("--blindfold", is_flag=True, help="Play without the board rendered.")
def main(
    mode: str | None,
    skill: int | None,
    color: str | None,
    no_color: bool,
    blindfold: bool,
) -> None:
    """Terminal Chess — play chess in your terminal."""
    # Normalize numeric mode to named.
    if mode == "1":
        mode = "two"
    elif mode == "2":
        mode = "vs"

    rc = run_interactive(
        mode=mode,
        skill=skill,
        color=color,
        use_color=not no_color,
        blindfold=blindfold,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
