# Price Watch

[![Flake8 Lint](https://github.com/sadsfae/pricewatch/actions/workflows/flake8.yml/badge.svg)](https://github.com/sadsfae/pricewatch/actions/workflows/flake8.yml)

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
python pricewatch.py <symbol> <mode> <target> <wav>
```

### Price targets
```
python pricewatch.py btc above 100000 alert.wav
python pricewatch.py eth below 3000 alert.wav
```

### Volatility
```
python pricewatch.py sol vol 10-5 alert.wav    # 10% move in 5 mins
python pricewatch.py doge vol 5-15 alert.wav   # 5% move in 15 mins
python pricewatch.py tsla vol 5-10 alert.wav   # 5% move in 10 mins (needs FINNHUB_API_KEY)
```

### Stocks
* Requires a [Finnhub](https://finnhub.io/register) API key (Free, email signup only)
```bash
export FINNHUB_API_KEY="your_key_here"
python pricewatch.py tsla above 400 alert.wav
```

## Requirements
- Python 3 with these libraries:
   * `requests` or `python3-requests`
   * `pytz` or `python3-pytz`
   * `websockets` or `python3-websockets` (Stocks only)
- mpv or mplayer

### GUI
To run the GUI:
```
python pricewatch_gui.py
```

## Installation
### Clone Repository
```bash
git clone https://github.com/sadsfae/pricewatch.git
cd pricewatch/src
```

### Copy .desktop file (optional GUI)
```bash
cat > pricewatch.desktop <<EOF
[Desktop Entry]
Version=1.0
Name=Price Watch
Comment=Monitor crypto and stock prices
Exec=$(which python3) $(pwd)/pricewatch_gui.py
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
mv pricewatch.desktop ~/.local/share/applications/
chmod +x ~/.local/share/applications/pricewatch.desktop
update-desktop-database ~/.local/share/applications/
```

## Screenshots
### CLI
![Pricewatch Mon](image/monitor_price.png)

![Pricewatch Vol](image/monitor_vol.png)

### GUI
![Pricewatch GUI](image/monitor_gui.png)
