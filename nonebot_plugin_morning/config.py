from nonebot import get_driver
from nonebot.log import logger
from pathlib import Path
from pydantic import BaseModel, Extra
from typing import Dict, Union
import json
from .utils import morning_json_update


class PluginConfig(BaseModel, extra=Extra.ignore):
    morning_path: Path = Path(__file__).parent / "resource"


driver = get_driver()
morning_config: PluginConfig = PluginConfig.parse_obj(driver.config.dict())


@driver.on_startup
async def _() -> None:
    if not morning_config.morning_path.exists():
        morning_config.morning_path.mkdir(parents=True, exist_ok=True)

    config_json_path: Path = morning_config.morning_path / "config.json"

    # Initial default config, global for all groups
    _config: Dict[str, Dict[str, Dict[str, Union[bool, int]]]] = {
        "morning": {
            "morning_intime": {
                "enable": True,
                "early_time": 6,
                "late_time": 12
            },
            "multi_get_up": {
                "enable": False,
                "interval": 6
            },
            "super_get_up": {
                "enable": False,
                "interval": 3
            }
        },
        "night": {
            "night_intime": {
                "enable": True,
                "early_time": 21,
                "late_time": 6
            },
            "good_sleep": {
                "enable": True,
                "interval": 6
            },
            "deep_sleep": {
                "enable": False,
                "interval": 3
            }
        }
    }

    if not config_json_path.exists():
        with open(config_json_path, 'w', encoding='utf-8') as f:
            json.dump(_config, f, ensure_ascii=False, indent=4)

        logger.info("Initialized the config.json of Morning plugin")
    else:
        # Overwrite the config.json up to v0.3.2
        with open(config_json_path, 'r', encoding='utf-8') as f:
            _c = json.load(f)
            if "default" not in _c:
                with open(config_json_path, 'w', encoding='utf-8') as f:
                    json.dump(_config, f, ensure_ascii=False, indent=4)

                logger.info(
                    "Overwrote the config.json of Morning plugin up to v0.3.2")

    # Old data.json will be transferred from v0.2.x into v0.3.x version automatically
    old_data_path: Path = morning_config.morning_path / "data.json"
    new_data_path: Path = morning_config.morning_path / "morning.json"

    if not new_data_path.exists():
        if old_data_path.exists():
            with open(old_data_path, 'r', encoding='utf-8') as f:
                _d: Dict[str, Dict[str, Dict[str, int]]] = json.load(f)
                _nfile = morning_json_update(_d)

                # Write into morning.json
                with open(new_data_path, 'w', encoding='utf-8') as f:
                    json.dump(_nfile, f, ensure_ascii=False, indent=4)

                logger.info("旧版数据文件已自动更新至新版，后续可关闭 OLD_MORNING_COMPATIBLE 选项！")

            old_data_path.unlink()

        else:
            with open(new_data_path, 'w', encoding='utf-8') as f:
                json.dump(dict(), f, ensure_ascii=False, indent=4)

            logger.warning(
                "旧版数据文件不存在，已自动创建新版数据文件。开启 OLD_MORNING_COMPATIBLE 选项可将旧版 data.json 数据文件自动更新。")
