from telethon.sync import TelegramClient, events
from telethon import connection
from datetime import datetime
from typing import List
from colorama import Fore, Style, init
import asyncio
import random
import sys
from python_socks import ProxyType
from argparse import ArgumentParser
import json
import signal

# Initialize colorama for cross-platform color support
init(autoreset=True)

###################
# CLI SETUP      #
###################

def parse_args():
    parser = ArgumentParser(description='Cute little delta-neutral trading bot')
    
    # Required config file
    parser.add_argument('--config', type=str, required=True,
                      help='Path to JSON config file')
    
    # Optional trading parameters
    parser.add_argument('--margin', type=int, default=50,
                      help='Margin in USDC (default: 50)')
    parser.add_argument('--leverage', type=int, default=10,
                      help='Leverage multiplier (default: 10)')
    parser.add_argument('--duration-min', type=int, default=10,
                      help='Minimum trade duration in minutes (default: 10)')
    parser.add_argument('--duration-max', type=int, default=90,
                      help='Maximum trade duration in minutes (default: 90)')
    
    # Optional timing parameters
    parser.add_argument('--sleep-orders', type=int, nargs=2, default=[3, 6],
                      help='Sleep between orders range in seconds (default: 3 6)')
    parser.add_argument('--sleep-iteration', type=int, default=60,
                      help='Sleep after iteration in seconds (default: 60)')
    parser.add_argument('--random-sleep', type=int, nargs=2, default=[3, 6],
                      help='Random sleep range in seconds (default: 3 6)')
    
    # Optional bot parameters
    parser.add_argument('--trade-bot-id', type=int, default=6753205995,
                      help='Trade bot user ID (default: 6753205995)')
    
    return parser.parse_args()

def load_config():
    args = parse_args()
    
    try:
        with open(args.config) as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ['api', 'pairs', 'proxies']
        for field in required_fields:
            if field not in config:
                raise KeyError(f"Missing required field: {field}")
            
        return {
            'API_ID': config['api'].get('id'),
            'API_HASH': config['api'].get('hash'),
            'TRADE_BOT_USER_ID': args.trade_bot_id,
            'MARGIN': args.margin,
            'LEVERAGE': args.leverage,
            'DURATION_RANGE': (args.duration_min, args.duration_max),
            'SLEEP_BETWEEN_ORDERS_RANGE': tuple(args.sleep_orders),
            'SLEEP_AFTER_ITERATION': args.sleep_iteration,
            'RANDOM_SLEEP_RANGE': tuple(args.random_sleep),
            'CLIENT_CONFIG': config['proxies'],
            'TRADING_PAIRS_CONFIG': config['pairs'],
        }
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

###################
# CONFIGURATIONS  #
###################

# These will be populated from CLI arguments
API_ID = None
API_HASH = None
MARGIN = None
LEVERAGE = None
DURATION_RANGE = None
SLEEP_BETWEEN_ORDERS_RANGE = None
SLEEP_AFTER_ITERATION = None
RANDOM_SLEEP_RANGE = None
TRADE_BOT_USER_ID = None
CLIENT_CONFIG = None
TRADING_PAIRS_CONFIG = None

###################
#     LOGGING    #
###################

