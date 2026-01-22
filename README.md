# Price Watcher

[![Flake8 Lint](https://github.com/sadsfae/pricewatcher/actions/workflows/flake8.yml/badge.svg)](https://github.com/sadsfae/pricewatcher/actions/workflows/flake8.yml)

Monitors crypto/stock prices & volatility and plays an alert sound when target is reached.
* It will also send a desktop notification on Linux or MAC OSX.
* Run via `python` in a terminal or use the optional GUI

> [!NOTE]
> Stock prices utilize [Finnhub](https://finnhub.io/register) free API (email sign-up required)
>
> Crypto prices utilize CoinGecko open API but may be rate limited occasionally.
>
> (optional) If you want to use a CoinGecko API key use `export COINGECKO_API_KEY="your_API_key"`

## Usage

```
python pricewatcher.py <symbol> <mode> <target> <wav>
```

### Price targets
```
python pricewatcher.py btc above 100000 alert.wav
python pricewatcher.py eth below 3000 alert.wav
```

### Volatility
```
python pricewatcher.py sol vol 10-5 alert.wav    # 10% move in 5 mins
python pricewatcher.py doge vol 5-15 alert.wav   # 5% move in 15 mins
python pricewatcher.py tsla vol 5-10 alert.wav   # 5% move in 10 mins (needs FINNHUB_API_KEY)
```

### Stocks
* Requires a [Finnhub](https://finnhub.io/register) API key (Free, email signup only)
```bash
export FINNHUB_API_KEY="your_key_here"
python pricewatcher.py tsla above 400 alert.wav
```

## Requirements
- Python 3 with these libraries:
   * `requests` or `python3-requests`
   * `pytz` or `python3-pytz` (Stocks only)
   * `websockets` or `python3-websockets` (Stocks only)
- mpv or mplayer (playing alerts)

### GUI
To run the GUI:
```
python pricewatcher_gui.py
```

## Installation
### Clone Repository
```bash
git clone https://github.com/sadsfae/pricewatcher.git
cd pricewatcher/src
```

### Copy .desktop file (optional GUI)
```bash
cat > pricewatcher.desktop <<EOF
[Desktop Entry]
Version=1.0
Name=Price Watch
Comment=Monitor crypto and stock prices
Exec=$(which python3) $(pwd)/pricewatcher_gui.py
Path=$(pwd)/
Icon=utilities-system-monitor
Terminal=false
Type=Application
Categories=Utility;Finance;
EOF
```

### Install it to your local applications folder (optional GUI)
```bash
mkdir -p ~/.local/share/applications/
mv pricewatcher.desktop ~/.local/share/applications/
chmod +x ~/.local/share/applications/pricewatcher.desktop
update-desktop-database ~/.local/share/applications/
```

## Screenshots
### CLI
![pricewatcher Mon](image/monitor_price.png)

![pricewatcher Vol](image/monitor_vol.png)

### GUI
![pricewatcher GUI](image/monitor_gui.png)
