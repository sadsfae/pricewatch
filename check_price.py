import shutil
import subprocess
import time
import sys
import os
from collections import deque
import threading
import json
import requests
import datetime
import pytz

CRYPTO = {
    'BTC': 'bitcoin', 'BITCOIN': 'bitcoin',
    'ETH': 'ethereum', 'ETHEREUM': 'ethereum',
    'SOL': 'solana', 'SOLANA': 'solana',
    'DOGE': 'dogecoin', 'DOGECOIN': 'dogecoin',
    'ADA': 'cardano', 'CARDANO': 'cardano',
    'XRP': 'ripple', 'RIPPLE': 'ripple',
    'XMR': 'monero', 'MONERO': 'monero',
    'LTC': 'litecoin', 'LITECOIN': 'litecoin',
    'ZEC': 'zcash', 'ZCASH': 'zcash',
    'ZAN': 'zano', 'ZANO': 'zano',
    'XLM': 'stellar', 'STELLAR': 'stellar',
}
POLL_INTERVAL = 30

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BLINK = '\033[5m'
NO_BLINK = '\033[25m'

BAR_FULL = '█'
BAR_EMPTY = '░'
BAR_WIDTH = 20

current_price = None
price_lock = threading.Lock()
ws_thread = None
api_key = None
finnhub_symbol = None


def get_crypto_price_coingecko(cg_id):
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {'ids': cg_id, 'vs_currencies': 'usd'}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()[cg_id]['usd']
    except Exception:
        return None


def get_fallback_quote():
    try:
        url = "https://finnhub.io/api/v1/quote"
        params = {'symbol': finnhub_symbol, 'token': api_key}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('c') or data.get('pc')
    except Exception:
        return None


def hours_until_market_open():
    eastern = pytz.timezone('US/Eastern')
    now = datetime.datetime.now(eastern)
    weekday = now.weekday()
    if weekday >= 5:
        days_ahead = 7 - weekday
    else:
        days_ahead = 0
    next_open = (now.date() + datetime.timedelta(days=days_ahead))
    if now.time() >= datetime.time(9, 30):
        next_open += datetime.timedelta(days=1)
    open_dt = datetime.datetime.combine(next_open, datetime.time(9, 30))
    open_dt = eastern.localize(open_dt)
    delta = open_dt - now
    hours = delta.total_seconds() / 3600
    return round(hours, 1)


def on_message(ws, message):
    global current_price
    data = json.loads(message)
    if 'data' in data:
        for trade in data['data']:
            with price_lock:
                current_price = trade['p']


def on_error(ws, error):
    print(f"WebSocket error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")


def on_open(ws, symbol):
    ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))


