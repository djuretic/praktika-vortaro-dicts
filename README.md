# Dictionary files for Praktika Vortaro

## Generating the database

Install the dependencies, download the dictionary files and process them:

```bash
git submodule init && git submodule update
pip install pipenv
pipenv install
# if using pyenv
pyenv rehash
praktika_vortaro process_revo
```

This will generate the sqlite database `output/vortaro.db`.

To download the most recent data files from Revo:

```bash
./download_revo.sh
praktika_vortaro process_revo
```

## Tests

```bash
pytest
```