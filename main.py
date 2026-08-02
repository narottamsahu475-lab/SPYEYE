import asyncio
import aiohttp
import os
import re
import time
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Google Sheets Integration
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION & GLOBAL STATES ---
FOUR_SIM_API_KEY = "6788f58a862c093c2167b7e57d62e122"
SPYEYE_API_KEY = "TBRSUMANTHA1205"
BASE_URL = "https://spyeyeloots.online/up_yono"

# Google Sheets Config
SHEET_KEY = "1xIqGOP_NCWttETOpq5ScnTkqlbzKp1cwgqxpWhF0xnQ"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
sheet = None

def init_google_sheet():
    global sheet
    if not HAS_GSPREAD:
        print("⚠️ gspread package missing!")
        return None
    try:
        possible_paths = [
            BASE_DIR / "credentials.json",
            "/sdcard/Amit/test10/credentials.json",
            "credentials.json",
            os.path.expanduser("~/credentials.json"),
            "/etc/secrets/credentials.json",
        ]

        creds = None
        creds_json = os.getenv("GOOGLE_CREDENTIALS")

        if creds_json:
            creds = Credentials.from_service_account_info(
                json.loads(creds_json), scopes=SCOPES
            )
        else:
            for path in possible_paths:
                if os.path.exists(path):
                    print(f"📁 Found credentials at: {path}")
                    creds = Credentials.from_service_account_file(path, scopes=SCOPES)
                    break

        if not creds:
            print("⚠️ Credentials file not found!")
            return None

        client = gspread.authorize(creds)
        sheet_obj = client.open_by_key(SHEET_KEY).sheet1
        print("✅ Google Sheets Connected Successfully via Key!")
        return sheet_obj
    except Exception as e:
        print(f"Google Sheet Connection Warning/Error: {e}")
        return None

sheet = init_google_sheet()

GAME_MAP = {
    "567slots": {"api": "567slots", "ui": "567slots"},
    "MBMBet": {"api": "mbmbet", "ui": "MBMBet"},
    "Bingo": {"api": "bingo101", "ui": "Bingo"},
    "789Jackpot": {"api": "789jackpots", "ui": "789Jackpot"},
    "SpinCrush": {"api": "spincrush", "ui": "Spin Crush"},
    "HiRummy": {"api": "hirummy", "ui": "HiRummy"},
    "Maha": {"api": "mahagames", "ui": "Maha"},
    "YonoVip": {"api": "yonovip", "ui": "YonoVip"},
    "789Jackpots": {"api": "789jackpots", "ui": "789Jackpots"},
    "MaxRummy": {"api": "maxrummy", "ui": "MaxRummy"},
    "YonoGames": {"api": "yonogames", "ui": "YonoGames"},
    "INDRummy": {"api": "indrummy", "ui": "INDrummy"},
    "YonoSlots": {"api": "yonoslots", "ui": "YonoSlots"}
}

# Reverse map for API_TO_UI normalization
API_TO_UI = {v["api"].lower(): v["ui"] for v in GAME_MAP.values()}

live_stats = {
    "total_targeted": 0,
    "total_thread_count": 0,
    "active_threads": 0,
    "success_otps": 0,
    "already_registered": 0,
    "cancelled_orders": 0,
    "total_secured": 0,
    "system_status": "Ready to Start",
    "pipeline_running": False,
    "progress": 0,
    "eta": "---",
    "success_records": [],
    "error_logs": [],  
    "recent_activity": [],
    "game_analytics": {},
    "registration_summary": {},
    "activity_timeline": [],
    "otp_history": [],
    "health_check": {
        "internet": "Connected",
        "gateway": "Connected",
        "SPYEYE": "Connected"
    },
    "realtime_active_threads": 0,
    "realtime_already_logs": 0,
    "cancel_failed_logs": 0,
    "cancel_failed_numbers_list": [],
    "spyeye_balance": "₹0",
    "gateway_balance": "₹0",
    "selected_provider": "4sim"
}

stats_lock = asyncio.Lock()
buy_lock = asyncio.Lock()
stop_event = asyncio.Event()

logged_cancels = set()
active_already_tasks = set()

success_buy_count = 0
input_total_accounts = 0
active_task_counter = 0

global_provider = "4sim"
global_service_id = "1929"
global_otpdoctor_service_id = "16311"
global_otpdoctor_api_key = "v776afeph25jum1p3z7uk7blqc7vyac5"

