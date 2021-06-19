# Dictionary files for Praktika Vortaro

## Generating the database

Install the dependencies, download the dictionary files and process them:

```bash
git submodule init && git submodule update
pip install pipfile
pipfile install
python vortaro.py process_revo
```

This will generate the sqlite database `output/vortaro.db`.

To download the most recent data files from Revo:

```bash
./download_revo.sh
python vortaro.py process_revo
```

## Tests

```bash
pytest
```