def logger(nickname: str, message: str):
    """Log messages with color coding based on message type and nickname."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    COLORS = [
        Fore.GREEN, Fore.MAGENTA, Fore.CYAN, 
        Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTBLUE_EX, 
        Fore.LIGHTMAGENTA_EX
    ]
    
    try:
        nickname_colors = {
            'main': Fore.BLUE,
            **{user.username: COLORS[i % len(COLORS)] 
               for i, user in enumerate(trade_machine.clients)}
        }
    except (NameError, AttributeError):
        # Fallback if trade_machine not initialized
        nickname_colors = {'main': Fore.BLUE}
    
    # Message color selection
    message_color = Fore.WHITE
    if '⚠️' in message:
        message_color = Fore.RED
    elif 'balance' in message.lower():
        message_color = Fore.CYAN
    elif 'trying to' in message.lower():
        message_color = Fore.YELLOW
    elif any(symbol in message for symbol in ['✅', '🥳', '🟢']):
        message_color = Fore.GREEN

    # Format and output
    nick_color = nickname_colors.get(nickname, Fore.WHITE)
    log_message = (
        f"{Fore.WHITE}[{current_time}] "
        f"{nick_color}[{nickname}] "
        f"{message_color}{message}"
        f"{Style.RESET_ALL}"
    )
    
    print(log_message)
    with open('trading.log', 'a', encoding='utf-8') as f:
        f.write(f"[{current_time}] [{nickname}] {message}\n")

###################
# TRADING LOGIC  #
###################

def generate_delta_neutral_orders():
    """Generate balanced long/short orders across clients."""
    random_coin = random.choices(
        list(TRADING_PAIRS_CONFIG.keys()), 
        list(TRADING_PAIRS_CONFIG.values())
    )[0]
    random_duration = random.randint(*DURATION_RANGE)
    
    total_clients = len(CLIENT_CONFIG)
    long_clients = total_clients // 2
    margin_per_side = MARGIN
    
    # Generate and normalize weights
    long_weights = [random.uniform(0.8, 1.2) for _ in range(long_clients)]
    short_weights = [random.uniform(0.8, 1.2) for _ in range(total_clients - long_clients)]
    
    # Normalize weights to sum to 1.0
    long_weights = [w/sum(long_weights) for w in long_weights]
    short_weights = [w/sum(short_weights) for w in short_weights]
    
    # Generate orders
    iterations = []
    long_total = 0
    short_total = 0
    
    # Generate initial orders
    for i, config in enumerate(CLIENT_CONFIG):
        direction = 'long' if i < long_clients else 'short'
        weight = long_weights[i] if direction == 'long' else short_weights[i - long_clients]
        amount = round(margin_per_side * weight)
        
        if direction == 'long':
            long_total += amount
        else:
            short_total += amount
            
        iterations.append({
            'coin': random_coin,
            'duration': random_duration,
            'direction': direction,
            'amount': amount
        })

    # Adjust last orders of each side to ensure totals match margin_per_side
    last_long_idx = long_clients - 1
    last_short_idx = total_clients - 1
    
    iterations[last_long_idx]['amount'] += (margin_per_side - long_total)
    iterations[last_short_idx]['amount'] += (margin_per_side - short_total)

    return iterations

###################
#  BOT HANDLERS  #
###################

async def bot_main_handler(event: events.NewMessage.Event | events.MessageEdited.Event, nickname: str):
    """Handle incoming bot messages and trading operations."""
    if getattr(event.message.peer_id, 'user_id', None) != TRADE_BOT_USER_ID:
        return
    
    message_text = event.message.message
    message_lines = message_text.split('\n')

    # Handle different message types
    if '🏦 Balances Overview' in message_text:
        logger(nickname, f'balance is {message_lines[3]}')
        return

    # Handle error conditions
    for error_text, error_message in [
        ('Failed to open position', 'Failed to open position'),
        ('💀 Insufficient Margin', 'Insufficient margin'),
        ('Leverage exceeds max leverage', 'Leverage exceeds max leverage')
    ]:
        if error_text in message_text:
            logger(nickname, f'⚠️⚠️⚠️ {error_message}, stopping the bot')
            trade_machine.stop()
            return

    # Handle order status messages
    if any(text in message_text for text in ['order placed', '✅ Closed']):
        logger(nickname, message_text)
        return

    # Handle order creation and closing
    if '👀 Order Preview' in message_text:
        is_closing = 'Closing' in message_text
        action_type = 'close' if is_closing else 'confirm'
        
        if ('Order Size:' in message_text or is_closing) and 'Confirm your trade' in message_text:
            logger(nickname, f'Trying to {action_type} order')
            
            cancel_cb = event.reply_markup.rows[0].buttons[0].text
            confirm_cb = event.reply_markup.rows[0].buttons[1].text

            if '❌ Cancel' in cancel_cb and '✅ Confirm' in confirm_cb:
                await asyncio.sleep(random.randint(*RANDOM_SLEEP_RANGE))
                await event.message.click(1)  # Confirm action
            return

###################
# CLIENT SETUP   #
###################

class TelegramUser:
    def __init__(self, client: TelegramClient, config: dict, username: str):
        self.client = client
        self.config = config
        self.username = username

async def initialize_clients() -> List[TelegramUser]:
    clients = []
    for i, proxy_config in enumerate(CLIENT_CONFIG):
        try:
            session_name = f"sessions_client_{i}"
            client = TelegramClient(
                session=session_name,
                api_id=API_ID,
                api_hash=API_HASH,
                proxy=proxy_config
            )
            await client.start()
            
            me = await client.get_me()
            if not me:
                raise Exception(f"Failed to get user info for client {i}")
                
            username = me.first_name or me.username
            user = TelegramUser(client, proxy_config, username)
            clients.append(user)

            # Create unique handlers for each client
            def create_handler(user_name):
                async def handler(event):
                    await bot_main_handler(event, user_name)
                return handler

            # Add handlers with unique closures
            client.add_event_handler(
                create_handler(username),
                events.NewMessage(from_users='pvptrade_bot')
            )
            client.add_event_handler(
                create_handler(username),
                events.MessageEdited(from_users='pvptrade_bot')
            )
            
        except Exception as e:
            print(f"Error initializing client {i}: {e}")
            for user in clients:
                await user.client.disconnect()
            sys.exit(1)
            
    return clients

###################
# TRADE MACHINE  #
###################

def format_order(order: dict) -> str:
    """Format a single order for logging."""
    direction_emoji = '📈' if order['direction'] == 'long' else '📉'
    return (
        f"{direction_emoji} {order['direction'].upper()} {order['coin'].upper()} "
        f"${order['amount']} ({order['duration']}min)"
    )

class TradeMachine:
    def __init__(self, clients: List[TelegramUser]):
        self.clients = clients
        self.is_stopped = False

    async def run_iteration(self):
        orders = generate_delta_neutral_orders()
        
        formatted_orders = '\n'.join([
            f"  {user.username}: {format_order(order)}"
            for user, order in zip(self.clients, orders)
        ])
        
        logger('main', f'🐇🟢 Starting new iteration:\n{formatted_orders}')

        # Create orders
        for user, order in zip(self.clients, orders):
            method = self.open_long if order['direction'] == 'long' else self.open_short
            await method(
                user, 
                order['coin'], 
                order['amount'], 
                order['duration']
            )
            await asyncio.sleep(random.randint(*SLEEP_BETWEEN_ORDERS_RANGE))

        # Wait for duration then close positions
        await asyncio.sleep(orders[0]['duration'] * 60)

        for user in self.clients:
            await self.close_position(user, orders[0]['coin'])
            await asyncio.sleep(random.randint(*SLEEP_BETWEEN_ORDERS_RANGE))

        await asyncio.sleep(SLEEP_AFTER_ITERATION)
        logger('main', '🥳🎉 Iteration is done, got you some points!')

    async def open_long(self, user: TelegramUser, coin: str, amount: int, duration: int):
        logger(user.username, f'Trying to open long position on {coin} with amount {amount} for {duration} minutes')
        await user.client.send_message('pvptrade_bot', f'/long {coin} x{LEVERAGE} {amount}')

    async def open_short(self, user: TelegramUser, coin: str, amount: int, duration: int):
        logger(user.username, f'Trying to open short position on {coin} with amount {amount} for {duration} minutes')
        await user.client.send_message('pvptrade_bot', f'/short {coin} x{LEVERAGE} {amount}')

    async def close_position(self, user: TelegramUser, coin: str):
        logger(user.username, f'Trying to close position on {coin}')
        await user.client.send_message('pvptrade_bot', f'/close {coin} 100%')

    async def get_balance(self, user: TelegramUser):
        logger(user.username, 'Trying to get balance')
        await user.client.send_message('pvptrade_bot', '/balances')

    async def stop(self):
        self.is_stopped = True
        # Close all client connections
        for user in self.clients:
            await user.client.disconnect()
        sys.exit(0)  # Consider more graceful exit

###################
#     MAIN       #
###################

async def main():
    # Load configuration
    config = load_config()
    
    # Update global variables
    globals().update(config)
    
    # Initialize and run
    global trade_machine
    clients = await initialize_clients()
    trade_machine = TradeMachine(clients)
    
    while not trade_machine.is_stopped:
        await trade_machine.run_iteration()

def signal_handler(signum, frame):
    print("\nReceived shutdown signal")
    if 'trade_machine' in globals():
        asyncio.create_task(trade_machine.stop())

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    asyncio.run(main())