def format_time_only(ts_val):
    if not ts_val:
        return "N/A"
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    if isinstance(ts_val, (int, float)):
        dt = datetime.fromtimestamp(ts_val, tz=ist_tz)
    elif isinstance(ts_val, datetime):
        dt = ts_val.astimezone(ist_tz)
    else:
        return str(ts_val)
    return dt.strftime("%I:%M:%S %p")

def get_ist_time():
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_tz).strftime("%d %B %Y, %I:%M:%S %p")

async def log_otp_history(phone, game_name, otp_code, send_time, rec_time, verified_time, status_text):
    async with stats_lock:
        live_stats["otp_history"].insert(0, {
            "phone": phone,
            "game_name": game_name,
            "send_otp_time": format_time_only(send_time),
            "otp_code": otp_code,
            "otp_received_time": format_time_only(rec_time),
            "otp_verified_time": format_time_only(verified_time),
            "status": status_text
        })
        if len(live_stats["otp_history"]) > 300:
            live_stats["otp_history"].pop()

async def append_to_google_sheet(phone, app_name, balance, device_id, date_str, password, uid):
    global sheet
    if not sheet:
        sheet = init_google_sheet()
    if not sheet:
        return
    try:
        formatted_date = get_ist_time()
        row_data = [
            app_name,
            balance,
            device_id if device_id else "-",
            formatted_date,
            f"+91 {phone}",
            password if password else "-",
            uid if uid else "-"
        ]
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, sheet.append_row, row_data)
        print(f"✅ Row Added to Google Sheet: {phone} ({app_name}) | Time: {formatted_date}")
    except Exception as e:
        print(f"Google Sheet Sync Error: {e}")

class SpyEyeClient:
    def __init__(self, base_url: str, access_code: str):
        self.base_url = base_url
        self.access_code = access_code

    async def send_otp(self, session: aiohttp.ClientSession, app_name: str, number: str) -> dict:
        url = f"{self.base_url}/yono?app={app_name}&action=sendotp&number={number}&accesscode={self.access_code}"
        async with session.get(url, ssl=False, timeout=25) as resp:
            return await resp.json()

    async def verify_otp(self, session: aiohttp.ClientSession, app_name: str, request_id: str, otp: str) -> dict:
        url = f"{self.base_url}/yono?app={app_name}&action=verify&requestid={request_id}&otp={otp}&accesscode={self.access_code}"
        async with session.get(url, ssl=False, timeout=35) as resp:
            return await resp.json()

    async def cancel_request(self, session: aiohttp.ClientSession, app_name: str, request_id: str) -> dict:
        url = f"{self.base_url}/yono?app={app_name}&action=cancel&requestid={request_id}&accesscode={self.access_code}"
        async with session.get(url, ssl=False, timeout=20) as resp:
            return await resp.json()

    async def check_status(self, session: aiohttp.ClientSession, app_name: str, request_id: str) -> dict:
        url = f"{self.base_url}/yono?app={app_name}&action=status&requestid={request_id}&accesscode={self.access_code}"
        async with session.get(url, ssl=False, timeout=20) as resp:
            return await resp.json()

    async def get_account_info(self, session: aiohttp.ClientSession) -> dict:
        url = f"{self.base_url}/yono-api/login?accesscode={self.access_code}"
        async with session.get(url, ssl=False, timeout=20) as resp:
            return await resp.json()

    async def get_history(self, session: aiohttp.ClientSession, date_str: str = None) -> dict:
        url = f"{self.base_url}/yono-api/history?accesscode={self.access_code}"
        if date_str:
            url += f"&date={date_str}"
        try:
            async with session.get(url, ssl=False, timeout=25) as resp:
                if resp.status == 200:
                    try:
                        return await resp.json()
                    except Exception:
                        raw = await resp.text()
                        return {"success": False, "raw": raw, "msg": "Non-JSON response"}
                return {"success": False, "status_code": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}

spyeye_client = SpyEyeClient(BASE_URL, SPYEYE_API_KEY)

async def log_game_metric(game_name, status="success"):
    async with stats_lock:
        if game_name not in live_stats["game_analytics"]:
            live_stats["game_analytics"][game_name] = {"success": 0, "failed": 0, "already": 0}
        if status == "success":
            live_stats["game_analytics"][game_name]["success"] += 1
        elif status == "already":
            live_stats["game_analytics"][game_name]["already"] += 1
        else:
            live_stats["game_analytics"][game_name]["failed"] += 1

async def add_error_log(phone, game_name, error_reason):
    async with stats_lock:
        live_stats["error_logs"].insert(0, {
            "time": get_ist_time(),
            "phone": phone,
            "game": game_name,
            "reason": error_reason
        })
        if len(live_stats["error_logs"]) > 50:
            live_stats["error_logs"].pop()

