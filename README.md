# Goldteeth

[![Flake8 Lint](https://github.com/sadsfae/goldteeth/actions/workflows/flake8.yml/badge.svg)](https://github.com/sadsfae/goldteeth/actions/workflows/flake8.yml)
[![PyPI version](https://img.shields.io/pypi/v/goldteeth.svg)](https://pypi.org/project/goldteeth/)

Monitors crypto/stock prices & volatility and plays an alert sound when a
target is reached.

* It will also send a desktop notification on Linux or MAC OSX.
* Run via `python` in a terminal or use the optional GUI.

> [!NOTE]
> Stock prices utilize [Finnhub](https://finnhub.io/register) free API
> (email sign-up required)
>
> Crypto prices utilize the CoinGecko open API but may be rate limited
> occasionally.
>
> (optional) If you want to use a CoinGecko API key use
> `export COINGECKO_API_KEY="your_API_key"`

## Usage

```bash
python src/goldteeth_cli.py <symbol> <mode> <target> <wav>
```

### Price Targets
```bash
python src/goldteeth_cli.py btc above 100000 alert.wav
python src/goldteeth_cli.py eth below 3000 alert.wav
```

### Volatility
```bash
python src/goldteeth_cli.py sol vol 10-5 src/goldteeth/alert.wav  # 10% move in 5 mins
python src/goldteeth_cli.py doge vol 5-15 src/goldteeth/alert.wav  # 5% move in 15 mins
python src/goldteeth_cli.py tsla vol 5-10 src/goldteeth/alert.wav  # 5% move in 10 mins
```

### Stocks
* Requires a [Finnhub](https://finnhub.io/register) API key (free, email sign-up)
```bash
export FINNHUB_API_KEY="your_key_here"
python src/goldteeth_cli.py tsla above 400 src/goldteeth/alert.wav
```

## Requirements
- Python 3 with these libraries:
   * `requests` or `python3-requests`
   * `pytz` or `python3-pytz` (stocks only)
   * `websockets` or `python3-websockets` (stocks only)
- mpv or mplayer (audio alerts)

### GUI
```bash
python src/goldteeth_gui.py
```

## Installation via Pip
```bash
python -m venv goldteeth
. !$/bin/activate
pip install goldteeth
```

### Usage with Pip
```bash
goldteeth
```

## Installation via Repository
```bash
git clone [https://github.com/sadsfae/goldteeth.git](https://github.com/sadsfae/goldteeth.git)
cd goldteeth/src
```
### Copy .desktop file (optional GUI)
```bash
cat > goldteeth.desktop <<EOF
[Desktop Entry]
Version=1.0
Name=Goldteeth
Comment=Monitor crypto and stock prices
Exec=$(which python3) $(pwd)/src/goldteeth_gui.py
Path=$(pwd)/
Icon=utilities-system-monitor
Terminal=false
Type=Application
Categories=Utility;Finance;
EOF
```

### Install it to local apps folder (optional GUI)
```bash
mkdir -p ~/.local/share/applications/
mv goldteeth.desktop ~/.local/share/applications/
chmod +x ~/.local/share/applications/goldteeth.desktop
update-desktop-database ~/.local/share/applications/
```

## Screenshots

### CLI
![goldteeth Mon](image/monitor_price.png)

![goldteeth Vol](image/monitor_vol.png)

### GUI
![goldteeth GUI](image/monitor_gui.png)
