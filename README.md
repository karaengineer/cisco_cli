# Show CLI Utility

Python CLI toolset for running Netmiko commands against multiple Cisco devices.  
It reads device lists and command sets from `data/`, executes them concurrently, and stores the results in `outputs/`.

## Features
- Multithreaded execution with per-device logging (`src/show_v2.py`, `src/show_v3.py`).
- Configurable inputs: manual entry, text files, or command lists.
- Structured outputs with automatic error and failed-IP tracking.
- Sample data and raw data separation to help keep the repository light.

## Project Layout
```text
├─ README.md
├─ requirements.txt
├─ src/
│  ├─ __init__.py
│  ├─ show_v2.py
│  └─ show_v3.py
├─ data/
│  ├─ inputs/          # tracked sample inputs for quick tests
│  ├─ raw/             # large or sensitive datasets (ignored)
│  └─ templates/       # helper templates for user-specific data
├─ outputs/            # generated at runtime (ignored)
├─ tests/
│  └─ test_show_cli.py
└─ docs/
   └─ usage.md
```

## Getting Started
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Usage
Examples assume you're at the project root.

```bash
# Run show_v3 with sample data
python src/show_v3.py --user admin ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmd-file data/inputs/show_sample.txt ^
    --output-dir demo_outputs

# Run show_v2 with inline command list
python src/show_v2.py --user admin ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmds "show version,show ip interface brief" ^
    --output-dir demo_outputs --threads 5
```

Provide your own credentials when prompted. Outputs and logs are placed in `outputs/<chosen-dir>`; compilation into a single file is available via `--combine`.

## Data Management
- Put real/sensitive device lists in `data/raw/` (ignored by Git). Use the templates in `data/templates/` to track the required format.
- Place reusable examples in `data/inputs/` so contributors can reproduce behaviour.
- Large command or IP lists should live in `data/raw/` and stay out of version control.

## Testing
```bash
pytest
```
The suite exercises helper functions like file readers and output directory preparation.

## Documentation
More detailed walkthroughs live under `docs/usage.md`. Expand this section with troubleshooting notes or runbooks as the project grows.

## License
Distributed under the MIT License. See `LICENSE` for details.