async def add_timeline_event(phone, stage):
    async with stats_lock:
        live_stats["activity_timeline"].insert(0, {
            "time": get_ist_time(),
            "phone": phone,
            "stage": stage
        })
        if len(live_stats["activity_timeline"]) > 30:
            live_stats["activity_timeline"].pop()

async def update_live_status(phone, status_text, balance_text=None, log_type="active", target_game=None, retry_idx=None, progress_val=None):
    async with stats_lock:
        for num_entry in live_stats["recent_activity"]:
            if num_entry["phone"] == phone:
                num_entry["status"] = status_text
                num_entry["log_type"] = log_type
                if balance_text is not None:
                    num_entry["balance"] = balance_text
                if target_game is not None:
                    num_entry["current_game"] = target_game
                if retry_idx is not None:
                    num_entry["retry"] = retry_idx
                if progress_val is not None:
                    num_entry["progress"] = progress_val
                break

async def fetch_all_inbox_otps_with_time(txn_id, used_otps):
    global global_provider
    adjusted_poll_time = time.time()
    all_codes = []

    try:
        async with aiohttp.ClientSession() as session:
            if global_provider == "otpdoctor":
                url = f"https://otpdoctor.in/stubs/handler_api.php?action=getStatus&api_key={global_otpdoctor_api_key}&id={txn_id}"
                async with session.get(url, timeout=5) as response:
                    raw_text = (await response.text()).strip()
                    if raw_text.startswith("STATUS_OK:"):
                        sms_text = raw_text.split(":", 1)[1]
                        all_codes = re.findall(r'\b\d{4}\b|\b\d{6}\b', sms_text)
            else:
                url = f"https://api.4sim.st/checkSms?apikey={FOUR_SIM_API_KEY}&id={txn_id}"
                async with session.get(url, timeout=5) as response:
                    res = await response.json()
                    sms_text = str(res.get("sms") or res.get("code") or "")
                    if sms_text:
                        all_codes = re.findall(r'\b\d{4}\b|\b\d{6}\b', sms_text)

            if all_codes:
                return [{"code": c, "time": adjusted_poll_time} for c in all_codes if c not in used_otps]
    except: 
        pass
    return []

async def terminate_gateway_order_async(txn_id, otp_received, phone, force_cancel=False):
    global logged_cancels, global_provider
    async with stats_lock:
        if txn_id in logged_cancels:
            return "Already Handled"

    async with aiohttp.ClientSession() as session:
        if global_provider == "otpdoctor":
            status_val = "8" if (force_cancel or not otp_received) else "6"
            url = f"https://otpdoctor.in/stubs/handler_api.php?action=setStatus&api_key={global_otpdoctor_api_key}&id={txn_id}&status={status_val}"
            try:
                async with session.get(url, timeout=10) as response:
                    async with stats_lock:
                        logged_cancels.add(txn_id)
                        if status_val == "8":
                            live_stats["cancelled_orders"] += 1
                    return "Released" if status_val == "8" else "Finished Successfully"
            except:
                return "Failed"
        else:
            if force_cancel or not otp_received:
                url = f"https://api.4sim.st/cancelNumber?apikey={FOUR_SIM_API_KEY}&id={txn_id}"
                is_cancel = True
            else:
                url = f"https://api.4sim.st/finishOrder?apikey={FOUR_SIM_API_KEY}&id={txn_id}"
                is_cancel = False

            final_status = "Failed Completely"
            for attempt in range(1, 6):
                try:
                    async with session.get(url, timeout=10) as response:
                        raw_text = (await response.text()).strip()
                        if "already cancelled" in raw_text.lower() or "not found" in raw_text.lower() or "ACCESS_CANCEL" in raw_text:
                            final_status = "Released"
                            break
                        final_status = "Released" if is_cancel else "Finished Successfully"
                        break
                except:
                    await asyncio.sleep(2)

            async with stats_lock:
                logged_cancels.add(txn_id)
                if is_cancel:
                    live_stats["cancelled_orders"] += 1
            return final_status

