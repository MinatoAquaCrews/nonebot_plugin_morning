from pathlib import Path
from pydantic import BaseModel, Extra
from typing import Optional
from nonebot import get_driver, logger
import httpx
try:
    import ujson as json
except ModuleNotFoundError:
    import json

class PluginConfig(BaseModel, extra=Extra.ignore):
    morning_path: Path = Path(__file__).parent / "resource"
    
mor_switcher = {
    "时限": "get_up_intime",
    "多重起床": "multi_get_up",
    "超级亢奋": "super_get_up"
}

nig_switcher = {
    "时限": "sleep_intime",
    "优质睡眠": "good_sleep",
    "深度睡眠": "deep_sleep"
}
    
driver = get_driver()
morning_config: PluginConfig = PluginConfig.parse_obj(driver.config.dict())

class DownloadError(Exception):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return self.msg
    
async def download_url(url: str) -> Optional[httpx.Response]:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue
                return response
            except Exception:
                logger.warning(f"Error occured when downloading {url}, retry: {i+1}/3")
    
    logger.warning("Abort downloading")
        
@driver.on_startup
async def _() -> None:
    if not morning_config.morning_path.exists():
        morning_config.morning_path.mkdir(parents=True, exist_ok=True)
    
    config_json_path: Path = morning_config.morning_path / "config.json"
    if not config_json_path.exists():
        url = "https://raw.fastgit.org/MinatoAquaCrews/nonebot_plugin_morning/beta/nonebot_plugin_morning/resource/config.json"
        
        resp = await download_url(url)
        if resp is None:
            if not config_json_path.exists():
                raise DownloadError("Morning configuration file missing! Please check!")
            
        with open(config_json_path, 'w', encoding='utf-8') as f:
            json.dump(resp.json(), f, ensure_ascii=False, indent=4)
        
        logger.info(f"Got the config.json of Morning from repo")
    
    data_json_path: Path = morning_config.morning_path / "morning.json"
    if not data_json_path.exists():
        with open(data_json_path, 'w', encoding='utf-8') as f:
            json.dump(dict(), f, ensure_ascii=False, indent=4)