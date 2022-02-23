import requests
from pathlib import Path
try:
    import ujson as json
except ModuleNotFoundError:
    import json

class DownloadError(Exception):
    pass

def get_preset_config(file_path: Path) -> None:
    url = f"https://cdn.jsdelivr.net/gh/KafCoppelia/nonebot_plugin_morning@alpha.16/nonebot_plugin_morning/resource/config.json"
    data = requests.get(url).json()
    if data:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(dict()))
            f.close()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    if not file_path.exists():
        raise DownloadError