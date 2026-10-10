# Diana Agent

A local AI assistant for the **Hitman World of Assassination** trilogy, in the
voice of Diana Burnwood, Agent 47's handler. Ask her about missions, targets,
Steam achievements, Silent Assassin / Suit Only challenges, game mechanics and
story. Everything runs on your own machine through [Ollama](https://ollama.com).
No API keys and no cloud.

## Features

- **Chat with Diana.** Answers in character, with dry British wit.
- **Mission browser.** A sidebar with Hitman 1, 2 and 3. Expand a game to see
  every mission with its location, and hover over a mission to see its targets.
- **Grounded answers.** Mission, target and achievement facts come from local
  data files through tool calls, not from the model's memory. Game terms and
  story come from editable lore files, so the model doesn't have to guess.
- **Easy to extend.** Fix or add knowledge by editing JSON and Markdown files.
  No retraining.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) with a model that supports tool calling
  (default: `qwen3:8b`, about 5 GB)
- No GPU required. On a CPU, expect a few seconds per answer.

## Setup

```bash
git clone https://github.com/twasiel/Diana-Agent
cd Diana-Agent

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

ollama pull qwen3:8b
```

## Usage

Make sure Ollama is running (`ollama serve`), then:

```bash
python main.py          # GUI in its own window
python main.py --cli    # chat in the terminal instead
```

### Configuration

Environment variables:

| Variable       | Default    | Description                                                                  |
|----------------|------------|------------------------------------------------------------------------------|
| `DIANA_MODEL`  | `qwen3:8b` | Any Ollama model with tool support. Try `qwen3:4b` on slower machines.       |
| `DIANA_THINK`  | `1`        | `0` turns off the model's reasoning step: faster, but weaker answers.        |

```bash
DIANA_MODEL=qwen3:4b DIANA_THINK=0 python main.py
```

## Project structure

```
main.py          GUI (Flet) and terminal chat
agent.py         The model: system prompt, tools, data loading and chat loop
targets/         Missions per game: location, mission, achievement, targets
  hitman1.jsonc
  hitman2.jsonc
  hitman3.jsonc
lore/            Background knowledge the model answers from
  ratings-and-challenges.md
  mechanics.md
  game-modes.md
  story.md
  diana-voice.md   Diana's persona and example replies
```

## Adding knowledge

**Missions** go in `targets/<game>.jsonc`, keyed by location:

```jsonc
{
    "Paris": {
        "mission": "The Showstopper",
        "achievement": "When No One Else Dares",
        "targets": ["Viktor Novikov", "Dalia Margolis"]
    }
}
```

Comments (`//`) and trailing commas are allowed. A new `targets/*.jsonc` file
appears as a new card in the sidebar.

**Lore** is any Markdown file in `lore/`. All of them are added to the model's
instructions at startup. To change how Diana talks, add example exchanges to
`lore/diana-voice.md`.

Restart the app after editing either folder.

## Troubleshooting

- **"Connection lost" in the chat:** Ollama isn't running. Start it with `ollama serve`.
- **Answers are slow:** use a smaller model (`DIANA_MODEL=qwen3:4b`) or set
  `DIANA_THINK=0`.
- **NixOS:** Flet downloads a prebuilt desktop client, which needs
  `programs.nix-ld` with these libraries:
  ```nix
  programs.nix-ld = {
    enable = true;
    libraries = with pkgs; [
      stdenv.cc.cc.lib zlib glib gtk3 pango cairo gdk-pixbuf atk
      harfbuzz libepoxy fontconfig freetype libGL xorg.libX11 libsecret
    ];
  };
  ```
- **No window opens:** to run in the browser instead, change the last line
  of `main.py` to `ft.run(gui, view=ft.AppView.WEB_BROWSER, port=8550)`.

## License

[MIT](LICENSE). The license covers this project's code and text only, not
HITMAN or any IO Interactive property.

## Disclaimer

A fan project, not affiliated with or endorsed by IO Interactive. HITMAN and
all related names are trademarks of IO Interactive A/S.
