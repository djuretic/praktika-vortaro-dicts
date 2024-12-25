# Dictionary files for Praktika Vortaro

## Generating the database

Requirements: uv

Install the dependencies, download the dictionary files and process them:

```bash
git submodule init && git submodule update
uv run cli.py process_revo
```

This will generate the sqlite database `output/vortaro.db`.

To download the most recent data files from Revo:

```bash
# you may need 'sudo apt install lynx'
./download_revo.sh
uv run cli.py process_revo
```

## Formatting code

```bash
uv tool install ruff
ruff format .
```

## Tests

```bash
pytest
```