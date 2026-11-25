# -*- coding: utf-8 -*-
import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
import html
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests

# --- Flask Keep Alive ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "i am private xyz"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("Flask Keep-Alive server started.")
# --- End Flask Keep Alive ---

# --- Configuration ---
TOKEN = '9103389155:AAEE6q_QWmrPDACDNL41ADg4oDaraoQoDsg' # Replace with your actual token
OWNER_ID = 7536482921 # Replace with your Owner ID
ADMIN_ID = 7536482921 # Replace with your Admin ID (can be same as Owner)
YOUR_USERNAME = '@Notyournotmine' # Replace with your Telegram username
UPDATE_CHANNEL = 'https://t.me/+_i5znUzlynw1ZjY1' # Replace with your update channel link

# --- Premium Typography, Glowing Emoji & Animation Configuration ---
BRAND_TITLE = "𝟮𝟰/𝟳 𝗛𝗔𝗖𝗞𝗘𝗥𝗥 𝗛𝗢𝗦𝗧𝗜𝗡𝗚"
FONT_PRESET = "small_caps" # Options: 'small_caps', 'bold_sans', 'serif_italic', 'monospace'
USE_PREMIUM_EMOJIS = True # Renders glowing <tg-emoji> tags with automatic safe fallback
USE_MESSAGE_EFFECTS = True # Triggers Telegram native full-screen glowing animations
ENABLE_ANIMATIONS = True
ANIMATION_DELAY = 0.38 # Seconds between animation frames

# Verified Telegram Custom Emoji IDs (glowing/animated for Premium & Fragment-linked bots, clean fallback otherwise)
PREMIUM_EMOJIS = {
    'crown':     ('5443038326535759644', '👑'),
    'sparkles':  ('5467583879948803288', '✨'),
    'bolt':      ('5373098009640836781', '⚡'),
    'rocket':    ('5445284980978621387', '🚀'),
    'gem':       ('5427181942934088912', '💎'),
    'fire':      ('5431449001532594346', '🔥'),
    'check':     ('5427009714745517609', '✅'),
    'cross':     ('5465665476971471368', '❌'),
    'lock':      ('5469741319330996757', '🔒'),
    'unlock':    ('5469908370521268914', '🔓'),
    'folder':    ('5433653135799228968', '📁'),
    'stats':     ('5424972470023104089', '📊'),
    'shield':    ('5472164874886846699', '🛡️'),
    'hourglass': ('5467928559664242360', '⏳'),
    'megaphone': ('5424818078833715060', '📢'),
    'gear':      ('5372981976804366741', '⚙️'),
    'card':      ('5447410659077661506', '💳'),
    'party':     ('5461151367559141950', '🎉'),
    'warning':   ('5447644880824181033', '⚠️'),
    'dot_green': ('5427009714745517609', '🟢'),
    'dot_red':   ('5465665476971471368', '🔴'),
}

# Native Telegram Bot API Message Effect IDs (works natively on all Telegram clients)
MESSAGE_EFFECTS = {
    'fire':      '5104841245755180586',
    'confetti':  '5046509860389126442',
    'thumbs_up': '5107584321108051014',
    'heart':     '5159385139981059251',
}

SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ',
    'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
    'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
    'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
}

def _map_alphabet(text, upper_start, lower_start, digit_start=None, exceptions=None):
    exceptions = exceptions or {}
    out = []
    for ch in text:
        if ch in exceptions:
            out.append(exceptions[ch])
        elif 'A' <= ch <= 'Z':
            out.append(chr(upper_start + (ord(ch) - 65)))
        elif 'a' <= ch <= 'z':
            out.append(chr(lower_start + (ord(ch) - 97)))
        elif digit_start is not None and '0' <= ch <= '9':
            out.append(chr(digit_start + (ord(ch) - 48)))
        else:
            out.append(ch)
    return ''.join(out)

def stylize(text, preset=None):
    """Apply premium Unicode typography cleanly without breaking symbols."""
    mode = preset or FONT_PRESET
    if mode == 'small_caps':
        return ''.join(SMALL_CAPS_MAP.get(ch.lower(), ch) for ch in text)
    if mode == 'bold_sans':
        return _map_alphabet(text, 0x1D5D4, 0x1D5EE, 0x1D7EC)
    if mode == 'serif_italic':
        return _map_alphabet(text, 0x1D434, 0x1D44E, exceptions={'h': 'ℎ'})
    if mode == 'monospace':
        return _map_alphabet(text, 0x1D670, 0x1D68A, 0x1D7F6)
    return text

def h(value):
    """HTML-escape untrusted dynamic values (usernames, filenames, logs)."""
    return html.escape(str(value), quote=False)

def pe(key):
    """Render a glowing Telegram Premium custom emoji with graceful HTML fallback."""
    emoji_id, fallback = PREMIUM_EMOJIS.get(key, ('', '✨'))
    if USE_PREMIUM_EMOJIS and emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'
    return fallback

def strip_tg_emoji_tags(text):
    """Fallback sanitizer if bot token lacks Fragment custom emoji permissions."""
    return re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', text)

def progress_bar(percent, width=10):
    filled = max(0, min(width, int(round((percent / 100.0) * width))))
    empty = width - filled
    return f"[{'▓' * filled}{'░' * empty}] {percent:>3}%"

def safe_send_message(chat_id, text, reply_markup=None, parse_mode='HTML', effect=None, **kwargs):
    """Send message with automatic fallback if custom emojis or effects are rejected."""
    send_kwargs = dict(kwargs)
    if reply_markup is not None:
        send_kwargs['reply_markup'] = reply_markup
    if parse_mode:
        send_kwargs['parse_mode'] = parse_mode
    if USE_MESSAGE_EFFECTS and effect and effect in MESSAGE_EFFECTS:
        send_kwargs['message_effect_id'] = MESSAGE_EFFECTS[effect]
    try:
        return bot.send_message(chat_id, text, **send_kwargs)
    except (telebot.apihelper.ApiTelegramException, TypeError) as err:
        err_str = str(err).lower()
        clean_text = strip_tg_emoji_tags(text) if ('emoji' in err_str or 'document_invalid' in err_str or 'custom_emoji' in err_str) else text
        send_kwargs.pop('message_effect_id', None)
        try:
            return bot.send_message(chat_id, clean_text, **send_kwargs)
        except Exception:
            send_kwargs.pop('parse_mode', None)
            return bot.send_message(chat_id, re.sub(r'<[^>]+>', '', clean_text), **send_kwargs)

def safe_reply_to(message, text, reply_markup=None, parse_mode='HTML', effect=None, **kwargs):
    """Reply to message with automatic fallback for custom emojis / effects."""
    send_kwargs = dict(kwargs)
    if reply_markup is not None:
        send_kwargs['reply_markup'] = reply_markup
    if parse_mode:
        send_kwargs['parse_mode'] = parse_mode
    if USE_MESSAGE_EFFECTS and effect and effect in MESSAGE_EFFECTS:
        send_kwargs['message_effect_id'] = MESSAGE_EFFECTS[effect]
    try:
        return bot.reply_to(message, text, **send_kwargs)
    except (telebot.apihelper.ApiTelegramException, TypeError) as err:
        err_str = str(err).lower()
        clean_text = strip_tg_emoji_tags(text) if ('emoji' in err_str or 'document_invalid' in err_str or 'custom_emoji' in err_str) else text
        send_kwargs.pop('message_effect_id', None)
        try:
            return bot.reply_to(message, clean_text, **send_kwargs)
        except Exception:
            send_kwargs.pop('parse_mode', None)
            return bot.reply_to(message, re.sub(r'<[^>]+>', '', clean_text), **send_kwargs)

def safe_edit_message_text(text, chat_id, message_id, reply_markup=None, parse_mode='HTML'):
    """Edit message safely with automatic fallback for custom emojis."""
    edit_kwargs = {}
    if reply_markup is not None:
        edit_kwargs['reply_markup'] = reply_markup
    if parse_mode:
        edit_kwargs['parse_mode'] = parse_mode
    try:
        return bot.edit_message_text(text, chat_id, message_id, **edit_kwargs)
    except telebot.apihelper.ApiTelegramException as err:
        err_str = str(err).lower()
        if "message is not modified" in err_str:
            return None
        if 'emoji' in err_str or 'document_invalid' in err_str or 'custom_emoji' in err_str:
            clean_text = strip_tg_emoji_tags(text)
            return bot.edit_message_text(clean_text, chat_id, message_id, **edit_kwargs)
        raise

def animate_frames(chat_id, frames, reply_to_message=None, existing_msg=None, final_markup=None):
    """Play smooth frame-by-frame loading animations before revealing final card."""
    msg = existing_msg
    if not ENABLE_ANIMATIONS or ANIMATION_DELAY <= 0 or len(frames) <= 1:
        final_text = frames[-1]
        if msg:
            safe_edit_message_text(final_text, chat_id, msg.message_id, reply_markup=final_markup)
            return msg
        if reply_to_message:
            return safe_reply_to(reply_to_message, final_text, reply_markup=final_markup)
        return safe_send_message(chat_id, final_text, reply_markup=final_markup)

    for idx, frame in enumerate(frames):
        is_last = (idx == len(frames) - 1)
        markup = final_markup if is_last else None
        if msg is None:
            if reply_to_message is not None:
                msg = safe_reply_to(reply_to_message, frame, reply_markup=markup)
            else:
                msg = safe_send_message(chat_id, frame, reply_markup=markup)
        else:
            try:
                safe_edit_message_text(frame, chat_id, msg.message_id, reply_markup=markup)
            except Exception as e:
                logger.debug(f"Animation frame skipped: {e}")
        if not is_last:
            time.sleep(ANIMATION_DELAY)
    return msg

# Folder setup - using absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
IROTECH_DIR = os.path.join(BASE_DIR, 'inf')
DATABASE_PATH = os.path.join(IROTECH_DIR, 'bot_data.db')

# File upload limits
FREE_USER_LIMIT = 2
SUBSCRIBED_USER_LIMIT = 15
ADMIN_LIMIT = 999
OWNER_LIMIT = float('inf')

# Create necessary directories
os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(IROTECH_DIR, exist_ok=True)

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# --- Data structures ---
bot_scripts = {}
user_subscriptions = {}
user_files = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
bot_locked = False

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Stylized Command Button Labels (Guaranteed Exact Match) ---
BTN_UPDATES      = f"📢 {stylize('Updates Channel')}"
BTN_UPLOAD       = f"📤 {stylize('Upload File')}"
BTN_CHECK_FILES  = f"📂 {stylize('Check Files')}"
BTN_SPEED        = f"⚡ {stylize('Bot Speed')}"
BTN_STATS        = f"📊 {stylize('Statistics')}"
BTN_CONTACT      = f"📞 {stylize('Contact Owner')}"
BTN_SUBS         = f"💳 {stylize('Subscriptions')}"
BTN_BROADCAST    = f"📢 {stylize('Broadcast')}"
BTN_LOCK         = f"🔒 {stylize('Lock Bot')}"
BTN_RUN_ALL      = f"🟢 {stylize('Running All Code')}"
BTN_ADMIN_PANEL  = f"👑 {stylize('Admin Panel')}"

COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    [BTN_UPDATES],
    [BTN_UPLOAD, BTN_CHECK_FILES],
    [BTN_SPEED, BTN_STATS],
    [BTN_CONTACT]
]
ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    [BTN_UPDATES],
    [BTN_UPLOAD, BTN_CHECK_FILES],
    [BTN_SPEED, BTN_STATS],
    [BTN_SUBS, BTN_BROADCAST],
    [BTN_LOCK, BTN_RUN_ALL],
    [BTN_ADMIN_PANEL, BTN_CONTACT]
]

