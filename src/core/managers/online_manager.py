import requests
import threading
import time
from src.utils import Logger, GameSettings

POLL_INTERVAL = 0.02

class OnlineManager:
    list_players: list[dict]
    player_id: int
    
    _stop_event: threading.Event
    _thread: threading.Thread | None
    _lock: threading.Lock
    
    def __init__(self):
        self.base: str = GameSettings.ONLINE_SERVER_URL
        self.player_id = -1
        self.list_players = []

        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        Logger.info("OnlineManager initialized")
        
    def enter(self):
        self.register()
        self.start()
            
    def exit(self):
        self.stop()
        
    def get_list_players(self) -> list[dict]:
        with self._lock:
            return list(self.list_players)

    # ------------------------------------------------------------------
    # Threading and API Calling Below
    # ------------------------------------------------------------------
    def register(self):
        try:
            url = f"{self.base}/register"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if resp.status_code == 200:
                self.player_id = data["id"]
                Logger.info(f"OnlineManager registered with id={self.player_id}")
            else:
                Logger.error("Registration failed:", data)
        except Exception as e:
            Logger.warning(f"OnlineManager registration error: {e}")
        return

    def update(self, x: float, y: float, map_name: str, direction: str | None = None, sprite: str | None = None) -> bool:
        if self.player_id == -1:
            # Try to register again
            return False
        
        url = f"{self.base}/players"
        body = {"id": self.player_id, "x": x, "y": y, "map": map_name}
        if direction:
            body["dir"] = direction
        if sprite:
            body["sprite"] = sprite
        try:
            resp = requests.post(url, json=body, timeout=5)
            if resp.status_code == 200:
                return True
            Logger.warning(f"Update failed: {resp.status_code} {resp.text}")
        except Exception as e:
            Logger.warning(f"Online update error: {e}")
        return False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="OnlineManagerPoller",
            daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop_event.wait(POLL_INTERVAL):
            self._fetch_players()
            
    def _fetch_players(self) -> None:
        try:
            url = f"{self.base}/players"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            all_players = resp.json().get("players", [])

            pid = self.player_id
            filtered = []
            for key, p in all_players.items():
                if int(key) == pid:
                    continue
                p["id"] = int(key)
                filtered.append(p)
            with self._lock:
                self.list_players = filtered
            
        except Exception as e:
            Logger.warning(f"OnlineManager fetch error: {e}")

    def send_message(self, text: str) -> bool:
        """Send a chat message to the server."""
        if self.player_id == -1:
            return False
        
        url = f"{self.base}/chat"
        body = {"id": self.player_id, "text": text}
        try:
            resp = requests.post(url, json=body, timeout=5)
            if resp.status_code == 200:
                return True
            Logger.warning(f"Send message failed: {resp.status_code} {resp.text}")
        except Exception as e:
            Logger.warning(f"Send message error: {e}")
        return False

    def get_recent_chat(self, limit: int = 50) -> list[dict]:
        """Get recent chat messages from the server."""
        try:
            url = f"{self.base}/chat"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            messages = data.get("messages", [])
            return messages[-limit:] if len(messages) > limit else messages
        except Exception as e:
            Logger.warning(f"Get chat error: {e}")
            return []