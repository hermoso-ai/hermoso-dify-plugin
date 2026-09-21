# Contributing

```bash
pip install -r requirements.txt pytest
python scripts/build_tool_yaml.py        # regenerate tools/*.yaml from one table
pytest -m "not live"                     # offline tests, HTTP is mocked
export HERMOSO_API_KEY                   # set it to a key of your own first
pytest -m live                           # free, read-only calls against the live API
```

The live tests only call endpoints that read data and spend nothing, and they assert that the credit
balance is unchanged at the end. Generation, ad research, competitor discovery and scheduling are
covered by mocked tests only, because they spend credits or write to real social accounts.

`tools/*.yaml` is generated. Edit `scripts/build_tool_yaml.py`, not the YAML.

Package and validate:

```bash
dify plugin package . -o hermoso-0.0.1.difypkg
python3 validator/validate-difypkg.py hermoso-0.0.1.difypkg --output-dir ./validation-report
```
