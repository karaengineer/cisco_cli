# Show CLI Utility

Python CLI toolset for running Netmiko commands against multiple Cisco devices. It reads device lists and command sets from `data/`, executes them concurrently, and stores the results in `outputs/`.

## Features
- Multithreaded execution with per-device logging (`show_cli/main.py`).
- Configurable inputs: manual entry, text files, or command lists.
- Structured outputs with automatic error and failed-IP tracking.
- Sample data and raw data separation to help keep the repository light.
- Structured logging with adjustable verbosity (`--log-level`).
- Optional INI configuration file so you can store defaults once.

## Project Layout
```
./README.md
./CHANGELOG.md
./requirements.txt
./.github/workflows/
    ci.yml
./show_cli/
    __init__.py
    main.py
./data/
    inputs/          # tracked sample inputs for quick tests
    raw/             # large or sensitive datasets (ignored)
    templates/       # helper templates for user-specific data
./outputs/          # generated at runtime (ignored)
./tests/
    test_show_cli.py
./docs/
    usage.md
./LICENSE
```

## Getting Started
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt          # cepat untuk percobaan lokal
# atau instal sebagai paket editabel (termasuk dependency dev)
pip install -e .[dev]
```

## Usage
Examples assume you're at the project root.

```bash
# Jalankan via console script (setelah pip install -e .)
show-cli --user admin ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmd-file data/inputs/show_sample.txt ^
    --output-dir demo_outputs

# Jalankan langsung dari sumber
python -m show_cli.main --user admin ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmd-file data/inputs/show_sample.txt ^
    --output-dir demo_outputs

# Run with inline command list
python -m show_cli.main --user admin ^
    --ip-file data/inputs/ip_sample.txt ^
    --cmds "show version,show ip interface brief" ^
    --output-dir demo_outputs --threads 5
```

Provide your own credentials when prompted. Outputs and logs are placed in `outputs/<chosen-dir>`; compilation into a single file is available via `--combine`. Atur detail logging via `--log-level` (`DEBUG`, `INFO`, dsb).
Gunakan flag tambahan seperti `--command-timeout`, `--delay-factor`, atau `--session-timeout` ketika perlu mengatur perilaku Netmiko langsung dari CLI.

### Using a Config File

```ini
[cli]
user = admin
ip_file = inputs/ip_sample.txt
cmd_file = inputs/show_sample.txt
threads = 8
combine = true
log_level = INFO
command_timeout = 300
delay_factor = 2.0
session_timeout = 30
```

Simpan ke `data/templates/config_template.ini`, lalu panggil:

```bash
show-cli --config data/templates/config_template.ini
```

Argumen CLI yang diberikan secara eksplisit akan menimpa nilai dari file konfigurasi. Anda juga dapat menambah parameter seperti `command_timeout`, `delay_factor`, atau `session_timeout` untuk menyesuaikan perilaku Netmiko tanpa mengubah kode.
Jika file konfigurasi Anda berada di dalam `data/`, Anda juga bisa menuliskan hanya nama file-nya saja:

```bash
show-cli --config config.ini   # akan mencari di root proyek dan data/
```

## Data Management
- Put real/sensitive device lists in `data/raw/` (ignored by Git). Use the templates in `data/templates/` to track the required format.
- Place reusable examples in `data/inputs/` so contributors can reproduce behaviour.
- Large command or IP lists should live in `data/raw/` and stay out of version control.
- Gunakan `data/templates/config_template.ini` sebagai contoh konfigurasi bawaan.

## Testing
```bash
pytest
```
The suite exercises helper functions like file readers and output directory preparation.

## Documentation
More detailed walkthroughs live under `docs/usage.md`. Expand this section with troubleshooting notes or runbooks as the project grows.

## Future Work
- Bungkus koneksi Netmiko dalam lapisan abstraksi agar mudah menambahkan vendor lain atau melakukan mocking saat pengujian integrasi.
- Tambahkan tes integrasi yang memanfaatkan monkeypatch Netmiko untuk memastikan alur `connect_and_run` berfungsi tanpa perangkat fisik.

## License
Distributed under a custom non-commercial license. You may use, modify, and share the code for non-commercial purposes, but only MIFTA may grant commercial rights. See `LICENSE` for full terms.