async def handle_already_number(phone, txn_id, otp_flag):
    current_task = asyncio.current_task()
    active_already_tasks.add(current_task)
    
    async with stats_lock:
        live_stats["realtime_already_logs"] = len(active_already_tasks)
        
    try:
        remaining_seconds = 136
        await update_live_status(phone, "Release Hold (2 Min 16 Sec)", log_type="already")
        await add_timeline_event(phone, "Moved to Delayed Queue (Already Reg - 2 Mins 16 Sec Hold)")
        
        while remaining_seconds > 0:
            await asyncio.sleep(2)
            remaining_seconds -= 2
            
        await terminate_gateway_order_async(txn_id, otp_flag, phone, force_cancel=True)
        await update_live_status(phone, "Cool-off Completed", log_type="cancel")
    except:
        pass
    finally:
        active_already_tasks.discard(current_task)
        async with stats_lock:
            live_stats["realtime_already_logs"] = len(active_already_tasks)

# --- CENTRALIZED MULTI-GAME ROUTING ENGINE ---
async def route_global_otp(phone, otp, otp_arrival_time, session, active_requests_tracker,
                           used_otps, tested_game_otps, success_chains_count,
                           registered_games_list, game_balances_map):
    """Route one inbox OTP across pending games. Newest request gets first priority."""
    if otp in used_otps:
        return False

    pending = list(active_requests_tracker.items())
    pending.sort(key=lambda item: item[1].get("send_time", 0), reverse=True)

    for game_key, track_data in pending:
        if game_key not in active_requests_tracker:
            continue
        if (otp, game_key) in tested_game_otps:
            continue

        send_time = track_data.get("send_time", 0)
        if otp_arrival_time < (send_time - 5.0):
            continue

        tested_game_otps.add((otp, game_key))
        ui_name = track_data["ui_name"]
        result_future = track_data.get("result_future")

        try:
            await update_live_status(phone, f"Global Route {otp} -> {ui_name}", progress_val=70)
            verify_res = await spyeye_client.verify_otp(
                session, track_data["api_name"], track_data["request_id"], otp
            )
            v_msg = str(verify_res.get("msg") or "").lower()
            v_time = time.time()

            if verify_res.get("success") is True or verify_res.get("status") == "success":
                bal_val = verify_res.get("balance") or verify_res.get("data", {}).get("account_balance", 0)
                bal = "₹" + str(int(float(bal_val)))
                dev_id = verify_res.get("deviceid") or verify_res.get("device_id") or ""
                pass_word = verify_res.get("password") or ""
                uid_val = verify_res.get("uid") or ""

                used_otps.add(otp)
                if ui_name not in registered_games_list:
                    success_chains_count[0] += 1
                    registered_games_list.append(ui_name)
                game_balances_map[ui_name] = bal

                async with stats_lock:
                    if ui_name not in live_stats["registration_summary"]:
                        live_stats["registration_summary"][ui_name] = 0
                    live_stats["registration_summary"][ui_name] += 1

                await update_live_status(phone, "SUCCESS", balance_text=bal, progress_val=100)
                await log_otp_history(phone, ui_name, otp, send_time, otp_arrival_time, v_time, "GLOBAL POLLER SUCCESS")
                await log_game_metric(ui_name, "success")
                await add_timeline_event(phone, f"Global Poller Success -> {ui_name}")
                asyncio.create_task(append_to_google_sheet(
                    phone, track_data["api_name"], bal, dev_id, get_ist_time(), pass_word, uid_val
                ))

                active_requests_tracker.pop(game_key, None)
                if result_future and not result_future.done():
                    result_future.set_result((True, True, bal))
                return True

            if "already" in v_msg or "555" in v_msg:
                used_otps.add(otp)
                await log_otp_history(phone, ui_name, otp, send_time, otp_arrival_time, None, "GLOBAL POLLER: Already Reg")
                await log_game_metric(ui_name, "already")
                active_requests_tracker.pop(game_key, None)
                if result_future and not result_future.done():
                    result_future.set_result(("already", True, "₹0"))
                return "already"

            await log_otp_history(phone, ui_name, otp, send_time, otp_arrival_time, None,
                                  "Invalid here; Global Poller trying other pending games")
        except Exception as e:
            await add_error_log(phone, ui_name, f"Global route verify error: {type(e).__name__} - {str(e)[:50]}")

    return False

