# Dictionary files for Praktika Vortaro

## Generating the database

Install the dependencies, download the dictionary files and process them:

```bash
git submodule init && git submodule update
pip install -r requirements.txt
process_revo
```

This will generate the sqlite database `eo_dicts/vortaro.db`.

To download the most recent data files from Revo:

```bash
./download_revo.sh
process_revo
```
