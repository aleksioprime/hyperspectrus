import subprocess
import time
import json
from pathlib import Path

STATE_FILE = Path.home() / ".hotspot_state.json"

class NetworkState:
    """Сохраняет состояние сети перед включением точки доступа."""
    def __init__(self):
        self.dhcpcd_active = self._is_service_active("dhcpcd")
        self.nm_active = self._is_service_active("NetworkManager")
        self.ssid = self._get_current_ssid()

    def _is_service_active(self, service):
        return subprocess.run(["systemctl", "is-active", "--quiet", service]).returncode == 0

    def _get_current_ssid(self):
        try:
            return subprocess.check_output(["iwgetid", "-r"], encoding="utf-8").strip() or None
        except Exception:
            return None

    def to_dict(self):
        return {
            "dhcpcd_active": self.dhcpcd_active,
            "nm_active": self.nm_active,
            "ssid": self.ssid
        }

    def save_to_file(self):
        try:
            STATE_FILE.write_text(json.dumps(self.to_dict()))
        except Exception as e:
            print(f"Ошибка сохранения состояния сети: {e}")

    @staticmethod
    def from_file():
        if not STATE_FILE.exists():
            return None
        try:
            data = json.loads(STATE_FILE.read_text())
            ns = NetworkState.__new__(NetworkState)
            ns.dhcpcd_active = data.get("dhcpcd_active", True)
            ns.nm_active = data.get("nm_active", True)
            ns.ssid = data.get("ssid")
            return ns
        except Exception as e:
            print(f"Ошибка чтения состояния сети: {e}")
            return None

    def restore(self):
        """Восстанавливает предыдущую сетевую конфигурацию."""
        print("→ Восстанавливаю сеть...")
        if not self.nm_active:
            subprocess.run(["systemctl", "stop", "NetworkManager"], check=False)

        if self.dhcpcd_active:
            subprocess.run(["systemctl", "start", "dhcpcd"], check=False)
            time.sleep(2)

        if self.ssid:
            subprocess.run(["wpa_cli", "-i", "wlan0", "reconfigure"], check=False)

        if STATE_FILE.exists():
            STATE_FILE.unlink()
        print("→ Сеть восстановлена.")

def ensure_network_manager():
    """Запускает NetworkManager, если не запущен."""
    if subprocess.run(["systemctl", "is-active", "--quiet", "NetworkManager"]).returncode != 0:
        subprocess.run(["systemctl", "start", "NetworkManager"], check=False)
        time.sleep(2)

def is_hotspot_active():
    """Проверяет, активна ли точка доступа."""
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME", "connection", "show", "--active"],
        stdout=subprocess.PIPE, encoding="utf-8"
    )
    return "pi-hotspot" in result.stdout

def enable_hotspot(ssid="hyperspectrus", password="hyperspectrus1"):
    """Включает точку доступа, возвращает (успех, state)."""
    state = NetworkState()
    state.save_to_file()

    if state.dhcpcd_active:
        subprocess.run(["systemctl", "stop", "dhcpcd"], check=False)
        time.sleep(1)

    ensure_network_manager()

    try:
        subprocess.run([
            "nmcli", "device", "wifi", "hotspot",
            "ifname", "wlan0",
            "con-name", "pi-hotspot",
            "ssid", ssid,
            "password", password
        ], check=True)
        print("→ Точка доступа включена.")
        return True, state
    except subprocess.CalledProcessError as e:
        print(f"Ошибка включения точки доступа: {e}")
        state.restore()
        return False, state

def disable_hotspot(state=None):
    """Отключает точку доступа и восстанавливает предыдущее состояние сети."""
    if is_hotspot_active():
        subprocess.run(["nmcli", "connection", "down", "pi-hotspot"], check=False)
        print("→ Точка доступа отключена.")
    else:
        print("→ Точка уже отключена.")

    if not state:
        state = NetworkState.from_file()

    if isinstance(state, NetworkState):
        state.restore()
        return True

    print("Завершение: состояние не восстановлено (нет сохранённого состояния).")
    return False
