"""First-run welcome tasks: they explain the app by being tasks the user can tick off."""
import os
from datetime import date

from todo import service


def seed_welcome(path: str) -> bool:
    """Create the welcome tasks when there is no data file yet; returns True if it did."""
    if os.path.exists(path):
        return False
    today = date.today().isoformat()
    first = service.create(path, "Hoş geldin! Dairesine tıkla, görev tamamlansın", "high", today)
    service.update(path, first.id, {"pinned": True})
    service.create(path, "Yaz ve Enter: “rapor cuma !yüksek #iş” ya da “spor her gün”",
                   "medium", today, ["ipucu"])
    detail = service.create(path, "Göreve tıkla: not, alt görevler, tarih, tekrar ve takvim burada",
                            "medium", None, ["ipucu"])
    service.update(path, detail.id, {
        "note": "Detay sayfasında her şey otomatik kaydedilir.",
        "subtasks": [{"text": "Bir alt görev işaretle", "done": False},
                     {"text": "Takvim ya da Gmail seçeneğine bak", "done": False}]})
    service.create(path, "Sekmeyi sürükle: ekranın sağına, soluna, üstüne ya da altına yapışır",
                   "low", None, ["ipucu"])
    service.create(path, "Başka bir programdayken Ctrl+Alt+N: anında görev ekle", "low", None,
                   ["ipucu"])
    return True