def start_websocket(symbol, key):
    import websocket
    global ws_thread
    ws_url = f"wss://ws.finnhub.io?token={key}"
    ws = websocket.WebSocketApp(ws_url,
                                on_open=lambda ws: on_open(ws, symbol),
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()


def get_price():
    with price_lock:
        if current_price is not None:
            return current_price
    return get_fallback_quote()


def crossed_threshold(price, last_price, target, check_above):
    """Return True if price just crossed the target threshold."""
    if last_price is None:
        return price >= target if check_above else price <= target
    if check_above:
        return price >= target and last_price < target
    return price <= target and last_price > target


def get_audio_player():
    """Return available audio player command, or None if not found."""
    if shutil.which("mpv"):
        return ["mpv", "--loop=inf", "--really-quiet"]
    if shutil.which("mplayer"):
        return ["mplayer", "-loop", "0", "-nolirc", "-quiet"]
    return None


def play_alert(wav, player_cmd):
    subprocess.Popen(player_cmd + [wav],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def send_notification(title, message):
    """Send a desktop notification using notify-send or osascript."""
    if shutil.which('notify-send'):
        subprocess.Popen(['notify-send', title, message],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    elif shutil.which('osascript'):
        safe_msg = message.replace('"', '\\"')
        safe_title = title.replace('"', '\\"')
        script = (f'display notification "{safe_msg}" '
                  f'with title "{safe_title}"')
        subprocess.Popen(['osascript', '-e', script],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)


def update_deques(now, price, price_history, min_prices, max_prices, cutoff):
    """Update price history and min/max deques, prune old entries."""
    price_history.append((now, price))

    while min_prices and min_prices[-1][1] > price:
        min_prices.pop()
    min_prices.append((now, price))

    while max_prices and max_prices[-1][1] < price:
        max_prices.pop()
    max_prices.append((now, price))

    while price_history and price_history[0][0] < cutoff:
        old_time, _ = price_history.popleft()
        if min_prices and min_prices[0][0] == old_time:
            min_prices.popleft()
        if max_prices and max_prices[0][0] == old_time:
            max_prices.popleft()


def check_volatility(price_history, min_prices, max_prices, target_pct):
    """Check if volatility threshold met.

    Returns (triggered, swing_pct) or (False, None).
    """
    if len(price_history) < 2:
        return False, 0.0

    min_price = min_prices[0][1]
    max_price = max_prices[0][1]

    if min_price <= 0:
        return False, 0.0

    swing_pct = (max_price - min_price) / min_price * 100
    return swing_pct >= target_pct, swing_pct


def get_volatility_bar(pct, target_pct):
    ratio = min(pct / target_pct, 1.0)
    filled = int(ratio * BAR_WIDTH)
    bar = BAR_FULL * filled + BAR_EMPTY * (BAR_WIDTH - filled)
    if pct < target_pct * 0.5:
        color = GREEN
    elif pct < target_pct:
        color = YELLOW
    else:
        color = RED
    return f"{color}{bar}{RESET} {pct:.4f}%"


def run_volatility_monitor(symbol, target_pct, time_mins, wav, player_cmd,
                           fetch_price):
    """Run the volatility monitoring loop."""
    price_history, min_prices, max_prices = deque(), deque(), deque()
    triggered = False

    while True:
        price = fetch_price()
        now = time.monotonic()
        time_str = time.strftime('%H:%M:%S')

        if price is not None and price > 0:
            cutoff = now - (time_mins * 60)
            update_deques(now, price, price_history, min_prices,
                          max_prices, cutoff)

            has_enough_data = len(price_history) >= 2

            if triggered:
                print(f"{symbol}: ${price:,.2f} ({time_str})")
            elif not has_enough_data:
                print(f"{symbol}: ${price:,.2f} (warming up...) ({time_str})")
            else:
                alert, swing_pct = check_volatility(
                    price_history, min_prices, max_prices, target_pct)

                if alert:
                    min_p = min_prices[0][1]
                    max_p = max_prices[0][1]
                    span_mins = (now - price_history[0][0]) / 60.0
                    msg = (f"{symbol} VOLATILITY: {swing_pct:.4f}% range "
                           f"in {span_mins:.1f}min (low ${min_p:,.2f}, "
                           f"high ${max_p:,.2f})")
                    print(f"\n{RED}!!! {msg} !!!{RESET}")
                    send_notification("Price Watch Alert", msg)

                    print(f"    Starting endless alert sound... "
                          f"(stop with: killall {player_cmd[0]})\n")
                    play_alert(wav, player_cmd)
                    triggered = True
                else:
                    bar = get_volatility_bar(swing_pct, target_pct)
                    print(f"{symbol}: ${price:,.2f} "
                          f"(vol {bar} / {time_mins}min) ({time_str})")

        else:
            hours = hours_until_market_open()
            print(
                f"{symbol}: Market closed, ~{hours}h until open ({time_str})")

        time.sleep(POLL_INTERVAL)


def run_price_monitor(symbol, mode, target, wav, player_cmd, fetch_price):
    """Run the price threshold monitoring loop."""
    triggered = False
    last_price = None
    blink_state = True

    while True:
        price = fetch_price()
        time_str = time.strftime('%H:%M:%S')
        blink_state = not blink_state

        if price is not None:
            if target > 0:
                pct_diff = abs(price - target) / target * 100
                big_arrow = "▲" if price > target else "▼"
                color = GREEN if price > target else RED
                base_arrow = f"{color}{big_arrow}{RESET}"

                if triggered:
                    blink_code = BLINK if blink_state else NO_BLINK
                    b_arrow = f"{blink_code}{color}{big_arrow}{RESET}"
                    triple_arrow = b_arrow + b_arrow + b_arrow
                else:
                    triple_arrow = base_arrow + base_arrow + base_arrow

                if pct_diff < 0.01:
                    if abs(price - target) < 0.0001:
                        status = "at target"
                    else:
                        direction = "above" if price > target else "below"
                        status = (
                            f"{triple_arrow} <0.01% {direction} target "
                            f"{triple_arrow}"
                        )
                else:
                    direction = "above" if price >= target else "below"
                    status = (
                        f"{triple_arrow} {pct_diff:.2f}% {direction} "
                        f"target {triple_arrow}"
                    )
            else:
                status = ""

            print(f"{symbol}: ${price:,.2f} ({time_str}) {status}")

            crossed = crossed_threshold(price, last_price, target,
                                        mode == 'above')
            if not triggered and crossed:
                if mode == 'above':
                    msg = (f"{symbol} BROKE ABOVE ${target:,}! "
                           f"Price: ${price:,.2f}")
                    print(f"\n!!! {msg} !!!")
                else:
                    msg = (f"{symbol} DROPPED BELOW ${target:,}! "
                           f"Price: ${price:,.2f}")
                    print(f"\n!!! {msg} !!!")

                send_notification("Price Watch Alert", msg)
                print(f"    Starting endless alert sound... "
                      f"(stop with: killall {player_cmd[0]})\n")
                play_alert(wav, player_cmd)
                triggered = True
            last_price = price

        else:
            hours = hours_until_market_open()
            print(
                f"{symbol}: Market closed, ~{hours}h until open ({time_str})")

        time.sleep(POLL_INTERVAL)


def parse_args():
    if len(sys.argv) != 5:
        print("Usage: check_price.py <symbol> <mode> <target> <wav>")
        print("")
        print("Modes:")
        print("  above <price>        Alert when price rises to target")
        print("  below <price>        Alert when price drops to target")
        print("  vol <pct>-<mins>     Alert on volatility")
        print("")
        print("Examples:")
        print("  btc above 100000 alert.wav")
        print("  slv below 61 alert.wav")
        print("  tsla vol 0.5-5 alert.wav")
        sys.exit(1)

    symbol = sys.argv[1]
    mode = sys.argv[2].lower()
    target_str = sys.argv[3]
    wav = sys.argv[4]

    if not os.path.isfile(wav):
        sys.exit(f"WAV not found: {wav}")

    if mode == 'vol':
        if '-' not in target_str:
            sys.exit("Volatility format: <percent>-<minutes> (e.g., 0.001-1)")
        try:
            pct_str, mins_str = target_str.split('-', 1)
            target_pct = float(pct_str)
            time_mins = int(mins_str)
        except ValueError:
            sys.exit("Invalid vol format: must be number-number")
        if target_pct <= 0 or time_mins <= 0:
            sys.exit("Percent and minutes must be > 0")
        return symbol, mode, (target_pct, time_mins), wav

    if mode not in ('above', 'below'):
        sys.exit("Mode must be 'above', 'below', or 'vol'")
    try:
        target = float(target_str)
    except ValueError:
        sys.exit("Target price must be a number.")
    return symbol, mode, target, wav


def main():
    global api_key, finnhub_symbol, current_price
    player_cmd = get_audio_player()
    if not player_cmd:
        sys.exit("Error: mpv or mplayer not found in PATH")

    symbol, mode, target, wav = parse_args()
    symbol_upper = symbol.upper()
    cg_id = CRYPTO.get(symbol_upper)

    if cg_id:
        def fetch_price():
            return get_crypto_price_coingecko(cg_id)
    else:
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            sys.exit("Error: FINNHUB_API_KEY environment variable not set")

        finnhub_symbol = symbol_upper

        current_price = None

        start_websocket(finnhub_symbol, api_key)

        time.sleep(2)

        current_price = get_price()

        def fetch_price():
            return get_price()

    print(f"Monitoring {symbol_upper}...")
    if mode == 'vol':
        target_pct, time_mins = target
        print(f"Alert on ±{target_pct:.4f}% change "
              f"within {time_mins} minute{'s' if time_mins != 1 else ''}")
    else:
        direction = "above or at" if mode == 'above' else "below or at"
        print(f"Alert when price goes {direction} ${target:,}")
    print("Press Ctrl+C to stop monitoring.\n")

    try:
        if mode == 'vol':
            target_pct, time_mins = target
            run_volatility_monitor(symbol_upper, target_pct, time_mins,
                                   wav, player_cmd, fetch_price)
        else:
            run_price_monitor(symbol_upper, mode, target, wav,
                              player_cmd, fetch_price)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