# --- Database Setup ---
def init_db():
    """Initialize the database with required tables"""
    logger.info(f"Initializing database at: {DATABASE_PATH}")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                     (user_id INTEGER PRIMARY KEY, expiry TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_files
                     (user_id INTEGER, file_name TEXT, file_type TEXT,
                      PRIMARY KEY (user_id, file_name))''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_users
                     (user_id INTEGER PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (user_id INTEGER PRIMARY KEY)''')
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
        if ADMIN_ID != OWNER_ID:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}", exc_info=True)

def load_data():
    """Load data from database into memory"""
    logger.info("Loading data from database...")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()

        c.execute('SELECT user_id, expiry FROM subscriptions')
        for user_id, expiry in c.fetchall():
            try:
                user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}
            except ValueError:
                logger.warning(f"⚠️ Invalid expiry date format for user {user_id}: {expiry}. Skipping.")

        c.execute('SELECT user_id, file_name, file_type FROM user_files')
        for user_id, file_name, file_type in c.fetchall():
            if user_id not in user_files:
                user_files[user_id] = []
            user_files[user_id].append((file_name, file_type))

        c.execute('SELECT user_id FROM active_users')
        active_users.update(user_id for (user_id,) in c.fetchall())

        c.execute('SELECT user_id FROM admins')
        admin_ids.update(user_id for (user_id,) in c.fetchall())

        conn.close()
        logger.info(f"Data loaded: {len(active_users)} users, {len(user_subscriptions)} subscriptions, {len(admin_ids)} admins.")
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}", exc_info=True)

init_db()
load_data()
# --- End Database Setup ---

# --- Helper Functions ---
def get_user_folder(user_id):
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def get_user_file_limit(user_id):
    if user_id == OWNER_ID: return OWNER_LIMIT
    if user_id in admin_ids: return ADMIN_LIMIT
    if user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now():
        return SUBSCRIBED_USER_LIMIT
    return FREE_USER_LIMIT

def get_user_file_count(user_id):
    return len(user_files.get(user_id, []))

def is_bot_running(script_owner_id, file_name):
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            proc = psutil.Process(script_info['process'].pid)
            is_running = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            if not is_running:
                if 'log_file' in script_info and hasattr(script_info['log_file'], 'close') and not script_info['log_file'].closed:
                    try:
                        script_info['log_file'].close()
                    except Exception as log_e:
                        logger.error(f"Error closing log file during zombie cleanup {script_key}: {log_e}")
                if script_key in bot_scripts:
                    del bot_scripts[script_key]
            return is_running
        except psutil.NoSuchProcess:
            if 'log_file' in script_info and hasattr(script_info['log_file'], 'close') and not script_info['log_file'].closed:
                try:
                    script_info['log_file'].close()
                except Exception as log_e:
                    logger.error(f"Error closing log file during cleanup {script_key}: {log_e}")
            if script_key in bot_scripts:
                del bot_scripts[script_key]
            return False
        except Exception as e:
            logger.error(f"Error checking process status for {script_key}: {e}", exc_info=True)
            return False
    return False

def kill_process_tree(process_info):
    pid = None
    log_file_closed = False
    script_key = process_info.get('script_key', 'N/A')
    try:
        if 'log_file' in process_info and hasattr(process_info['log_file'], 'close') and not process_info['log_file'].closed:
            try:
                process_info['log_file'].close()
                log_file_closed = True
            except Exception as log_e:
                logger.error(f"Error closing log file during kill for {script_key}: {log_e}")

        process = process_info.get('process')
        if process and hasattr(process, 'pid'):
            pid = process.pid
            if pid:
                try:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.terminate()
                        except psutil.NoSuchProcess:
                            pass
                        except Exception:
                            try: child.kill()
                            except Exception: pass
                    _, alive = psutil.wait_procs(children, timeout=1)
                    for p in alive:
                        try: p.kill()
                        except Exception: pass
                    try:
                        parent.terminate()
                        try: parent.wait(timeout=1)
                        except psutil.TimeoutExpired: parent.kill()
                    except psutil.NoSuchProcess:
                        pass
                    except Exception:
                        try: parent.kill()
                        except Exception: pass
                except psutil.NoSuchProcess:
                    pass
    except Exception as e:
        logger.error(f"❌ Unexpected error killing process tree for PID {pid or 'N/A'} ({script_key}): {e}", exc_info=True)

# --- Automatic Package Installation & Script Running ---
def attempt_install_pip(module_name, message):
    package_name = TELEGRAM_MODULES.get(module_name.lower(), module_name)
    if package_name is None:
        logger.info(f"Module '{module_name}' is core. Skipping pip install.")
        return False
    try:
        status_msg = animate_frames(
            message.chat.id,
            [
                f"{pe('hourglass')} <b>{stylize('Missing Module Detected')}</b>\n<blockquote><code>{h(module_name)}</code> → Preparing <code>pip</code>...\n<code>{progress_bar(20)}</code></blockquote>",
                f"{pe('gear')} <b>{stylize('Installing Package')}</b>\n<blockquote>Installing <code>{h(package_name)}</code>...\n<code>{progress_bar(65)}</code></blockquote>"
            ],
            reply_to_message=message
        )
        command = [sys.executable, '-m', 'pip', 'install', package_name]
        result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            safe_edit_message_text(
                f"{pe('check')} <b>{stylize('Package Installed')}</b>\n<blockquote><code>{h(package_name)}</code> ready for <code>{h(module_name)}</code>.\n<code>{progress_bar(100)}</code></blockquote>",
                message.chat.id, status_msg.message_id
            )
            return True
        else:
            raw_err = (result.stderr or result.stdout or '')[:3200]
            error_msg = f"{pe('cross')} <b>{stylize('Install Failed')}</b> for <code>{h(package_name)}</code>\n<pre>{h(raw_err)}</pre>"
            safe_edit_message_text(error_msg, message.chat.id, status_msg.message_id)
            return False
    except Exception as e:
        safe_reply_to(message, f"{pe('cross')} <b>{stylize('Install Error')}:</b> <code>{h(e)}</code>")
        return False

def attempt_install_npm(module_name, user_folder, message):
    try:
        status_msg = animate_frames(
            message.chat.id,
            [
                f"{pe('hourglass')} <b>{stylize('Node Package Missing')}</b>\n<blockquote><code>{h(module_name)}</code> → Initializing <code>npm</code>...\n<code>{progress_bar(25)}</code></blockquote>",
                f"{pe('gear')} <b>{stylize('Installing Node Module')}</b>\n<blockquote>Installing <code>{h(module_name)}</code> locally...\n<code>{progress_bar(70)}</code></blockquote>"
            ],
            reply_to_message=message
        )
        command = ['npm', 'install', module_name]
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=user_folder, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            safe_edit_message_text(
                f"{pe('check')} <b>{stylize('Node Package Installed')}</b>\n<blockquote><code>{h(module_name)}</code> installed locally.\n<code>{progress_bar(100)}</code></blockquote>",
                message.chat.id, status_msg.message_id
            )
            return True
        else:
            raw_err = (result.stderr or result.stdout or '')[:3200]
            error_msg = f"{pe('cross')} <b>{stylize('NPM Install Failed')}</b> for <code>{h(module_name)}</code>\n<pre>{h(raw_err)}</pre>"
            safe_edit_message_text(error_msg, message.chat.id, status_msg.message_id)
            return False
    except FileNotFoundError:
        safe_reply_to(message, f"{pe('cross')} <b>{stylize('Error')}:</b> <code>npm</code> not found in PATH.")
        return False
    except Exception as e:
        safe_reply_to(message, f"{pe('cross')} <b>{stylize('NPM Error')}:</b> <code>{h(e)}</code>")
        return False

def run_script(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt=1):
    """Run Python script with animated pre-check and clean telemetry feedback."""
    max_attempts = 2
    if attempt > max_attempts:
        safe_reply_to(message_obj_for_reply, f"{pe('cross')} <b>{stylize('Execution Failed')}</b> for <code>{h(file_name)}</code> after {max_attempts} attempts.")
        return

    script_key = f"{script_owner_id}_{file_name}"
    try:
        if not os.path.exists(script_path):
            safe_reply_to(message_obj_for_reply, f"{pe('cross')} <b>{stylize('File Not Found')}:</b> <code>{h(file_name)}</code>")
            if script_owner_id in user_files:
                user_files[script_owner_id] = [f for f in user_files.get(script_owner_id, []) if f[0] != file_name]
            remove_user_file_db(script_owner_id, file_name)
            return

        if attempt == 1:
            check_command = [sys.executable, script_path]
            check_proc = None
            try:
                check_proc = subprocess.Popen(check_command, cwd=user_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                stdout, stderr = check_proc.communicate(timeout=5)
                return_code = check_proc.returncode
                if return_code != 0 and stderr:
                    match_py = re.search(r"ModuleNotFoundError: No module named '(.+?)'", stderr)
                    if match_py:
                        module_name = match_py.group(1).strip().strip("'\"")
                        if attempt_install_pip(module_name, message_obj_for_reply):
                            safe_reply_to(message_obj_for_reply, f"{pe('rocket')} <b>{stylize('Retrying Launch')}</b> for <code>{h(file_name)}</code>...")
                            time.sleep(1.5)
                            threading.Thread(target=run_script, args=(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt + 1)).start()
                            return
                        else:
                            safe_reply_to(message_obj_for_reply, f"{pe('cross')} <b>{stylize('Install Failed')}.</b> Cannot run <code>{h(file_name)}</code>.")
                            return
                    else:
                        error_summary = stderr[:500]
                        safe_reply_to(message_obj_for_reply, f"{pe('cross')} <b>{stylize('Pre-Check Error')}</b> in <code>{h(file_name)}</code>\n<pre>{h(error_summary)}</pre>")
                        return
            except subprocess.TimeoutExpired:
                if check_proc and check_proc.poll() is None:
                    check_proc.kill(); check_proc.communicate()
            except FileNotFoundError:
                safe_reply_to(message_obj_for_reply, f"{pe('cross')} Python interpreter <code>{h(sys.executable)}</code> not found.")
                return
            except Exception as e:
                safe_reply_to(message_obj_for_reply, f"{pe('cross')} Unexpected pre-check error for <code>{h(file_name)}</code>: <code>{h(e)}</code>")
                return
            finally:
                if check_proc and check_proc.poll() is None:
                    check_proc.kill(); check_proc.communicate()

        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        try:
            log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        except Exception as e:
            safe_reply_to(message_obj_for_reply, f"{pe('cross')} Failed to open log file: <code>{h(e)}</code>")
            return

        process = None
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            process = subprocess.Popen(
                [sys.executable, script_path], cwd=user_folder, stdout=log_file, stderr=log_file,
                stdin=subprocess.PIPE, startupinfo=startupinfo, creationflags=0,
                encoding='utf-8', errors='ignore'
            )
            bot_scripts[script_key] = {
                'process': process, 'log_file': log_file, 'file_name': file_name,
                'chat_id': message_obj_for_reply.chat.id,
                'script_owner_id': script_owner_id,
                'start_time': datetime.now(), 'user_folder': user_folder, 'type': 'py', 'script_key': script_key
            }
            safe_reply_to(
                message_obj_for_reply,
                f"{pe('rocket')} <b>{stylize('Python Process Online')}</b>\n"
                f"<blockquote>"
                f"{pe('sparkles')} <b>{stylize('Script')}:</b> <code>{h(file_name)}</code>\n"
                f"{pe('bolt')} <b>{stylize('PID')}:</b> <code>{process.pid}</code>\n"
                f"{pe('shield')} <b>{stylize('Owner')}:</b> <code>{script_owner_id}</code>"
                f"</blockquote>",
                effect='fire'
            )
        except Exception as e:
            if log_file and not log_file.closed: log_file.close()
            safe_reply_to(message_obj_for_reply, f"{pe('cross')} Error starting <code>{h(file_name)}</code>: <code>{h(e)}</code>")
            if process and process.poll() is None:
                kill_process_tree({'process': process, 'log_file': log_file, 'script_key': script_key})
            if script_key in bot_scripts: del bot_scripts[script_key]
    except Exception as e:
        safe_reply_to(message_obj_for_reply, f"{pe('cross')} Unexpected error running <code>{h(file_name)}</code>: <code>{h(e)}</code>")
        if script_key in bot_scripts:
            kill_process_tree(bot_scripts[script_key])
            del bot_scripts[script_key]

def run_js_script(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt=1):
    """Run JS script with animated pre-check and clean telemetry feedback."""
    max_attempts = 2
    if attempt > max_attempts:
        safe_reply_to(message_obj_for_reply, f"{pe('cross')} <b>{stylize('Execution Failed')}</b> for <code>{h(file_name)}</code> after {max_attempts} attempts.")
        return

    script_key = f"{script_owner_id}_{file_name}"
    try:
        if not os.path.exists(script_path):
            safe_reply_to(message_obj_for_reply, f"{pe('cross')} <b>{stylize('File Not Found')}:</b> <code>{h(file_name)}</code>")
            if script_owner_id in user_files:
                user_files[script_owner_id] = [f for f in user_files.get(script_owner_id, []) if f[0] != file_name]
            remove_user_file_db(script_owner_id, file_name)
            return

        if attempt == 1:
            check_command = ['node', script_path]
            check_proc = None
            try:
                check_proc = subprocess.Popen(check_command, cwd=user_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                stdout, stderr = check_proc.communicate(timeout=5)
                return_code = check_proc.returncode
                if return_code != 0 and stderr:
                    match_js = re.search(r"Cannot find module '(.+?)'", stderr)
                    if match_js:
                        module_name = match_js.group(1).strip().strip("'\"")
                        if not module_name.startswith('.') and not module_name.startswith('/'):
                            if attempt_install_npm(module_name, user_folder, message_obj_for_reply):
                                safe_reply_to(message_obj_for_reply, f"{pe('rocket')} <b>{stylize('Retrying Launch')}</b> for <code>{h(file_name)}</code>...")
                                time.sleep(1.5)
                                threading.Thread(target=run_js_script, args=(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt + 1)).start()
                                return
                            else:
                                safe_reply_to(message_obj_for_reply, f"{pe('cross')} NPM install failed for <code>{h(file_name)}</code>.")
                                return
                    error_summary = stderr[:500]
                    safe_reply_to(message_obj_for_reply, f"{pe('cross')} <b>{stylize('JS Pre-Check Error')}</b> in <code>{h(file_name)}</code>\n<pre>{h(error_summary)}</pre>")
                    return
            except subprocess.TimeoutExpired:
                if check_proc and check_proc.poll() is None:
                    check_proc.kill(); check_proc.communicate()
            except FileNotFoundError:
                safe_reply_to(message_obj_for_reply, f"{pe('cross')} <code>node</code> runtime not found on server.")
                return
            except Exception as e:
                safe_reply_to(message_obj_for_reply, f"{pe('cross')} Unexpected JS pre-check error: <code>{h(e)}</code>")
                return
            finally:
                if check_proc and check_proc.poll() is None:
                    check_proc.kill(); check_proc.communicate()

        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        try:
            log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        except Exception as e:
            safe_reply_to(message_obj_for_reply, f"{pe('cross')} Failed to open log file: <code>{h(e)}</code>")
            return

        process = None
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            process = subprocess.Popen(
                ['node', script_path], cwd=user_folder, stdout=log_file, stderr=log_file,
                stdin=subprocess.PIPE, startupinfo=startupinfo, creationflags=0,
                encoding='utf-8', errors='ignore'
            )
            bot_scripts[script_key] = {
                'process': process, 'log_file': log_file, 'file_name': file_name,
                'chat_id': message_obj_for_reply.chat.id,
                'script_owner_id': script_owner_id,
                'start_time': datetime.now(), 'user_folder': user_folder, 'type': 'js', 'script_key': script_key
            }
            safe_reply_to(
                message_obj_for_reply,
                f"{pe('rocket')} <b>{stylize('Node.js Process Online')}</b>\n"
                f"<blockquote>"
                f"{pe('sparkles')} <b>{stylize('Script')}:</b> <code>{h(file_name)}</code>\n"
                f"{pe('bolt')} <b>{stylize('PID')}:</b> <code>{process.pid}</code>\n"
                f"{pe('shield')} <b>{stylize('Owner')}:</b> <code>{script_owner_id}</code>"
                f"</blockquote>",
                effect='fire'
            )
        except Exception as e:
            if log_file and not log_file.closed: log_file.close()
            safe_reply_to(message_obj_for_reply, f"{pe('cross')} Error starting <code>{h(file_name)}</code>: <code>{h(e)}</code>")
            if process and process.poll() is None:
                kill_process_tree({'process': process, 'log_file': log_file, 'script_key': script_key})
            if script_key in bot_scripts: del bot_scripts[script_key]
    except Exception as e:
        safe_reply_to(message_obj_for_reply, f"{pe('cross')} Unexpected error running JS <code>{h(file_name)}</code>: <code>{h(e)}</code>")
        if script_key in bot_scripts:
            kill_process_tree(bot_scripts[script_key])
            del bot_scripts[script_key]

# --- Map Telegram import names to actual PyPI package names ---
TELEGRAM_MODULES = {
    'telebot': 'pyTelegramBotAPI',
    'telegram': 'python-telegram-bot',
    'python_telegram_bot': 'python-telegram-bot',
    'aiogram': 'aiogram',
    'pyrogram': 'pyrogram',
    'telethon': 'telethon',
    'telethon.sync': 'telethon',
    'from telethon.sync import telegramclient': 'telethon',
    'telepot': 'telepot',
    'pytg': 'pytg',
    'tgcrypto': 'tgcrypto',
    'telegram_upload': 'telegram-upload',
    'telegram_send': 'telegram-send',
    'telegram_text': 'telegram-text',
    'mtproto': 'telegram-mtproto',
    'tl': 'telethon',
    'telegram_utils': 'telegram-utils',
    'telegram_logger': 'telegram-logger',
    'telegram_handlers': 'python-telegram-handlers',
    'telegram_redis': 'telegram-redis',
    'telegram_sqlalchemy': 'telegram-sqlalchemy',
    'telegram_payment': 'telegram-payment',
    'telegram_shop': 'telegram-shop-sdk',
    'pytest_telegram': 'pytest-telegram',
    'telegram_debug': 'telegram-debug',
    'telegram_scraper': 'telegram-scraper',
    'telegram_analytics': 'telegram-analytics',
    'telegram_nlp': 'telegram-nlp-toolkit',
    'telegram_ai': 'telegram-ai',
    'telegram_api': 'telegram-api-client',
    'telegram_web': 'telegram-web-integration',
    'telegram_games': 'telegram-games',
    'telegram_quiz': 'telegram-quiz-bot',
    'telegram_ffmpeg': 'telegram-ffmpeg',
    'telegram_media': 'telegram-media-utils',
    'telegram_2fa': 'telegram-twofa',
    'telegram_crypto': 'telegram-crypto-bot',
    'telegram_i18n': 'telegram-i18n',
    'telegram_translate': 'telegram-translate',
    'bs4': 'beautifulsoup4',
    'requests': 'requests',
    'pillow': 'Pillow',
    'cv2': 'opencv-python',
    'yaml': 'PyYAML',
    'dotenv': 'python-dotenv',
    'dateutil': 'python-dateutil',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'flask': 'Flask',
    'django': 'Django',
    'sqlalchemy': 'SQLAlchemy',
    'asyncio': None, 'json': None, 'datetime': None, 'os': None, 'sys': None,
    're': None, 'time': None, 'math': None, 'random': None, 'logging': None,
    'threading': None, 'subprocess': None, 'zipfile': None, 'tempfile': None,
    'shutil': None, 'sqlite3': None, 'psutil': 'psutil', 'atexit': None, 'html': None
}

# --- Database Operations ---
DB_LOCK = threading.Lock()

def save_user_file(user_id, file_name, file_type='py'):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO user_files (user_id, file_name, file_type) VALUES (?, ?, ?)',
                      (user_id, file_name, file_type))
            conn.commit()
            if user_id not in user_files: user_files[user_id] = []
            user_files[user_id] = [(fn, ft) for fn, ft in user_files[user_id] if fn != file_name]
            user_files[user_id].append((file_name, file_type))
        except Exception as e: logger.error(f"❌ Error saving file for {user_id}, {file_name}: {e}")
        finally: conn.close()

def remove_user_file_db(user_id, file_name):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
            conn.commit()
            if user_id in user_files:
                user_files[user_id] = [f for f in user_files[user_id] if f[0] != file_name]
                if not user_files[user_id]: del user_files[user_id]
        except Exception as e: logger.error(f"❌ Error removing file for {user_id}, {file_name}: {e}")
        finally: conn.close()

def add_active_user(user_id):
    active_users.add(user_id)
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO active_users (user_id) VALUES (?)', (user_id,))
            conn.commit()
        except Exception as e: logger.error(f"❌ Error adding active user {user_id}: {e}")
        finally: conn.close()

def save_subscription(user_id, expiry):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            expiry_str = expiry.isoformat()
            c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)', (user_id, expiry_str))
            conn.commit()
            user_subscriptions[user_id] = {'expiry': expiry}
        except Exception as e: logger.error(f"❌ Error saving subscription for {user_id}: {e}")
        finally: conn.close()

def remove_subscription_db(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
            conn.commit()
            if user_id in user_subscriptions: del user_subscriptions[user_id]
        except Exception as e: logger.error(f"❌ Error removing subscription for {user_id}: {e}")
        finally: conn.close()

def add_admin_db(admin_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (admin_id,))
            conn.commit()
            admin_ids.add(admin_id)
        except Exception as e: logger.error(f"❌ Error adding admin {admin_id}: {e}")
        finally: conn.close()

def remove_admin_db(admin_id):
    if admin_id == OWNER_ID:
        return False
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('SELECT 1 FROM admins WHERE user_id = ?', (admin_id,))
            if c.fetchone():
                c.execute('DELETE FROM admins WHERE user_id = ?', (admin_id,))
                conn.commit()
                removed = c.rowcount > 0
                if removed: admin_ids.discard(admin_id)
                return removed
            admin_ids.discard(admin_id)
            return False
        except Exception as e:
            logger.error(f"❌ Error removing admin {admin_id}: {e}")
            return False
        finally: conn.close()

# --- Stylized Inline & Reply Keyboards ---
def create_main_menu_inline(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_updates = types.InlineKeyboardButton(BTN_UPDATES, url=UPDATE_CHANNEL)
    btn_upload  = types.InlineKeyboardButton(BTN_UPLOAD, callback_data='upload')
    btn_files   = types.InlineKeyboardButton(BTN_CHECK_FILES, callback_data='check_files')
    btn_speed   = types.InlineKeyboardButton(BTN_SPEED, callback_data='speed')
    btn_contact = types.InlineKeyboardButton(BTN_CONTACT, url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}')

    if user_id in admin_ids:
        btn_subs   = types.InlineKeyboardButton(BTN_SUBS, callback_data='subscription')
        btn_stats  = types.InlineKeyboardButton(BTN_STATS, callback_data='stats')
        btn_lock   = types.InlineKeyboardButton(
            f"🔒 {stylize('Lock Bot')}" if not bot_locked else f"🔓 {stylize('Unlock Bot')}",
            callback_data='lock_bot' if not bot_locked else 'unlock_bot'
        )
        btn_bcast  = types.InlineKeyboardButton(BTN_BROADCAST, callback_data='broadcast')
        btn_admin  = types.InlineKeyboardButton(BTN_ADMIN_PANEL, callback_data='admin_panel')
        btn_runall = types.InlineKeyboardButton(f"🟢 {stylize('Run All Scripts')}", callback_data='run_all_scripts')

        markup.add(btn_updates)
        markup.add(btn_upload, btn_files)
        markup.add(btn_speed, btn_subs)
        markup.add(btn_stats, btn_bcast)
        markup.add(btn_lock, btn_runall)
        markup.add(btn_admin)
        markup.add(btn_contact)
    else:
        markup.add(btn_updates)
        markup.add(btn_upload, btn_files)
        markup.add(btn_speed, types.InlineKeyboardButton(BTN_STATS, callback_data='stats'))
        markup.add(btn_contact)
    return markup

def create_reply_keyboard_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    layout_to_use = ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC if user_id in admin_ids else COMMAND_BUTTONS_LAYOUT_USER_SPEC
    for row_buttons_text in layout_to_use:
        markup.add(*[types.KeyboardButton(text) for text in row_buttons_text])
    return markup

def create_control_buttons(script_owner_id, file_name, is_running=True):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_running:
        markup.row(
            types.InlineKeyboardButton(f"🔴 {stylize('Stop')}", callback_data=f'stop_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton(f"🔄 {stylize('Restart')}", callback_data=f'restart_{script_owner_id}_{file_name}')
        )
        markup.row(
            types.InlineKeyboardButton(f"🗑️ {stylize('Delete')}", callback_data=f'delete_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton(f"📜 {stylize('Logs')}", callback_data=f'logs_{script_owner_id}_{file_name}')
        )
    else:
        markup.row(
            types.InlineKeyboardButton(f"🟢 {stylize('Start')}", callback_data=f'start_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton(f"🗑️ {stylize('Delete')}", callback_data=f'delete_{script_owner_id}_{file_name}')
        )
        markup.row(
            types.InlineKeyboardButton(f"📜 {stylize('View Logs')}", callback_data=f'logs_{script_owner_id}_{file_name}')
        )
    markup.add(types.InlineKeyboardButton(f"🔙 {stylize('Back to Files')}", callback_data='check_files'))
    return markup

def create_admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton(f"➕ {stylize('Add Admin')}", callback_data='add_admin'),
        types.InlineKeyboardButton(f"➖ {stylize('Remove Admin')}", callback_data='remove_admin')
    )
    markup.row(types.InlineKeyboardButton(f"📋 {stylize('List Admins')}", callback_data='list_admins'))
    markup.row(types.InlineKeyboardButton(f"🔙 {stylize('Back to Main')}", callback_data='back_to_main'))
    return markup

def create_subscription_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton(f"➕ {stylize('Add Subscription')}", callback_data='add_subscription'),
        types.InlineKeyboardButton(f"➖ {stylize('Remove Subscription')}", callback_data='remove_subscription')
    )
    markup.row(types.InlineKeyboardButton(f"🔍 {stylize('Check Subscription')}", callback_data='check_subscription'))
    markup.row(types.InlineKeyboardButton(f"🔙 {stylize('Back to Main')}", callback_data='back_to_main'))
    return markup

# --- File Handling ---
def handle_zip_file(downloaded_file_content, file_name_zip, message):
    user_id = message.from_user.id
    user_folder = get_user_folder(user_id)
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix=f"user_{user_id}_zip_")
        zip_path = os.path.join(temp_dir, file_name_zip)
        with open(zip_path, 'wb') as new_file:
            new_file.write(downloaded_file_content)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.infolist():
                member_path = os.path.abspath(os.path.join(temp_dir, member.filename))
                if not member_path.startswith(os.path.abspath(temp_dir)):
                    raise zipfile.BadZipFile(f"Zip has unsafe path: {member.filename}")
            zip_ref.extractall(temp_dir)

        extracted_items = os.listdir(temp_dir)
        py_files = [f for f in extracted_items if f.endswith('.py')]
        js_files = [f for f in extracted_items if f.endswith('.js')]
        req_file = 'requirements.txt' if 'requirements.txt' in extracted_items else None
        pkg_json = 'package.json' if 'package.json' in extracted_items else None

        if req_file:
            req_path = os.path.join(temp_dir, req_file)
            dep_msg = animate_frames(
                message.chat.id,
                [
                    f"{pe('hourglass')} <b>{stylize('Installing Python Dependencies')}</b>\n<blockquote>Reading <code>{h(req_file)}</code>...\n<code>{progress_bar(30)}</code></blockquote>",
                    f"{pe('gear')} <b>{stylize('Resolving Packages')}</b>\n<blockquote>Running <code>pip install -r</code>...\n<code>{progress_bar(75)}</code></blockquote>"
                ],
                reply_to_message=message
            )
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req_path],
                               capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
                safe_edit_message_text(f"{pe('check')} <b>{stylize('Python Dependencies Installed')}</b>\n<blockquote><code>{h(req_file)}</code> complete.\n<code>{progress_bar(100)}</code></blockquote>", message.chat.id, dep_msg.message_id)
            except subprocess.CalledProcessError as e:
                raw_err = (e.stderr or e.stdout or '')[:3200]
                safe_edit_message_text(f"{pe('cross')} <b>{stylize('Pip Install Failed')}</b>\n<pre>{h(raw_err)}</pre>", message.chat.id, dep_msg.message_id)
                return

        if pkg_json:
            dep_msg = animate_frames(
                message.chat.id,
                [
                    f"{pe('hourglass')} <b>{stylize('Installing Node Dependencies')}</b>\n<blockquote>Reading <code>{h(pkg_json)}</code>...\n<code>{progress_bar(30)}</code></blockquote>",
                    f"{pe('gear')} <b>{stylize('Building Node Modules')}</b>\n<blockquote>Running <code>npm install</code>...\n<code>{progress_bar(75)}</code></blockquote>"
                ],
                reply_to_message=message
            )
            try:
                subprocess.run(['npm', 'install'], capture_output=True, text=True, check=True, cwd=temp_dir, encoding='utf-8', errors='ignore')
                safe_edit_message_text(f"{pe('check')} <b>{stylize('Node Dependencies Installed')}</b>\n<blockquote><code>{h(pkg_json)}</code> complete.\n<code>{progress_bar(100)}</code></blockquote>", message.chat.id, dep_msg.message_id)
            except FileNotFoundError:
                safe_reply_to(message, f"{pe('cross')} <code>npm</code> not found.")
                return
            except subprocess.CalledProcessError as e:
                raw_err = (e.stderr or e.stdout or '')[:3200]
                safe_edit_message_text(f"{pe('cross')} <b>{stylize('NPM Install Failed')}</b>\n<pre>{h(raw_err)}</pre>", message.chat.id, dep_msg.message_id)
                return

        main_script_name = None; file_type = None
        for p in ['main.py', 'bot.py', 'app.py']:
            if p in py_files: main_script_name = p; file_type = 'py'; break
        if not main_script_name:
            for p in ['index.js', 'main.js', 'bot.js', 'app.js']:
                if p in js_files: main_script_name = p; file_type = 'js'; break
        if not main_script_name:
            if py_files: main_script_name = py_files[0]; file_type = 'py'
            elif js_files: main_script_name = js_files[0]; file_type = 'js'
        if not main_script_name:
            safe_reply_to(message, f"{pe('cross')} No <code>.py</code> or <code>.js</code> entry script found in archive.")
            return

        for item_name in os.listdir(temp_dir):
            src_path = os.path.join(temp_dir, item_name)
            dest_path = os.path.join(user_folder, item_name)
            if os.path.isdir(dest_path): shutil.rmtree(dest_path)
            elif os.path.exists(dest_path): os.remove(dest_path)
            shutil.move(src_path, dest_path)

        save_user_file(user_id, main_script_name, file_type)
        main_script_path = os.path.join(user_folder, main_script_name)
        safe_reply_to(message, f"{pe('rocket')} <b>{stylize('Archive Extracted')}</b>\n<blockquote>Launching <code>{h(main_script_name)}</code>...</blockquote>")

        if file_type == 'py':
            threading.Thread(target=run_script, args=(main_script_path, user_id, user_folder, main_script_name, message)).start()
        elif file_type == 'js':
            threading.Thread(target=run_js_script, args=(main_script_path, user_id, user_folder, main_script_name, message)).start()

    except zipfile.BadZipFile as e:
        safe_reply_to(message, f"{pe('cross')} Invalid or corrupted ZIP archive: <code>{h(e)}</code>")
    except Exception as e:
        safe_reply_to(message, f"{pe('cross')} Error processing ZIP: <code>{h(e)}</code>")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir)
            except Exception: pass

def handle_js_file(file_path, script_owner_id, user_folder, file_name, message):
    try:
        save_user_file(script_owner_id, file_name, 'js')
        threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, message)).start()
    except Exception as e:
        safe_reply_to(message, f"{pe('cross')} Error processing JS file: <code>{h(e)}</code>")

def handle_py_file(file_path, script_owner_id, user_folder, file_name, message):
    try:
        save_user_file(script_owner_id, file_name, 'py')
        threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, message)).start()
    except Exception as e:
        safe_reply_to(message, f"{pe('cross')} Error processing Python file: <code>{h(e)}</code>")

# --- Core Logic Functions ---
def _build_welcome_text(user_id, user_name, user_username):
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    limit_str = str(file_limit) if file_limit != float('inf') else stylize("Unlimited")
    expiry_info = ""

    if user_id == OWNER_ID:
        user_status = f"{pe('crown')} <b>{stylize('Owner')}</b>"
    elif user_id in admin_ids:
        user_status = f"{pe('shield')} <b>{stylize('Admin')}</b>"
    elif user_id in user_subscriptions:
        expiry_date = user_subscriptions[user_id].get('expiry')
        if expiry_date and expiry_date > datetime.now():
            days_left = (expiry_date - datetime.now()).days
            user_status = f"{pe('gem')} <b>{stylize('Premium Member')}</b>"
            expiry_info = f"\n{pe('hourglass')} <b>{stylize('Expires In')}:</b> <code>{days_left} days</code>"
        else:
            user_status = f"{pe('sparkles')} <b>{stylize('Free Tier')}</b> <i>({stylize('Expired')})</i>"
            remove_subscription_db(user_id)
    else:
        user_status = f"{pe('sparkles')} <b>{stylize('Free Tier')}</b>"

    return (
        f"{pe('sparkles')} <b>{stylize(BRAND_TITLE)}</b>\n"
        f"{pe('party')} {stylize('Welcome')}, <b>{h(user_name)}</b>\n\n"
        f"<blockquote>"
        f"{pe('bolt')} <b>{stylize('User ID')}:</b> <code>{user_id}</code>\n"
        f"{pe('megaphone')} <b>{stylize('Username')}:</b> <code>@{h(user_username or 'Not set')}</code>\n"
        f"{pe('gem')} <b>{stylize('Access Tier')}:</b> {user_status}{expiry_info}\n"
        f"{pe('folder')} <b>{stylize('Hosted Files')}:</b> <code>{current_files} / {limit_str}</code>"
        f"</blockquote>\n\n"
        f"{pe('rocket')} <i>{stylize('Host and run Python (.py), Node.js (.js), or ZIP (.zip) bots 24/7.')}</i>\n"
        f"{pe('gear')} {stylize('Select an action below to begin.')}"
    )

def _logic_send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    user_username = message.from_user.username

    if bot_locked and user_id not in admin_ids:
        safe_send_message(chat_id, f"{pe('lock')} <b>{stylize('System Locked')}</b>\n<blockquote>Maintenance in progress. Please check back shortly.</blockquote>")
        return

    user_bio = "No bio"
    photo_file_id = None
    try: user_bio = bot.get_chat(user_id).bio or "No bio"
    except Exception: pass
    try:
        user_profile_photos = bot.get_user_profile_photos(user_id, limit=1)
        if user_profile_photos.photos:
            photo_file_id = user_profile_photos.photos[0][-1].file_id
    except Exception: pass

    if user_id not in active_users:
        add_active_user(user_id)
        try:
            owner_notification = (
                f"{pe('party')} <b>{stylize('New User Joined')}</b>\n"
                f"<blockquote>"
                f"<b>{stylize('Name')}:</b> {h(user_name)}\n"
                f"<b>{stylize('Handle')}:</b> @{h(user_username or 'N/A')}\n"
                f"<b>{stylize('ID')}:</b> <code>{user_id}</code>\n"
                f"<b>{stylize('Bio')}:</b> {h(user_bio)}"
                f"</blockquote>"
            )
            safe_send_message(OWNER_ID, owner_notification, effect='confetti')
            if photo_file_id:
                bot.send_photo(OWNER_ID, photo_file_id, caption=f"Profile of {user_id}")
        except Exception as e:
            logger.error(f"⚠️ Failed to notify owner about new user {user_id}: {e}")

    welcome_msg_text = _build_welcome_text(user_id, user_name, user_username)
    main_reply_markup = create_reply_keyboard_main_menu(user_id)

    if photo_file_id:
        try: bot.send_photo(chat_id, photo_file_id)
        except Exception: pass

    if ENABLE_ANIMATIONS and ANIMATION_DELAY > 0:
        boot_msg = safe_send_message(
            chat_id,
            f"{pe('bolt')} <b>{stylize(BRAND_TITLE)}</b>\n<blockquote>{stylize('Initializing neural workspace...')}\n<code>{progress_bar(25)}</code></blockquote>"
        )
        time.sleep(ANIMATION_DELAY)
        safe_edit_message_text(
            f"{pe('gem')} <b>{stylize(BRAND_TITLE)}</b>\n<blockquote>{stylize('Syncing encrypted vault & tier...')}\n<code>{progress_bar(68)}</code></blockquote>",
            chat_id, boot_msg.message_id
        )
        time.sleep(ANIMATION_DELAY)
        safe_edit_message_text(
            f"{pe('rocket')} <b>{stylize(BRAND_TITLE)}</b>\n<blockquote>{stylize('Workspace ready.')}\n<code>{progress_bar(100)}</code></blockquote>",
            chat_id, boot_msg.message_id
        )
        time.sleep(max(0.12, ANIMATION_DELAY * 0.6))
        try: bot.delete_message(chat_id, boot_msg.message_id)
        except Exception: pass

    safe_send_message(chat_id, welcome_msg_text, reply_markup=main_reply_markup, effect='confetti')

def _logic_updates_channel(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(BTN_UPDATES, url=UPDATE_CHANNEL))
    safe_reply_to(
        message,
        f"{pe('megaphone')} <b>{stylize('Official Updates Channel')}</b>\n"
        f"<blockquote>{stylize('Follow releases, uptime alerts, and premium feature drops.')}</blockquote>",
        reply_markup=markup
    )

def _logic_upload_file(message):
    user_id = message.from_user.id
    if bot_locked and user_id not in admin_ids:
        safe_reply_to(message, f"{pe('lock')} <b>{stylize('System Locked')}</b> — Uploads are temporarily paused.")
        return

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else stylize("Unlimited")
        safe_reply_to(message, f"{pe('warning')} <b>{stylize('Slot Limit Reached')}</b> (<code>{current_files}/{limit_str}</code>)\n<blockquote>Delete an older script first to free up space.</blockquote>")
        return

    safe_reply_to(
        message,
        f"{pe('rocket')} <b>{stylize('Ready For Deployment')}</b>\n"
        f"<blockquote>Send your Python (<code>.py</code>), Node.js (<code>.js</code>), or ZIP (<code>.zip</code>) package directly here.</blockquote>"
    )

def _logic_check_files(message):
    user_id = message.from_user.id
    user_files_list = user_files.get(user_id, [])
    if not user_files_list:
        safe_reply_to(
            message,
            f"{pe('folder')} <b>{stylize('Your Script Vault')}</b>\n"
            f"<blockquote><i>{stylize('No files uploaded yet. Tap Upload File to deploy your first bot.')}</i></blockquote>"
        )
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files_list):
        is_running = is_bot_running(user_id, file_name)
        status_icon = "🟢 Online" if is_running else "🔴 Offline"
        btn_text = f"{file_name} ({file_type.upper()}) · {status_icon}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'file_{user_id}_{file_name}'))
    safe_reply_to(
        message,
        f"{pe('folder')} <b>{stylize('Your Script Vault')}</b>\n"
        f"<blockquote>{stylize('Select any hosted script below to manage process controls & live logs.')}</blockquote>",
        reply_markup=markup
    )

def _logic_bot_speed(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    start_time_ping = time.time()

    wait_msg = animate_frames(
        chat_id,
        [
            f"{pe('bolt')} <b>{stylize('Diagnostics')}</b> · ⠋ <i>{stylize('Measuring API latency...')}</i>",
            f"{pe('bolt')} <b>{stylize('Diagnostics')}</b> · ⠸ <i>{stylize('Sampling CPU & memory...')}</i>",
            f"{pe('bolt')} <b>{stylize('Diagnostics')}</b> · ⠧ <i>{stylize('Calibrating telemetry...')}</i>",
        ],
        reply_to_message=message
    )
    try:
        bot.send_chat_action(chat_id, 'typing')
        response_time = round((time.time() - start_time_ping) * 1000, 2)
        cpu_pct = psutil.cpu_percent(interval=None)
        ram_pct = psutil.virtual_memory().percent
        status = f"{pe('unlock')} {stylize('Unlocked')}" if not bot_locked else f"{pe('lock')} {stylize('Locked')}"
        if user_id == OWNER_ID: user_level = f"{pe('crown')} {stylize('Owner')}"
        elif user_id in admin_ids: user_level = f"{pe('shield')} {stylize('Admin')}"
        elif user_id in user_subscriptions and user_subscriptions[user_id].get('expiry', datetime.min) > datetime.now():
            user_level = f"{pe('gem')} {stylize('Premium')}"
        else:
            user_level = f"{pe('sparkles')} {stylize('Free User')}"

        speed_msg = (
            f"{pe('bolt')} <b>{stylize('System Speed & Telemetry')}</b>\n"
            f"<blockquote>"
            f"<b>{stylize('API Latency')}:</b> <code>{response_time} ms</code>\n"
            f"<b>{stylize('CPU Load')}:</b> <code>{cpu_pct}%</code>  ·  <b>{stylize('RAM')}:</b> <code>{ram_pct}%</code>\n"
            f"<b>{stylize('Bot Status')}:</b> {status}\n"
            f"<b>{stylize('Access Level')}:</b> {user_level}"
            f"</blockquote>"
        )
        safe_edit_message_text(speed_msg, chat_id, wait_msg.message_id)
    except Exception as e:
        logger.error(f"Error during speed test: {e}", exc_info=True)
        safe_edit_message_text(f"{pe('cross')} Error during speed test.", chat_id, wait_msg.message_id)

def _logic_contact_owner(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(BTN_CONTACT, url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}'))
    safe_reply_to(
        message,
        f"{pe('crown')} <b>{stylize('Direct Owner Support')}</b>\n"
        f"<blockquote>{stylize('Reach out for custom limits, premium access, or dedicated hosting.')}</blockquote>",
        reply_markup=markup
    )

# --- Admin Logic Functions ---
def _logic_subscriptions_panel(message):
    if message.from_user.id not in admin_ids:
        safe_reply_to(message, f"{pe('warning')} <b>{stylize('Admin Permissions Required')}</b>")
        return
    safe_reply_to(
        message,
        f"{pe('card')} <b>{stylize('Subscription Management')}</b>\n<blockquote>{stylize('Grant, inspect, or revoke premium user slots.')}</blockquote>",
        reply_markup=create_subscription_menu()
    )

def _logic_statistics(message):
    user_id = message.from_user.id
    total_users = len(active_users)
    total_files_records = sum(len(files) for files in user_files.values())

    running_bots_count = 0
    user_running_bots = 0
    for script_key_iter, script_info_iter in list(bot_scripts.items()):
        s_owner_id, _ = script_key_iter.split('_', 1)
        if is_bot_running(int(s_owner_id), script_info_iter['file_name']):
            running_bots_count += 1
            if int(s_owner_id) == user_id:
                user_running_bots += 1

    admin_extra = ""
    if user_id in admin_ids:
        lock_state = f"{pe('lock')} {stylize('Locked')}" if bot_locked else f"{pe('unlock')} {stylize('Unlocked')}"
        admin_extra = f"\n<b>{stylize('Gateway')}:</b> {lock_state}"

    stats_msg = (
        f"{pe('stats')} <b>{stylize('Live Platform Statistics')}</b>\n"
        f"<blockquote>"
        f"<b>{stylize('Total Users')}:</b> <code>{total_users}</code>\n"
        f"<b>{stylize('Stored Scripts')}:</b> <code>{total_files_records}</code>\n"
        f"<b>{stylize('Active Processes')}:</b> <code>{running_bots_count}</code>\n"
        f"<b>{stylize('Your Running Bots')}:</b> <code>{user_running_bots}</code>"
        f"{admin_extra}"
        f"</blockquote>"
    )
    safe_reply_to(message, stats_msg)

def _logic_broadcast_init(message):
    if message.from_user.id not in admin_ids:
        safe_reply_to(message, f"{pe('warning')} <b>{stylize('Admin Permissions Required')}</b>")
        return
    msg = safe_reply_to(message, f"{pe('megaphone')} <b>{stylize('Broadcast Studio')}</b>\n<blockquote>Send text or media to broadcast to all users, or /cancel to abort.</blockquote>")
    bot.register_next_step_handler(msg, process_broadcast_message)

def _logic_toggle_lock_bot(message):
    if message.from_user.id not in admin_ids:
        safe_reply_to(message, f"{pe('warning')} <b>{stylize('Admin Permissions Required')}</b>")
        return
    global bot_locked
    bot_locked = not bot_locked
    status_label = stylize("Locked") if bot_locked else stylize("Unlocked")
    icon = pe('lock') if bot_locked else pe('unlock')
    safe_reply_to(message, f"{icon} <b>{stylize('Bot Status Updated')}:</b> {status_label}")

def _logic_admin_panel(message):
    if message.from_user.id not in admin_ids:
        safe_reply_to(message, f"{pe('warning')} <b>{stylize('Admin Permissions Required')}</b>")
        return
    safe_reply_to(
        message,
        f"{pe('crown')} <b>{stylize('Admin Command Center')}</b>\n<blockquote>{stylize('Promote, demote, or audit system administrators.')}</blockquote>",
        reply_markup=create_admin_panel()
    )

def _logic_run_all_scripts(message_or_call):
    if isinstance(message_or_call, telebot.types.Message):
        admin_user_id = message_or_call.from_user.id
        admin_chat_id = message_or_call.chat.id
        reply_func = lambda text, **kwargs: safe_reply_to(message_or_call, text, **kwargs)
        admin_message_obj_for_script_runner = message_or_call
    elif isinstance(message_or_call, telebot.types.CallbackQuery):
        admin_user_id = message_or_call.from_user.id
        admin_chat_id = message_or_call.message.chat.id
        bot.answer_callback_query(message_or_call.id)
        reply_func = lambda text, **kwargs: safe_send_message(admin_chat_id, text, **kwargs)
        admin_message_obj_for_script_runner = message_or_call.message
    else:
        return

    if admin_user_id not in admin_ids:
        reply_func(f"{pe('warning')} <b>{stylize('Admin Permissions Required')}</b>")
        return

    progress_msg = safe_send_message(
        admin_chat_id,
        f"{pe('hourglass')} <b>{stylize('Batch Script Launcher')}</b>\n<blockquote>{stylize('Scanning user vaults...')}\n<code>{progress_bar(15)}</code></blockquote>"
    )

    started_count = 0; attempted_users = 0; skipped_files = 0; error_files_details = []
    all_user_files_snapshot = dict(user_files)

    for target_user_id, files_for_user in all_user_files_snapshot.items():
        if not files_for_user: continue
        attempted_users += 1
        user_folder = get_user_folder(target_user_id)

        for file_name, file_type in files_for_user:
            if not is_bot_running(target_user_id, file_name):
                file_path = os.path.join(user_folder, file_name)
                if os.path.exists(file_path):
                    try:
                        if file_type == 'py':
                            threading.Thread(target=run_script, args=(file_path, target_user_id, user_folder, file_name, admin_message_obj_for_script_runner)).start()
                            started_count += 1
                        elif file_type == 'js':
                            threading.Thread(target=run_js_script, args=(file_path, target_user_id, user_folder, file_name, admin_message_obj_for_script_runner)).start()
                            started_count += 1
                        else:
                            error_files_details.append(f"<code>{h(file_name)}</code> (User {target_user_id}) - Unknown type")
                            skipped_files += 1
                        time.sleep(0.5)
                    except Exception:
                        error_files_details.append(f"<code>{h(file_name)}</code> (User {target_user_id}) - Start error")
                        skipped_files += 1
                else:
                    error_files_details.append(f"<code>{h(file_name)}</code> (User {target_user_id}) - Missing")
                    skipped_files += 1

    details_block = ""
    if skipped_files > 0 and error_files_details:
        details_block = "\n<b>Skipped:</b>\n" + "\n".join(f"• {err}" for err in error_files_details[:5])

    summary_msg = (
        f"{pe('check')} <b>{stylize('Batch Launch Complete')}</b>\n"
        f"<blockquote>"
        f"<b>{stylize('Started')}:</b> <code>{started_count}</code>\n"
        f"<b>{stylize('Users Processed')}:</b> <code>{attempted_users}</code>\n"
        f"<b>{stylize('Skipped/Errors')}:</b> <code>{skipped_files}</code>{details_block}"
        f"</blockquote>"
    )
    safe_edit_message_text(summary_msg, admin_chat_id, progress_msg.message_id)

# --- Command Handlers & Text Handlers ---
@bot.message_handler(commands=['start', 'help'])
def command_send_welcome(message): _logic_send_welcome(message)

@bot.message_handler(commands=['status'])
def command_show_status(message): _logic_statistics(message)

BUTTON_TEXT_TO_LOGIC = {
    BTN_UPDATES:     _logic_updates_channel,
    BTN_UPLOAD:      _logic_upload_file,
    BTN_CHECK_FILES: _logic_check_files,
    BTN_SPEED:       _logic_bot_speed,
    BTN_CONTACT:     _logic_contact_owner,
    BTN_STATS:       _logic_statistics,
    BTN_SUBS:        _logic_subscriptions_panel,
    BTN_BROADCAST:   _logic_broadcast_init,
    BTN_LOCK:        _logic_toggle_lock_bot,
    BTN_RUN_ALL:     _logic_run_all_scripts,
    BTN_ADMIN_PANEL: _logic_admin_panel,
}

@bot.message_handler(func=lambda message: message.text in BUTTON_TEXT_TO_LOGIC)
def handle_button_text(message):
    logic_func = BUTTON_TEXT_TO_LOGIC.get(message.text)
    if logic_func: logic_func(message)

@bot.message_handler(commands=['updateschannel'])
def command_updates_channel(message): _logic_updates_channel(message)
@bot.message_handler(commands=['uploadfile'])
def command_upload_file(message): _logic_upload_file(message)
@bot.message_handler(commands=['checkfiles'])
def command_check_files(message): _logic_check_files(message)
@bot.message_handler(commands=['botspeed'])
def command_bot_speed(message): _logic_bot_speed(message)
@bot.message_handler(commands=['contactowner'])
def command_contact_owner(message): _logic_contact_owner(message)
@bot.message_handler(commands=['subscriptions'])
def command_subscriptions(message): _logic_subscriptions_panel(message)
@bot.message_handler(commands=['statistics'])
def command_statistics(message): _logic_statistics(message)
@bot.message_handler(commands=['broadcast'])
def command_broadcast(message): _logic_broadcast_init(message)
@bot.message_handler(commands=['lockbot'])
def command_lock_bot(message): _logic_toggle_lock_bot(message)
@bot.message_handler(commands=['adminpanel'])
def command_admin_panel(message): _logic_admin_panel(message)
@bot.message_handler(commands=['runningallcode'])
def command_run_all_code(message): _logic_run_all_scripts(message)

@bot.message_handler(commands=['ping'])
def ping(message):
    start_ping_time = time.time()
    msg = animate_frames(
        message.chat.id,
        [
            f"{pe('bolt')} <i>{stylize('Pinging core...')}</i>",
            f"{pe('bolt')} <b>{stylize('Pong!')}</b>"
        ],
        reply_to_message=message
    )
    latency = round((time.time() - start_ping_time) * 1000, 2)
    safe_edit_message_text(f"{pe('bolt')} <b>{stylize('Pong!')}</b> · <code>{latency} ms</code>", message.chat.id, msg.message_id)

# --- Document (File) Handler ---
@bot.message_handler(content_types=['document'])
def handle_file_upload_doc(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    doc = message.document

    if bot_locked and user_id not in admin_ids:
        safe_reply_to(message, f"{pe('lock')} <b>{stylize('System Locked')}</b> — Uploads paused.")
        return

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else stylize("Unlimited")
        safe_reply_to(message, f"{pe('warning')} <b>{stylize('File Limit Reached')}</b> (<code>{current_files}/{limit_str}</code>). Delete files via /checkfiles.")
        return

    file_name = doc.file_name
    if not file_name:
        safe_reply_to(message, f"{pe('warning')} Missing filename.")
        return
    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext not in ['.py', '.js', '.zip']:
        safe_reply_to(message, f"{pe('warning')} Unsupported type! Only <code>.py</code>, <code>.js</code>, <code>.zip</code> allowed.")
        return
    max_file_size = 20 * 1024 * 1024
    if doc.file_size > max_file_size:
        safe_reply_to(message, f"{pe('warning')} File exceeds <code>20 MB</code> limit.")
        return

    try:
        try:
            bot.forward_message(OWNER_ID, chat_id, message.message_id)
            safe_send_message(OWNER_ID, f"{pe('folder')} <b>{stylize('Incoming Upload')}</b>: <code>{h(file_name)}</code> from {h(message.from_user.first_name)} (<code>{user_id}</code>)")
        except Exception as e:
            logger.error(f"Failed to forward file to OWNER_ID: {e}")

        download_wait_msg = animate_frames(
            chat_id,
            [
                f"{pe('hourglass')} <b>{stylize('Downloading')}</b> <code>{h(file_name)}</code>\n<blockquote><code>{progress_bar(25)}</code></blockquote>",
                f"{pe('bolt')} <b>{stylize('Streaming Binary')}</b> <code>{h(file_name)}</code>\n<blockquote><code>{progress_bar(65)}</code></blockquote>"
            ],
            reply_to_message=message
        )
        file_info_tg_doc = bot.get_file(doc.file_id)
        downloaded_file_content = bot.download_file(file_info_tg_doc.file_path)
        safe_edit_message_text(
            f"{pe('check')} <b>{stylize('Download Complete')}</b> <code>{h(file_name)}</code>\n<blockquote><code>{progress_bar(100)}</code> · {stylize('Initializing runner...')}</blockquote>",
            chat_id, download_wait_msg.message_id
        )

        user_folder = get_user_folder(user_id)
        if file_ext == '.zip':
            handle_zip_file(downloaded_file_content, file_name, message)
        else:
            file_path = os.path.join(user_folder, file_name)
            with open(file_path, 'wb') as f:
                f.write(downloaded_file_content)
            if file_ext == '.js': handle_js_file(file_path, user_id, user_folder, file_name, message)
            elif file_ext == '.py': handle_py_file(file_path, user_id, user_folder, file_name, message)
    except telebot.apihelper.ApiTelegramException as e:
        if "file is too big" in str(e).lower():
            safe_reply_to(message, f"{pe('cross')} Telegram API Error: File too large (~20MB limit).")
        else:
            safe_reply_to(message, f"{pe('cross')} Telegram API Error: <code>{h(e)}</code>")
    except Exception as e:
        safe_reply_to(message, f"{pe('cross')} Unexpected error: <code>{h(e)}</code>")

# --- Callback Query Handlers ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data

    if bot_locked and user_id not in admin_ids and data not in ['back_to_main', 'speed', 'stats']:
        bot.answer_callback_query(call.id, "⚠️ Bot locked by admin.", show_alert=True)
        return
    try:
        if data == 'upload': upload_callback(call)
        elif data == 'check_files': check_files_callback(call)
        elif data.startswith('file_'): file_control_callback(call)
        elif data.startswith('start_'): start_bot_callback(call)
        elif data.startswith('stop_'): stop_bot_callback(call)
        elif data.startswith('restart_'): restart_bot_callback(call)
        elif data.startswith('delete_'): delete_bot_callback(call)
        elif data.startswith('logs_'): logs_bot_callback(call)
        elif data == 'speed': speed_callback(call)
        elif data == 'back_to_main': back_to_main_callback(call)
        elif data.startswith('confirm_broadcast_'): handle_confirm_broadcast(call)
        elif data == 'cancel_broadcast': handle_cancel_broadcast(call)
        elif data == 'subscription': admin_required_callback(call, subscription_management_callback)
        elif data == 'stats': stats_callback(call)
        elif data == 'lock_bot': admin_required_callback(call, lock_bot_callback)
        elif data == 'unlock_bot': admin_required_callback(call, unlock_bot_callback)
        elif data == 'run_all_scripts': admin_required_callback(call, run_all_scripts_callback)
        elif data == 'broadcast': admin_required_callback(call, broadcast_init_callback)
        elif data == 'admin_panel': admin_required_callback(call, admin_panel_callback)
        elif data == 'add_admin': owner_required_callback(call, add_admin_init_callback)
        elif data == 'remove_admin': owner_required_callback(call, remove_admin_init_callback)
        elif data == 'list_admins': admin_required_callback(call, list_admins_callback)
        elif data == 'add_subscription': admin_required_callback(call, add_subscription_init_callback)
        elif data == 'remove_subscription': admin_required_callback(call, remove_subscription_init_callback)
        elif data == 'check_subscription': admin_required_callback(call, check_subscription_init_callback)
        else:
            bot.answer_callback_query(call.id, "Unknown action.")
    except Exception as e:
        logger.error(f"Error handling callback '{data}' for {user_id}: {e}", exc_info=True)
        try: bot.answer_callback_query(call.id, "Error processing request.", show_alert=True)
        except Exception: pass

def admin_required_callback(call, func_to_run):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "⚠️ Admin permissions required.", show_alert=True)
        return
    func_to_run(call)

def owner_required_callback(call, func_to_run):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "⚠️ Owner permissions required.", show_alert=True)
        return
    func_to_run(call)

def upload_callback(call):
    user_id = call.from_user.id
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
        bot.answer_callback_query(call.id, f"⚠️ File limit ({current_files}/{limit_str}) reached.", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    safe_send_message(call.message.chat.id, f"{pe('rocket')} <b>{stylize('Upload Ready')}</b>\n<blockquote>Send your Python (<code>.py</code>), JS (<code>.js</code>), or ZIP (<code>.zip</code>) file.</blockquote>")

def check_files_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    user_files_list = user_files.get(user_id, [])
    if not user_files_list:
        bot.answer_callback_query(call.id, "⚠️ No files uploaded.", show_alert=True)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"🔙 {stylize('Back to Main')}", callback_data='back_to_main'))
        safe_edit_message_text(
            f"{pe('folder')} <b>{stylize('Your Script Vault')}</b>\n<blockquote><i>{stylize('No files uploaded yet.')}</i></blockquote>",
            chat_id, call.message.message_id, reply_markup=markup
        )
        return

    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files_list):
        is_running = is_bot_running(user_id, file_name)
        status_icon = "🟢 Online" if is_running else "🔴 Offline"
        btn_text = f"{file_name} ({file_type.upper()}) · {status_icon}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'file_{user_id}_{file_name}'))
    markup.add(types.InlineKeyboardButton(f"🔙 {stylize('Back to Main')}", callback_data='back_to_main'))
    safe_edit_message_text(
        f"{pe('folder')} <b>{stylize('Your Script Vault')}</b>\n<blockquote>{stylize('Tap any script to manage controls & logs.')}</blockquote>",
        chat_id, call.message.message_id, reply_markup=markup
    )

def file_control_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ You can only manage your own files.", show_alert=True)
            check_files_callback(call)
            return

        user_files_list = user_files.get(script_owner_id, [])
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True)
            check_files_callback(call)
            return

        bot.answer_callback_query(call.id)
        is_running = is_bot_running(script_owner_id, file_name)
        status_text = f"{pe('dot_green')} <b>{stylize('Running')}</b>" if is_running else f"{pe('dot_red')} <b>{stylize('Stopped')}</b>"
        file_type = next((f[1] for f in user_files_list if f[0] == file_name), '?')
        safe_edit_message_text(
            f"{pe('gear')} <b>{stylize('Process Controls')}</b>\n"
            f"<blockquote>"
            f"<b>{stylize('Script')}:</b> <code>{h(file_name)}</code> ({file_type.upper()})\n"
            f"<b>{stylize('Owner')}:</b> <code>{script_owner_id}</code>\n"
            f"<b>{stylize('Status')}:</b> {status_text}"
            f"</blockquote>",
            call.message.chat.id, call.message.message_id,
            reply_markup=create_control_buttons(script_owner_id, file_name, is_running)
        )
    except Exception as e:
        logger.error(f"Error in file_control_callback: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "An error occurred.", show_alert=True)

def start_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        file_type = file_info[1]
        user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name)

        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, f"⚠️ File missing! Re-upload.", show_alert=True)
            remove_user_file_db(script_owner_id, file_name); check_files_callback(call); return

        if is_bot_running(script_owner_id, file_name):
            bot.answer_callback_query(call.id, f"⚠️ Script already running.", show_alert=True)
            bot.edit_message_reply_markup(chat_id_for_reply, call.message.message_id, reply_markup=create_control_buttons(script_owner_id, file_name, True))
            return

        bot.answer_callback_query(call.id, f"🚀 Starting {file_name}...")
        animate_frames(
            chat_id_for_reply,
            [
                f"{pe('hourglass')} <b>{stylize('Booting Process')}</b> <code>{h(file_name)}</code>\n<blockquote><code>{progress_bar(45)}</code></blockquote>",
                f"{pe('rocket')} <b>{stylize('Launching Runtime')}</b> <code>{h(file_name)}</code>\n<blockquote><code>{progress_bar(85)}</code></blockquote>"
            ],
            existing_msg=call.message
        )
        if file_type == 'py':
            threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        elif file_type == 'js':
            threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()

        time.sleep(1.5)
        is_now_running = is_bot_running(script_owner_id, file_name)
        status_text = f"{pe('dot_green')} <b>{stylize('Running')}</b>" if is_now_running else f"{pe('hourglass')} <b>{stylize('Starting...')}</b>"
        safe_edit_message_text(
            f"{pe('gear')} <b>{stylize('Process Controls')}</b>\n<blockquote><b>{stylize('Script')}:</b> <code>{h(file_name)}</code>\n<b>{stylize('Status')}:</b> {status_text}</blockquote>",
            chat_id_for_reply, call.message.message_id,
            reply_markup=create_control_buttons(script_owner_id, file_name, is_now_running)
        )
    except Exception as e:
        logger.error(f"Error in start_bot_callback: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error starting script.", show_alert=True)

def stop_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        file_type = file_info[1]
        script_key = f"{script_owner_id}_{file_name}"
        bot.answer_callback_query(call.id, f"🛑 Stopping {file_name}...")
        process_info = bot_scripts.get(script_key)
        if process_info:
            kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]

        safe_edit_message_text(
            f"{pe('gear')} <b>{stylize('Process Controls')}</b>\n"
            f"<blockquote><b>{stylize('Script')}:</b> <code>{h(file_name)}</code> ({file_type.upper()})\n"
            f"<b>{stylize('Status')}:</b> {pe('dot_red')} <b>{stylize('Stopped')}</b></blockquote>",
            chat_id_for_reply, call.message.message_id,
            reply_markup=create_control_buttons(script_owner_id, file_name, False)
        )
    except Exception as e:
        logger.error(f"Error in stop_bot_callback: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error stopping script.", show_alert=True)

def restart_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        file_type = file_info[1]; user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name); script_key = f"{script_owner_id}_{file_name}"

        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, f"⚠️ File missing!", show_alert=True)
            remove_user_file_db(script_owner_id, file_name)
            if script_key in bot_scripts: del bot_scripts[script_key]
            check_files_callback(call); return

        bot.answer_callback_query(call.id, f"🔄 Restarting {file_name}...")
        animate_frames(
            chat_id_for_reply,
            [
                f"{pe('hourglass')} <b>{stylize('Cycling Process')}</b> <code>{h(file_name)}</code>\n<blockquote><code>{progress_bar(35)}</code></blockquote>",
                f"{pe('rocket')} <b>{stylize('Re-initializing')}</b> <code>{h(file_name)}</code>\n<blockquote><code>{progress_bar(80)}</code></blockquote>"
            ],
            existing_msg=call.message
        )
        if is_bot_running(script_owner_id, file_name):
            process_info = bot_scripts.get(script_key)
            if process_info: kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]
            time.sleep(1.2)

        if file_type == 'py':
            threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        elif file_type == 'js':
            threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()

        time.sleep(1.5)
        is_now_running = is_bot_running(script_owner_id, file_name)
        status_text = f"{pe('dot_green')} <b>{stylize('Running')}</b>" if is_now_running else f"{pe('hourglass')} <b>{stylize('Starting...')}</b>"
        safe_edit_message_text(
            f"{pe('gear')} <b>{stylize('Process Controls')}</b>\n<blockquote><b>{stylize('Script')}:</b> <code>{h(file_name)}</code>\n<b>{stylize('Status')}:</b> {status_text}</blockquote>",
            chat_id_for_reply, call.message.message_id,
            reply_markup=create_control_buttons(script_owner_id, file_name, is_now_running)
        )
    except Exception as e:
        logger.error(f"Error in restart_bot_callback: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error restarting.", show_alert=True)

def delete_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        bot.answer_callback_query(call.id, f"🗑️ Deleting {file_name}...")
        script_key = f"{script_owner_id}_{file_name}"
        if is_bot_running(script_owner_id, file_name):
            process_info = bot_scripts.get(script_key)
            if process_info: kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]
            time.sleep(0.5)

        user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name)
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        for path in [file_path, log_path]:
            if os.path.exists(path):
                try: os.remove(path)
                except OSError: pass

        remove_user_file_db(script_owner_id, file_name)
        safe_edit_message_text(
            f"{pe('check')} <b>{stylize('Script Deleted')}</b>\n<blockquote><code>{h(file_name)}</code> removed cleanly from vault.</blockquote>",
            chat_id_for_reply, call.message.message_id, reply_markup=None
        )
    except Exception as e:
        logger.error(f"Error in delete_bot_callback: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error deleting.", show_alert=True)

def logs_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_folder = get_user_folder(script_owner_id)
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        if not os.path.exists(log_path):
            bot.answer_callback_query(call.id, f"⚠️ No logs for '{file_name}'.", show_alert=True); return

        bot.answer_callback_query(call.id)
        file_size = os.path.getsize(log_path)
        max_log_kb = 100; max_tg_msg = 3800
        if file_size == 0:
            log_content = "(Log empty)"
        elif file_size > max_log_kb * 1024:
            with open(log_path, 'rb') as f:
                f.seek(-max_log_kb * 1024, os.SEEK_END)
                log_content = "(Last 100 KB)\n...\n" + f.read().decode('utf-8', errors='ignore')
        else:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()

        if len(log_content) > max_tg_msg:
            log_content = "...\n" + log_content[-max_tg_msg:]
        if not log_content.strip():
            log_content = "(No visible content)"

        safe_send_message(
            chat_id_for_reply,
            f"{pe('stats')} <b>{stylize('Live Logs')}</b> · <code>{h(file_name)}</code>\n<pre>{h(log_content)}</pre>"
        )
    except Exception as e:
        logger.error(f"Error in logs_bot_callback: {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error fetching logs.", show_alert=True)

def speed_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    start_cb_ping_time = time.time()
    bot.answer_callback_query(call.id)
    animate_frames(
        chat_id,
        [
            f"{pe('bolt')} <b>{stylize('Diagnostics')}</b> · ⠋ <i>{stylize('Measuring API latency...')}</i>",
            f"{pe('bolt')} <b>{stylize('Diagnostics')}</b> · ⠸ <i>{stylize('Sampling CPU & memory...')}</i>",
        ],
        existing_msg=call.message
    )
    try:
        bot.send_chat_action(chat_id, 'typing')
        response_time = round((time.time() - start_cb_ping_time) * 1000, 2)
        cpu_pct = psutil.cpu_percent(interval=None)
        ram_pct = psutil.virtual_memory().percent
        status = f"{pe('unlock')} {stylize('Unlocked')}" if not bot_locked else f"{pe('lock')} {stylize('Locked')}"
        if user_id == OWNER_ID: user_level = f"{pe('crown')} {stylize('Owner')}"
        elif user_id in admin_ids: user_level = f"{pe('shield')} {stylize('Admin')}"
        elif user_id in user_subscriptions and user_subscriptions[user_id].get('expiry', datetime.min) > datetime.now():
            user_level = f"{pe('gem')} {stylize('Premium')}"
        else:
            user_level = f"{pe('sparkles')} {stylize('Free User')}"

        speed_msg = (
            f"{pe('bolt')} <b>{stylize('System Speed & Telemetry')}</b>\n"
            f"<blockquote>"
            f"<b>{stylize('API Latency')}:</b> <code>{response_time} ms</code>\n"
            f"<b>{stylize('CPU Load')}:</b> <code>{cpu_pct}%</code>  ·  <b>{stylize('RAM')}:</b> <code>{ram_pct}%</code>\n"
            f"<b>{stylize('Bot Status')}:</b> {status}\n"
            f"<b>{stylize('Access Level')}:</b> {user_level}"
            f"</blockquote>"
        )
        safe_edit_message_text(speed_msg, chat_id, call.message.message_id, reply_markup=create_main_menu_inline(user_id))
    except Exception as e:
        logger.error(f"Error during speed test (cb): {e}", exc_info=True)
        safe_edit_message_text(f"{pe('cross')} Error in speed test.", chat_id, call.message.message_id, reply_markup=create_main_menu_inline(user_id))

def back_to_main_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    main_menu_text = _build_welcome_text(user_id, call.from_user.first_name, call.from_user.username)
    safe_edit_message_text(main_menu_text, chat_id, call.message.message_id, reply_markup=create_main_menu_inline(user_id))

# --- Admin Callback Implementations ---
def subscription_management_callback(call):
    bot.answer_callback_query(call.id)
    safe_edit_message_text(
        f"{pe('card')} <b>{stylize('Subscription Management')}</b>\n<blockquote>{stylize('Select an action below.')}</blockquote>",
        call.message.chat.id, call.message.message_id, reply_markup=create_subscription_menu()
    )

def stats_callback(call):
    bot.answer_callback_query(call.id)
    _logic_statistics(call.message)
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_main_menu_inline(call.from_user.id))
    except Exception: pass

def lock_bot_callback(call):
    global bot_locked; bot_locked = True
    bot.answer_callback_query(call.id, "🔒 Bot locked.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_main_menu_inline(call.from_user.id))
    except Exception: pass

def unlock_bot_callback(call):
    global bot_locked; bot_locked = False
    bot.answer_callback_query(call.id, "🔓 Bot unlocked.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_main_menu_inline(call.from_user.id))
    except Exception: pass

def run_all_scripts_callback(call):
    _logic_run_all_scripts(call)

def broadcast_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = safe_send_message(call.message.chat.id, f"{pe('megaphone')} <b>{stylize('Broadcast Studio')}</b>\n<blockquote>Send message to broadcast, or /cancel to abort.</blockquote>")
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    user_id = message.from_user.id
    if user_id not in admin_ids: safe_reply_to(message, f"{pe('warning')} Not authorized."); return
    if message.text and message.text.lower() == '/cancel': safe_reply_to(message, "Broadcast cancelled."); return

    broadcast_content = message.text
    if not broadcast_content and not (message.photo or message.video or message.document or message.sticker or message.voice or message.audio):
        safe_reply_to(message, f"{pe('warning')} Empty message. Send text/media or /cancel.")
        msg = safe_send_message(message.chat.id, f"{pe('megaphone')} Send broadcast message or /cancel.")
        bot.register_next_step_handler(msg, process_broadcast_message)
        return

    target_count = len(active_users)
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(f"✅ {stylize('Confirm & Send')}", callback_data=f"confirm_broadcast_{message.message_id}"),
        types.InlineKeyboardButton(f"❌ {stylize('Cancel')}", callback_data="cancel_broadcast")
    )
    preview_text = broadcast_content[:800].strip() if broadcast_content else "(Media message)"
    safe_reply_to(
        message,
        f"{pe('warning')} <b>{stylize('Confirm Broadcast')}</b>\n<blockquote><pre>{h(preview_text)}</pre>\nTargets: <b>{target_count}</b> users.</blockquote>",
        reply_markup=markup
    )

def handle_confirm_broadcast(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if user_id not in admin_ids: bot.answer_callback_query(call.id, "⚠️ Admin only.", show_alert=True); return
    try:
        original_message = call.message.reply_to_message
        if not original_message: raise ValueError("Could not retrieve original message.")
        broadcast_text = original_message.text if original_message.text else None
        broadcast_photo_id = original_message.photo[-1].file_id if original_message.photo else None
        broadcast_video_id = original_message.video.file_id if original_message.video else None
        if not (broadcast_text or broadcast_photo_id or broadcast_video_id):
            raise ValueError("Unsupported message type for broadcast.")

        bot.answer_callback_query(call.id, "🚀 Starting broadcast...")
        safe_edit_message_text(f"{pe('megaphone')} <b>{stylize('Broadcasting')}</b> to <code>{len(active_users)}</code> users...", chat_id, call.message.message_id)
        threading.Thread(target=execute_broadcast, args=(
            broadcast_text, broadcast_photo_id, broadcast_video_id,
            original_message.caption if (broadcast_photo_id or broadcast_video_id) else None,
            chat_id
        )).start()
    except Exception as e:
        safe_edit_message_text(f"{pe('cross')} Broadcast error: <code>{h(e)}</code>", chat_id, call.message.message_id)

def handle_cancel_broadcast(call):
    bot.answer_callback_query(call.id, "Broadcast cancelled.")
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception: pass

def execute_broadcast(broadcast_text, photo_id, video_id, caption, admin_chat_id):
    sent_count = 0; failed_count = 0; blocked_count = 0
    start_exec_time = time.time()
    users_to_broadcast = list(active_users); total_users = len(users_to_broadcast)
    batch_size = 25; delay_batches = 1.5

    for i, user_id_bc in enumerate(users_to_broadcast):
        try:
            if broadcast_text:
                bot.send_message(user_id_bc, broadcast_text)
            elif photo_id:
                bot.send_photo(user_id_bc, photo_id, caption=caption)
            elif video_id:
                bot.send_video(user_id_bc, video_id, caption=caption)
            sent_count += 1
        except telebot.apihelper.ApiTelegramException as e:
            err_desc = str(e).lower()
            if any(s in err_desc for s in ["bot was blocked", "user is deactivated", "chat not found", "kicked from", "restricted"]):
                blocked_count += 1
            elif "flood control" in err_desc or "too many requests" in err_desc:
                match = re.search(r"retry after (\d+)", err_desc)
                time.sleep(int(match.group(1)) + 1 if match else 5)
                try:
                    if broadcast_text: bot.send_message(user_id_bc, broadcast_text)
                    elif photo_id: bot.send_photo(user_id_bc, photo_id, caption=caption)
                    elif video_id: bot.send_video(user_id_bc, video_id, caption=caption)
                    sent_count += 1
                except Exception: failed_count += 1
            else:
                failed_count += 1
        except Exception:
            failed_count += 1

        if (i + 1) % batch_size == 0 and i < total_users - 1:
            time.sleep(delay_batches)
        elif i % 5 == 0:
            time.sleep(0.2)

    duration = round(time.time() - start_exec_time, 2)
    result_msg = (
        f"{pe('megaphone')} <b>{stylize('Broadcast Complete')}</b>\n"
        f"<blockquote>"
        f"{pe('check')} <b>{stylize('Sent')}:</b> <code>{sent_count}</code>\n"
        f"{pe('cross')} <b>{stylize('Failed')}:</b> <code>{failed_count}</code>\n"
        f"{pe('lock')} <b>{stylize('Blocked')}:</b> <code>{blocked_count}</code>\n"
        f"{pe('bolt')} <b>{stylize('Duration')}:</b> <code>{duration}s</code>"
        f"</blockquote>"
    )
    safe_send_message(admin_chat_id, result_msg, effect='confetti')

def admin_panel_callback(call):
    bot.answer_callback_query(call.id)
    safe_edit_message_text(
        f"{pe('crown')} <b>{stylize('Admin Command Center')}</b>\n<blockquote>{stylize('Manage system administrators.')}</blockquote>",
        call.message.chat.id, call.message.message_id, reply_markup=create_admin_panel()
    )

def add_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = safe_send_message(call.message.chat.id, f"{pe('crown')} Enter User ID to promote to Admin, or /cancel.")
    bot.register_next_step_handler(msg, process_add_admin_id)

def process_add_admin_id(message):
    if message.from_user.id != OWNER_ID: safe_reply_to(message, f"{pe('warning')} Owner only."); return
    if message.text.lower() == '/cancel': safe_reply_to(message, "Cancelled."); return
    try:
        new_admin_id = int(message.text.strip())
        if new_admin_id <= 0: raise ValueError("ID must be positive")
        if new_admin_id == OWNER_ID: safe_reply_to(message, "Owner is already Owner."); return
        if new_admin_id in admin_ids: safe_reply_to(message, f"User <code>{new_admin_id}</code> is already Admin."); return
        add_admin_db(new_admin_id)
        safe_reply_to(message, f"{pe('check')} User <code>{new_admin_id}</code> promoted to Admin.")
        try: safe_send_message(new_admin_id, f"{pe('party')} <b>{stylize('Promoted To Admin!')}</b>", effect='confetti')
        except Exception: pass
    except ValueError:
        msg = safe_reply_to(message, f"{pe('warning')} Invalid numerical ID. Try again or /cancel.")
        bot.register_next_step_handler(msg, process_add_admin_id)

def remove_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = safe_send_message(call.message.chat.id, f"{pe('crown')} Enter Admin User ID to remove, or /cancel.")
    bot.register_next_step_handler(msg, process_remove_admin_id)

def process_remove_admin_id(message):
    if message.from_user.id != OWNER_ID: safe_reply_to(message, f"{pe('warning')} Owner only."); return
    if message.text.lower() == '/cancel': safe_reply_to(message, "Cancelled."); return
    try:
        admin_id_remove = int(message.text.strip())
        if admin_id_remove <= 0: raise ValueError("ID must be positive")
        if admin_id_remove == OWNER_ID: safe_reply_to(message, "Owner cannot remove self."); return
        if admin_id_remove not in admin_ids: safe_reply_to(message, f"User <code>{admin_id_remove}</code> is not an Admin."); return
        if remove_admin_db(admin_id_remove):
            safe_reply_to(message, f"{pe('check')} Admin <code>{admin_id_remove}</code> removed.")
        else:
            safe_reply_to(message, f"{pe('cross')} Failed to remove admin.")
    except ValueError:
        msg = safe_reply_to(message, f"{pe('warning')} Invalid numerical ID. Try again or /cancel.")
        bot.register_next_step_handler(msg, process_remove_admin_id)

def list_admins_callback(call):
    bot.answer_callback_query(call.id)
    admin_list_str = "\n".join(
        f"• <code>{aid}</code> {'👑 <i>(Owner)</i>' if aid == OWNER_ID else '🛡️ <i>(Admin)</i>'}"
        for aid in sorted(list(admin_ids))
    )
    safe_edit_message_text(
        f"{pe('crown')} <b>{stylize('Authorized Administrators')}</b>\n<blockquote>{admin_list_str}</blockquote>",
        call.message.chat.id, call.message.message_id, reply_markup=create_admin_panel()
    )

def add_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = safe_send_message(call.message.chat.id, f"{pe('card')} Enter <code>USER_ID DAYS</code> (e.g. <code>12345678 30</code>) or /cancel.")
    bot.register_next_step_handler(msg, process_add_subscription_details)

def process_add_subscription_details(message):
    if message.from_user.id not in admin_ids: safe_reply_to(message, f"{pe('warning')} Not authorized."); return
    if message.text.lower() == '/cancel': safe_reply_to(message, "Cancelled."); return
    try:
        parts = message.text.split()
        if len(parts) != 2: raise ValueError("Use format: USER_ID DAYS")
        sub_user_id = int(parts[0].strip()); days = int(parts[1].strip())
        if sub_user_id <= 0 or days <= 0: raise ValueError("User ID and days must be positive")
        current_expiry = user_subscriptions.get(sub_user_id, {}).get('expiry')
        start_date = current_expiry if (current_expiry and current_expiry > datetime.now()) else datetime.now()
        new_expiry = start_date + timedelta(days=days)
        save_subscription(sub_user_id, new_expiry)
        safe_reply_to(message, f"{pe('check')} <b>{stylize('Subscription Updated')}</b>\n<blockquote>User: <code>{sub_user_id}</code>\nAdded: <code>{days} days</code>\nExpires: <code>{new_expiry:%Y-%m-%d}</code></blockquote>")
        try: safe_send_message(sub_user_id, f"{pe('gem')} <b>{stylize('Premium Activated!')}</b>\n<blockquote>Extended by <code>{days} days</code> (until <code>{new_expiry:%Y-%m-%d}</code>).</blockquote>", effect='confetti')
        except Exception: pass
    except ValueError as e:
        msg = safe_reply_to(message, f"{pe('warning')} {h(e)}. Try again or /cancel.")
        bot.register_next_step_handler(msg, process_add_subscription_details)

def remove_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = safe_send_message(call.message.chat.id, f"{pe('card')} Enter User ID to remove subscription, or /cancel.")
    bot.register_next_step_handler(msg, process_remove_subscription_id)

def process_remove_subscription_id(message):
    if message.from_user.id not in admin_ids: safe_reply_to(message, f"{pe('warning')} Not authorized."); return
    if message.text.lower() == '/cancel': safe_reply_to(message, "Cancelled."); return
    try:
        sub_user_id_remove = int(message.text.strip())
        if sub_user_id_remove <= 0: raise ValueError("ID must be positive")
        if sub_user_id_remove not in user_subscriptions:
            safe_reply_to(message, f"User <code>{sub_user_id_remove}</code> has no active subscription."); return
        remove_subscription_db(sub_user_id_remove)
        safe_reply_to(message, f"{pe('check')} Subscription removed for <code>{sub_user_id_remove}</code>.")
    except ValueError:
        msg = safe_reply_to(message, f"{pe('warning')} Invalid numerical ID. Try again or /cancel.")
        bot.register_next_step_handler(msg, process_remove_subscription_id)

def check_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = safe_send_message(call.message.chat.id, f"{pe('card')} Enter User ID to inspect subscription, or /cancel.")
    bot.register_next_step_handler(msg, process_check_subscription_id)

def process_check_subscription_id(message):
    if message.from_user.id not in admin_ids: safe_reply_to(message, f"{pe('warning')} Not authorized."); return
    if message.text.lower() == '/cancel': safe_reply_to(message, "Cancelled."); return
    try:
        sub_user_id_check = int(message.text.strip())
        if sub_user_id_check <= 0: raise ValueError("ID must be positive")
        if sub_user_id_check in user_subscriptions:
            expiry_dt = user_subscriptions[sub_user_id_check].get('expiry')
            if expiry_dt and expiry_dt > datetime.now():
                days_left = (expiry_dt - datetime.now()).days
                safe_reply_to(message, f"{pe('gem')} <b>{stylize('Active Subscription')}</b>\n<blockquote>User: <code>{sub_user_id_check}</code>\nExpires: <code>{expiry_dt:%Y-%m-%d %H:%M}</code> ({days_left} days left)</blockquote>")
            else:
                safe_reply_to(message, f"{pe('warning')} Subscription expired for <code>{sub_user_id_check}</code>.")
                remove_subscription_db(sub_user_id_check)
        else:
            safe_reply_to(message, f"ℹ️ User <code>{sub_user_id_check}</code> has no active subscription.")
    except ValueError:
        msg = safe_reply_to(message, f"{pe('warning')} Invalid numerical ID. Try again or /cancel.")
        bot.register_next_step_handler(msg, process_check_subscription_id)

# --- Cleanup Function ---
def cleanup():
    logger.warning("Shutdown. Cleaning up processes...")
    for key in list(bot_scripts.keys()):
        if key in bot_scripts:
            kill_process_tree(bot_scripts[key])
atexit.register(cleanup)

# --- Main Execution ---
if __name__ == '__main__':
    logger.info("=" * 40 + "\n🤖 Premium Bot Starting Up...\n" + "=" * 40)
    keep_alive()
    logger.info("🚀 Starting polling...")
    while True:
        try:
            bot.infinity_polling(logger_level=logging.INFO, timeout=60, long_polling_timeout=30)
        except requests.exceptions.ReadTimeout:
            logger.warning("Polling ReadTimeout. Restarting in 5s..."); time.sleep(5)
        except requests.exceptions.ConnectionError as ce:
            logger.error(f"Polling ConnectionError: {ce}. Retrying in 15s..."); time.sleep(15)
        except Exception as e:
            logger.critical(f"💥 Unrecoverable polling error: {e}", exc_info=True)
            time.sleep(30)
        finally:
            time.sleep(1)