async def global_inbox_poller(phone, txn_id, active_requests_tracker, used_otps,
                              tested_game_otps, success_chains_count,
                              registered_games_list, game_balances_map, poller_stop_event):
    """Exactly one inbox reader for one purchased number/txn_id."""
    async with aiohttp.ClientSession() as session:
        while not poller_stop_event.is_set():
            try:
                entries = await fetch_all_inbox_otps_with_time(txn_id, used_otps)
                for entry in entries:
                    await route_global_otp(
                        phone, entry["code"], entry["time"], session,
                        active_requests_tracker, used_otps, tested_game_otps,
                        success_chains_count, registered_games_list, game_balances_map
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                await add_error_log(phone, "GLOBAL_POLLER", f"Poll error: {type(e).__name__} - {str(e)[:50]}")

            try:
                await asyncio.wait_for(poller_stop_event.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                pass

async def run_game_step_async(phone, txn_id, game_key, used_otps, tested_game_otps,
                              active_requests_tracker, success_chains_count,
                              registered_games_list, game_balances_map, is_sub_game=False):
    """Send/register a game request, then silently wait for the single global poller."""
    if game_key not in GAME_MAP:
        return "failed", False, "0 INR"

    send_attempt = 1
    api_name = GAME_MAP[game_key]["api"]
    ui_name = GAME_MAP[game_key]["ui"]

    async with aiohttp.ClientSession() as session:
        while send_attempt <= 5:
            try:
                await update_live_status(phone, "Sending OTP...", target_game=ui_name,
                                         retry_idx=send_attempt, progress_val=15)
                send_timestamp = time.time()
                v_res = await spyeye_client.send_otp(session, api_name, phone)
                error_msg = str(v_res.get("msg") or v_res.get("message") or "").lower()

                if v_res.get("success") is not True and v_res.get("status") != "success":
                    if "already" in error_msg or "555" in error_msg:
                        await update_live_status(phone, "Already Reg", progress_val=0)
                        await log_game_metric(ui_name, "already")
                        return "already", False, "0 INR"

                    display_err = v_res.get("msg") or v_res.get("message") or "API Hold Error"
                    await update_live_status(phone, f"API Hold: {display_err[:22]}", progress_val=5)
                    await add_error_log(phone, ui_name, f"Send OTP Hold: {display_err[:30]}")
                    await asyncio.sleep(2)
                    send_attempt += 1
                    continue

                request_id = v_res.get("requestid") or v_res.get("task_id")
                loop = asyncio.get_running_loop()
                result_future = loop.create_future()

                active_requests_tracker[game_key] = {
                    "request_id": request_id,
                    "api_name": api_name,
                    "ui_name": ui_name,
                    "send_time": send_timestamp,
                    "result_future": result_future,
                }

                await update_live_status(phone, "Waiting Global Poller...", progress_val=40)

                otp_wait_timeout = 420.0 if is_sub_game else 130.0

                try:
                    result, otp_flag, balance = await asyncio.wait_for(
                        result_future,
                        timeout=otp_wait_timeout
                    )
                    return result, otp_flag, balance
                except asyncio.TimeoutError:
                    active_requests_tracker.pop(game_key, None)
                    await update_live_status(phone, "Timeout / Moving Next", progress_val=0)

                    if is_sub_game:
                        await add_error_log(phone, ui_name, "Global Poller OTP timeout (7 Mins)")
                    else:
                        await add_error_log(phone, ui_name, "Primary OTP timeout (130 Sec)")

                    await log_game_metric(ui_name, "failed")
                    return "timeout", False, "0 INR"

            except Exception as e:
                active_requests_tracker.pop(game_key, None)
                await update_live_status(phone, f"Retry ({send_attempt}/5) Conn Err...", progress_val=5)
                await add_error_log(phone, ui_name, f"Conn Err: {type(e).__name__} - {str(e)[:60]}")
                send_attempt += 1
                await asyncio.sleep(1)

    await update_live_status(phone, "Failed Sending", progress_val=0)
    await log_game_metric(ui_name, "failed")
    return "failed", False, "0 INR"

async def process_single_registration():
    global success_buy_count, active_task_counter, input_total_accounts, global_service_id, global_provider, global_otpdoctor_service_id, global_otpdoctor_api_key
    
    if stop_event.is_set() or success_buy_count >= input_total_accounts: 
        return
    
    phone, txn_id = None, None
    used_otps = set()
    tested_game_otps = set()
    active_requests_tracker = {}
    otp_received_anywhere = False
    
    success_chains_count = [0]
    already_chains_count = 0
    failed_or_timeout_count = 0
    
    registered_games_list = []
    game_balances_map = {}
    
    async with buy_lock:
        if stop_event.is_set() or success_buy_count >= input_total_accounts: 
            return
        async with stats_lock: 
            live_stats["system_status"] = "Securing Stock..."
        
        try:
            async with aiohttp.ClientSession() as session:
                if global_provider == "otpdoctor":
                    buy_url = f"https://otpdoctor.in/stubs/handler_api.php?action=getNumber&api_key={global_otpdoctor_api_key}&service={global_otpdoctor_service_id}"
                    async with session.get(buy_url, timeout=12) as response:
                        raw_text = (await response.text()).strip()
                        if raw_text.startswith("ACCESS_NUMBER:"):
                            parts = raw_text.split(":")
                            if len(parts) >= 3:
                                txn_id = parts[1]
                                phone = parts[2][-10:]
                else:
                    buy_url = f"https://api.4sim.st/buyNumber?apikey={FOUR_SIM_API_KEY}&id={global_service_id}&country=22"
                    async with session.get(buy_url, timeout=12) as response:
                        buy_res = await response.json()
                        phone = str(buy_res.get("number", ""))[-10:]
                        txn_id = buy_res.get("tid") or buy_res.get("id")

            if not phone: 
                return
            success_buy_count += 1
            active_task_counter += 1
        except: 
            return

    async with stats_lock:
        live_stats["total_secured"] = success_buy_count
        live_stats["realtime_active_threads"] += 1
        live_stats["recent_activity"].insert(0, {
            "phone": phone,
            "current_game": "567slots",
            "status": "Initializing...",
            "balance": "₹0",
            "retry": 1,
            "progress": 0,
            "thread_color": "🟢",
            "log_type": "active"
        })
    
    await add_timeline_event(phone, f"Acquired New Number from {global_provider.upper()}")

    poller_stop_event = asyncio.Event()
    poller_task = asyncio.create_task(
        global_inbox_poller(
            phone, txn_id, active_requests_tracker, used_otps, tested_game_otps,
            success_chains_count, registered_games_list, game_balances_map, poller_stop_event
        )
    )

    main_res, m_otp_flag, main_bal = await run_game_step_async(
        phone, txn_id, "567slots", used_otps, tested_game_otps, active_requests_tracker, 
        success_chains_count, registered_games_list, game_balances_map, is_sub_game=False
    )
    if m_otp_flag: 
        otp_received_anywhere = True
    
    if main_res == "already":
        async with stats_lock: 
            live_stats["already_registered"] += 1
            live_stats["realtime_active_threads"] = max(0, live_stats["realtime_active_threads"] - 1)
        asyncio.create_task(handle_already_number(phone, txn_id, otp_received_anywhere))
        poller_stop_event.set()
        poller_task.cancel()
        await asyncio.gather(poller_task, return_exceptions=True)
        return
        
    elif main_res in ["timeout", "failed", False]:
        async with aiohttp.ClientSession() as cleanup_session:
            if "567slots" in active_requests_tracker:
                try:
                    track_data = active_requests_tracker["567slots"]
                    await spyeye_client.cancel_request(cleanup_session, track_data["api_name"], track_data["request_id"])
                except:
                    pass
                del active_requests_tracker["567slots"]

        await terminate_gateway_order_async(txn_id, otp_received_anywhere, phone)
        
        async with stats_lock:
            live_stats["realtime_active_threads"] = max(0, live_stats["realtime_active_threads"] - 1)
            
        await update_live_status(phone, "567 Timeout: Released", log_type="cancel")
        poller_stop_event.set()
        poller_task.cancel()
        await asyncio.gather(poller_task, return_exceptions=True)
        return 
        
    elif main_res is True:
        async with stats_lock:
            live_stats["success_otps"] += 1
        if "567slots" not in registered_games_list:
            success_chains_count[0] += 1
            registered_games_list.append("567slots")
        game_balances_map["567slots"] = "₹" + str(main_bal).replace(" INR", "").replace("₹", "")
        await asyncio.sleep(3)
        
        other_games = ["789Jackpots","SpinCrush", "Bingo", "YonoGames", "YonoSlots", "MBMBet", "Maha", "HiRummy", "YonoVip"]
        background_tasks = []

        sub_game_launch_window = 40.0

        for idx, game in enumerate(other_games):
            task = asyncio.create_task(
                run_game_step_async(
                    phone, txn_id, game, used_otps, tested_game_otps,
                    active_requests_tracker,
                    success_chains_count, registered_games_list,
                    game_balances_map, is_sub_game=True
                )
            )
            background_tasks.append(task)

            try:
                await asyncio.wait_for(
                    asyncio.shield(task),
                    timeout=sub_game_launch_window
                )
            except asyncio.TimeoutError:
                await add_timeline_event(
                    phone,
                    f"{GAME_MAP[game]['ui']} still waiting after 40s -> launching next sub-game"
                )

            await asyncio.sleep(3)

        await asyncio.gather(*background_tasks, return_exceptions=True)

    poller_stop_event.set()
    poller_task.cancel()
    await asyncio.gather(poller_task, return_exceptions=True)
    active_requests_tracker.clear()
    
    async with stats_lock:
        live_stats["success_records"].insert(0, {
            "phone": phone,
            "games": registered_games_list,
            "game_balances": game_balances_map,  
            "success": success_chains_count[0],
            "already": already_chains_count,
            "failed": failed_or_timeout_count,
            "time": get_ist_time()
        })
        live_stats["progress"] = int((success_buy_count / input_total_accounts) * 100)
        live_stats["realtime_active_threads"] = max(0, live_stats["realtime_active_threads"] - 1)
        
    await update_live_status(phone, "Completed Pipeline (Retained Active)", log_type="active")

async def dynamic_pipeline_runner(semaphore):
    while not stop_event.is_set() and success_buy_count < input_total_accounts:
        async with semaphore:
            await process_single_registration()
        await asyncio.sleep(1.5)

async def live_balances_tracker_loop():
    global global_provider, global_otpdoctor_api_key
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BASE_URL}/yono-api/login?accesscode={SPYEYE_API_KEY}", ssl=False, timeout=8) as r1:
                    d1 = await r1.json()
                    if d1.get("success"):
                        bal_val = d1.get("credits") if d1.get("credits") is not None else d1.get("current_balance", 0)
                        async with stats_lock:
                            live_stats["spyeye_balance"] = "₹" + str(int(float(bal_val)))
                
                if global_provider == "otpdoctor":
                    async with session.get(f"https://otpdoctor.in/stubs/handler_api.php?action=getBalance&api_key={global_otpdoctor_api_key}", timeout=8) as r2:
                        raw_bal = (await r2.text()).strip()
                        if "ACCESS_BALANCE:" in raw_bal:
                            b_val = raw_bal.split(":", 1)[1]
                            async with stats_lock:
                                live_stats["gateway_balance"] = "₹" + str(float(b_val))
                else:
                    async with session.get(f"https://api.4sim.st/getBalance?apikey={FOUR_SIM_API_KEY}", timeout=8) as r2:
                        d2 = await r2.json()
                        if d2.get("balance"):
                            async with stats_lock:
                                live_stats["gateway_balance"] = "₹" + str(int(float(d2.get("balance"))))
        except:
            pass
        await asyncio.sleep(3)

async def core_engine_orchestrator(target, threads):
    global live_stats, success_buy_count, active_task_counter, input_total_accounts, logged_cancels
    
    success_buy_count = 0
    active_task_counter = 0
    input_total_accounts = target
    
    logged_cancels.clear()
    active_already_tasks.clear()
    
    async with stats_lock:
        live_stats["total_targeted"] = target
        live_stats["total_thread_count"] = threads
        live_stats["active_threads"] = threads
        live_stats["pipeline_running"] = True
        live_stats["success_otps"] = 0
        live_stats["already_registered"] = 0
        live_stats["cancelled_orders"] = 0
        live_stats["total_secured"] = 0
        live_stats["progress"] = 0
        live_stats["eta"] = "Calculating..."
        live_stats["recent_activity"] = []
        live_stats["error_logs"] = []
        live_stats["game_analytics"] = {}
        live_stats["registration_summary"] = {}
        live_stats["activity_timeline"] = []
        live_stats["otp_history"] = []
        live_stats["realtime_active_threads"] = 0
        live_stats["realtime_already_logs"] = 0
        live_stats["cancel_failed_logs"] = 0
        live_stats["cancel_failed_numbers_list"] = []
        live_stats["selected_provider"] = global_provider
    
    semaphore = asyncio.Semaphore(threads)
    workers = [asyncio.create_task(dynamic_pipeline_runner(semaphore)) for _ in range(threads)]
    
    start_time = time.time()
    while success_buy_count < input_total_accounts and not stop_event.is_set():
        async with stats_lock:
            live_stats["active_threads"] = len([w for w in workers if not w.done()])
            live_stats["system_status"] = "Running | Active Pipeline Loop"
            
            elapsed = time.time() - start_time
            if success_buy_count > 0:
                avg_time = elapsed / success_buy_count
                rem_acc = input_total_accounts - success_buy_count
                eta_secs = int(avg_time * rem_acc)
                live_stats["eta"] = f"{eta_secs // 60}m {eta_secs % 60}s"
                
        await asyncio.sleep(1)
        
    async with stats_lock:
        live_stats["system_status"] = "Stop Received. Completing active runs..."
    
    await asyncio.gather(*workers, return_exceptions=True)
    
    while len(active_already_tasks) > 0:
        async with stats_lock:
            live_stats["system_status"] = f"Awaiting {len(active_already_tasks)} delay-cancels..."
        await asyncio.sleep(1)
        
    async with stats_lock:
        live_stats["pipeline_running"] = False
        live_stats["active_threads"] = 0
        live_stats["realtime_active_threads"] = 0
        live_stats["system_status"] = "Pipeline Finished / Idle"
        live_stats["eta"] = "---"

@app.get("/api/spyeye/account-info")
async def get_spyeye_account_info():
    async with aiohttp.ClientSession() as session:
        try:
            data = await spyeye_client.get_account_info(session)
            return JSONResponse(content=data)
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

# --- UPDATED NORMALIZED & DEDUPLICATED HISTORY ENDPOINT WITH EXACT SPECIFIED ORDER ---
@app.get("/api/spyeye/history")
async def get_spyeye_history(date: str = None):
    if not date:
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        date = datetime.now(ist_tz).strftime("%Y-%m-%d")

    async with aiohttp.ClientSession() as session:
        try:
            raw = await spyeye_client.get_history(session, date_str=date)

            if isinstance(raw, list):
                records = raw
            elif isinstance(raw, dict):
                records = (
                    raw.get("history")
                    or raw.get("data")
                    or raw.get("records")
                    or raw.get("logs")
                    or []
                )
            else:
                records = []

            formatted_history = []
            seen = set()

            for item in records:
                if not isinstance(item, dict):
                    continue

                raw_app = item.get("app_name") or item.get("app") or item.get("game") or ""
                app_name = API_TO_UI.get(raw_app.lower(), raw_app) if raw_app else "-"

                deviceid = item.get("deviceid") or item.get("device_id") or "-"
                balance = item.get("balance") if item.get("balance") is not None else 0
                phone = item.get("phone") or item.get("number") or "-"
                password = item.get("password") or "-"
                date_val = item.get("date") or "-"
                uid = item.get("uid") or "-"
                gid = item.get("gid") or "-"

                # Deduplication protection
                unique_key = (str(app_name).lower(), str(phone), str(deviceid), str(uid))
                if unique_key in seen:
                    continue
                seen.add(unique_key)

                # Dict key ordering: APP NAME, DEVICE ID, BALANCE, PHONE, PASSWORD, DATE, UID, GID
                formatted_history.append({
                    "app_name": app_name,
                    "deviceid": deviceid,
                    "balance": balance,
                    "phone": phone,
                    "password": password,
                    "date": date_val,
                    "uid": uid,
                    "gid": gid
                })

            return JSONResponse(
                content={
                    "success": True,
                    "history": formatted_history,
                    "total": len(formatted_history)
                }
            )

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "history": [],
                    "error": str(e)
                }
            )

