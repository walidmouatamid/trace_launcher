import os
import sys
import platform
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from colorama import init, Fore, Style
from pyperclip import copy

if platform.system() == "Windows":
    import ctypes
    import msvcrt

# ====== Constants ======
init(autoreset=True)
MAX_WAIT = 100
HOME_URL = "https://sso.tealiumiq.com/login/sso/"
SELENIUM_PROFILE_DIR = os.path.expanduser("~/selenium-profile")
LOCK_FILE_PATH = os.path.join(SELENIUM_PROFILE_DIR, "SingletonLock")
DRIVER_PATH_FILE = os.path.expanduser("~/.chromedriver_path_cache.txt")

# ====== UI Helpers ======
def escape_applescript_string(s):
    return s.replace('"', '\\"')

def show_alert(title, message, info=False):
    system = platform.system()

    if system == "Windows":
        icon_type = 0x40 if info else 0x10
        MB_OK = 0x0
        ctypes.windll.user32.MessageBoxW(0, message, title, icon_type | MB_OK)

    elif system == "Darwin":
        icon = "note" if info else "stop"
        safe_title = escape_applescript_string(title)
        safe_message = escape_applescript_string(message)
        subprocess.run([
            "osascript", "-e",
            f'display dialog "{safe_message}" with title "{safe_title}" buttons ["OK"] default button "OK" with icon {icon}'
        ])

    else:
        print(f"[{title}] {message}")

# ====== Profile Lock Check ======
def is_profile_in_use(lock_path):
    system = platform.system()
    if system == "Windows":
        try:
            if os.path.exists(lock_path):
                with open(lock_path, 'r+') as f:
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    return False
            return False
        except OSError:
            return True
    elif system == "Darwin":
        try:
            user_data_dir = os.path.dirname(lock_path)
            result = subprocess.run(
                f'ps aux | grep "[C]hrome" | grep -- "--user-data-dir={user_data_dir}"',
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            return result.returncode == 0
        except Exception as e:
            print(Fore.YELLOW + f"⚠️  MacOS profile check failed: {e}")
            return False
    return False

# ====== Selenium Helpers ======
def wait_for_visible(driver, xpath, timeout=MAX_WAIT):
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, xpath)))

def safe_js_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    driver.execute_script("arguments[0].click();", element)

def click_element(driver, xpath, js_click=True):
    el = wait_for_visible(driver, xpath)
    safe_js_click(driver, el) if js_click else el.click()
    return el

def switch_to_new_tab(driver, original_handle, timeout=MAX_WAIT):
    WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) > 1)
    for handle in driver.window_handles:
        if handle != original_handle:
            driver.switch_to.window(handle)
            return handle

# ====== Helper to get ChromeDriver path once and cache it ======
def get_chromedriver_path():
    if os.path.exists(DRIVER_PATH_FILE):
        with open(DRIVER_PATH_FILE, "r") as f:
            path = f.read().strip()
            if os.path.exists(path):
                print(f"Using cached ChromeDriver at {path}")
                return path
            else:
                print("Cached ChromeDriver path not found, reinstalling...")

    print("Downloading ChromeDriver...")
    path = ChromeDriverManager().install()
    with open(DRIVER_PATH_FILE, "w") as f:
        f.write(path)
    print(f"ChromeDriver installed and cached at {path}")
    return path

# ====== Main Script ======
if is_profile_in_use(LOCK_FILE_PATH):
    show_alert("Profile Already In Use", "A Chrome instance using this Selenium profile is currently running.")
    sys.exit(1)

try:
    driver_path = get_chromedriver_path()
    service = ChromeService(driver_path)

    options = Options()
    options.add_argument(f"--user-data-dir={SELENIUM_PROFILE_DIR}")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()

    driver.get(HOME_URL)
    wait_for_visible(driver, '//*[@id="account"]').send_keys('e-voyageurs-sncf')
    click_element(driver, '//*[@id="submitBtn"]')
    original_tab = driver.current_window_handle

    event_stream_tab = wait_for_visible(driver, '//*[@id="nav_section_event_stream"]')
    safe_js_click(driver, event_stream_tab)
    
    switch_to_new_tab(driver, original_tab)

    click_element(driver, '//*[@id="collapsibleTrace"]', js_click=False)
    click_element(driver, '//*[@data-testid="trace_start_button"]')

    trace_id_container = wait_for_visible(driver, "//div[starts-with(@class, 'StartTraceView__TraceId-sc')]")
    trace_id = trace_id_container.text.strip()
    url = f"https://master.test-sncf-connect.com/home?trace_id={trace_id}"

    print(Fore.GREEN + "*" * 87, flush=True)
    print(Fore.GREEN + f"*  Trace ID ===> {Style.BRIGHT}{trace_id}", flush=True)
    print(Fore.GREEN + f"*  Link     ===> {Style.BRIGHT}{url}", flush=True)
    print(Fore.GREEN + "*" * 87, flush=True)

    copy(trace_id)

    click_element(driver, "//button[starts-with(@class, 'Button__MultiButton-tealium-ui-kit__sc')]")
    input("✅ Script complete. Press Enter to exit...")

except TimeoutException as e:
    print(Fore.CYAN + "Timeout waiting for an element: ", str(e), flush=True)
except Exception as e:
    print(Fore.CYAN + "Unexpected error", str(e), flush=True)
except KeyboardInterrupt:
    print(Fore.CYAN + "\n🛑 Script interrupted by user.", flush=True)