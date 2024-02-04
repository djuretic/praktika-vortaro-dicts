# Dictionary files for Praktika Vortaro

## Generating the database

Install Python environment:

```bash
pyenv update
pyenv install 3.11.0
pyenv virtualenv 3.11.0 pv-dicts311
pyenv activate
```

Install the dependencies, download the dictionary files and process them:

```bash
git submodule init && git submodule update
pip install pipenv
pipenv install -d
# if using pyenv
pyenv rehash
praktika_vortaro process_revo
```

This will generate the sqlite database `output/vortaro.db`.

To download the most recent data files from Revo:

```bash
# you may need 'sudo apt install lynx'
./download_revo.sh
praktika_vortaro process_revo
```

## Tests

```bash
pytest
```