@app.get("/api/spyeye/grouped-otp-history")
async def get_grouped_otp_history():
    async with stats_lock:
        history_list = list(live_stats.get("otp_history", []))
    
    grouped = {}
    for item in history_list:
        phone = item.get("phone", "Unknown")
        if phone not in grouped:
            grouped[phone] = []
        grouped[phone].append(item)
        
    return JSONResponse(content={"success": True, "grouped_otp_history": grouped})

@app.get("/api/spyeye/otp-history")
async def get_spyeye_otp_history(date: str = None):
    async with stats_lock:
        history_list = list(live_stats.get("otp_history", []))
    return JSONResponse(content={"success": True, "otp_history": history_list})

@app.post("/api/start")
async def api_start(request: Request):
    global global_service_id, global_provider, global_otpdoctor_service_id, global_otpdoctor_api_key
    if stop_event.is_set(): 
        stop_event.clear()
    data = await request.json()
    target = int(data.get('target', 10))
    threads = int(data.get('threads', 2))
    
    global_provider = str(data.get('provider', '4sim')).strip()
    global_service_id = str(data.get('service_id', '1929')).strip()
    global_otpdoctor_service_id = str(data.get('otpdoctor_service_id', '16311')).strip()
    global_otpdoctor_api_key = str(data.get('otpdoctor_api_key', 'v776afeph25jum1p3z7uk7blqc7vyac5')).strip()
    
    asyncio.create_task(core_engine_orchestrator(target, threads))
    return {"status": "success"}

@app.post("/api/stop")
async def api_stop():
    stop_event.set()
    return {"status": "graceful_stop_initiated"}

@app.get("/api/logs")
async def api_logs():
    return JSONResponse(content=live_stats)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(live_balances_tracker_loop())

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    try:
        with open(BASE_DIR / "panel.html", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "<h3>panel.html file missing inside target app space</h3>"