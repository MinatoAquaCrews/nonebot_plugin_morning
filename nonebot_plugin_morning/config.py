from pathlib import Path
from pydantic import BaseModel, Extra
from typing import Any
import httpx
from nonebot import get_driver
from nonebot import logger
from enum import Enum
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

class Op_Type(Enum):
    TURN_ON = "开启"
    TURN_OFF = "关闭"
    SETTING = "设置"

class Param_Type(Enum):
    TIME_LIMIT = "时限"
    MULTI_GET_UP = "多重起床"
    SUPER_GET_UP = "超级亢奋"
    GOOD_SLEEP = "优质睡眠"
    DEEP_SLEEP = "深度睡眠"
    
driver = get_driver()
morning_config: PluginConfig = PluginConfig.parse_obj(driver.config.dict())

class DownloadError(Exception):
    pass
    
async def download_url(url: str) -> Any:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue
                return response.json()
            except Exception as e:
                logger.warning(f"Error occured when downloading {url}, {i+1}/3: {e}")
    
    raise DownloadError
        
@driver.on_startup
async def _() -> None:
    if not morning_config.morning_path.exists():
        morning_config.what2eat_path.mkdir(parents=True, exist_ok=True)
    
    config_json_path: Path = morning_config.what2eat_path / "config.json"
    if not config_json_path.exists():
        url = "https://raw.fastgit.org/MinatoAquaCrews/nonebot_plugin_morning/beta/nonebot_plugin_morning/resource/config.json"
        
        resp = await download_url(url)
        if resp:
            with open(config_json_path, 'w', encoding='utf-8') as f:
                json.dump(resp, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Get file config.json from repo")
    
    data_json_path: Path = morning_config.what2eat_path / "morning.json"
    if not data_json_path.exists():
        with open(data_json_path, 'w', encoding='utf-8') as f:
            json.dump(dict(), f, ensure_ascii=False, indent=4)