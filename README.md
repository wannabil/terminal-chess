# Terminal Chess

A local terminal chess game with full FIDE rule enforcement, algebraic-notation
move entry, Unicode board rendering, two-player hotseat mode, and a one-player
mode against Stockfish.

Rules, move generation, and engine protocol all rely on
[`python-chess`](https://python-chess.readthedocs.io/) — this project handles
the CLI, rendering, and game loop only.

```
  a b c d e f g h
8 ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜ 8
7 ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟ 7
6 · · · · · · · · 6
5 · · · · · · · · 5
4 · · · · ♙ · · · 4
3 · · · · · · · · 3
2 ♙ ♙ ♙ ♙ · ♙ ♙ ♙ 2
1 ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖ 1
  a b c d e f g h
```

## Install

### 1. Install Stockfish (only required for computer mode)

**macOS**

```sh
brew install stockfish
```

**Linux**

```sh
sudo apt-get install stockfish    # Debian/Ubuntu
sudo pacman -S stockfish           # Arch
```

**Manual**

Download a binary from <https://stockfishchess.org/download/> and place it on
your `PATH` as `stockfish`, e.g.:

```sh
sudo mv stockfish /usr/local/bin/stockfish
chmod +x /usr/local/bin/stockfish
```

### 2. Install Python dependencies

```sh
git clone https://github.com/<you>/terminal-chess.git
cd terminal-chess
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Play

From the project root with the venv active:

```sh
python -m src.main                          # prompts for mode
python -m src.main --mode two               # two-player hotseat
python -m src.main --mode vs --skill 8      # vs Stockfish at skill 8
python -m src.main --mode vs --color black  # play as Black
```

## Move entry

Moves are entered in Standard Algebraic Notation (SAN):

| Input   | Meaning                         |
|---------|---------------------------------|
| `e4`    | Pawn to e4                      |
| `Nf3`   | Knight to f3                    |
| `Bxe5`  | Bishop captures on e5           |
| `exd5`  | Pawn on e-file captures on d5   |
| `O-O`   | Kingside castle                 |
| `O-O-O` | Queenside castle                |
| `e8=Q`  | Promote to queen                |
| `Qxd5+` | Queen captures with check       |
| `Raxe1#`| Disambiguated rook mate         |

## Slash commands

| Command      | Effect                                           |
|--------------|--------------------------------------------------|
| `:help`      | Show commands + notation reference               |
| `:history`   | List moves played so far                         |
| `:fen`       | Print current FEN                                |
| `:pgn`       | Print game history as PGN                        |
| `:undo`      | Undo last move (or last two vs computer)         |
| `:resign`    | Resign the game                                  |
| `:quit`      | Exit without resigning                           |

## Tests

```sh
source .venv/bin/activate
pip install pytest
pytest
```

## Roadmap

- Save/load PGN files
- Time controls
- Post-game engine analysis
- Puzzle mode

## License

MIT.
