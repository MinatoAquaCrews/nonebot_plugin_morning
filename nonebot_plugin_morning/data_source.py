from calendar import MONDAY
from nonebot import require
from nonebot.adapters.onebot.v11 import MessageSegment
from typing import Union, List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, time
import random
from .config import *
from .utils import *
    
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from apscheduler.jobstores.base import JobLookupError

class MorningManager:
    def __init__(self):
        self._morning: Dict[str, Dict[str, Dict[str, Dict[str, Union[str, int, datetime, List[int]]]]]] = dict()
        self._morning_path: Path = morning_config.morning_path / "morning.json"
        
        self._config: Dict[str, Dict[str, Dict[str, Union[bool, int]]]] = dict()
        self._config_path: Path = morning_config.morning_path / "config.json"

    def _init_group_data(self, gid: str) -> None:
        '''
            Initialize group data.
        '''
        self._load_data()
        if gid not in self._morning:
            self._morning.update({
                gid: {
                    "group_count": {
                        "daily": {
                            "good_morning": 0,  # Daily good-morning count of groups, REFRESH at the late time of good-morning everyday
                            "good_night": 0     # Daily good-night count of groups, REFRESH at the late time of good-night everyday
                        },
                        "weekly": {
                            "sleeping_king": "" # Sleeping king of group of last week, REFRESH at the late time of good-morning every Monday
                        }
                    }
                }
            })
            
            self._save_data()

    def get_current_config(self) -> MessageSegment:
        '''
            Return the current configurations.
        '''
        msg: str = "早安晚安设置如下："
        self._load_config()
        
        # Morning config
        morning_intime: bool = self._config["morning"]["morning_intime"]["enable"]
        if morning_intime:
            msg += "\n是否要求规定时间内起床：是\n - 最早允许起床时间：" + str(self._config["morning"]['morning_intime']["early_time"]) + "点\n - 最晚允许起床时间：" + str(self._config["morning"]["morning_intime"]["late_time"]) + "点"
        else:
            msg += "\n是否要求规定时间内起床：否"
            
        multi_get_up: bool = self._config["morning"]["multi_get_up"]["enable"]
        if multi_get_up:
            msg += "\n是否允许连续多次起床：是"
        else:
            msg += "\n是否允许连续多次起床：否\n - 允许的最短起床间隔：" + str(self._config["morning"]["multi_get_up"]["interval"]) + "小时"
        
        super_get_up: bool = self._config["morning"]["super_get_up"]["enable"]
        if super_get_up:
            msg += "\n是否允许超级亢奋(即睡眠时长很短)：是"
        else:
            msg += "\n是否允许超级亢奋(即睡眠时长很短)：否\n - 允许的最短睡觉时长：" + str(self._config["morning"]["super_get_up"]["interval"]) + "小时"
        
        # Night config
        night_intime: bool = self._config["night"]["night_intime"]["enable"]
        if night_intime:
            msg += "\n是否要求规定时间内睡觉：是\n - 最早允许睡觉时间：" + str(self._config["night"]["night_intime"]["early_time"]) + \
                "点\n - 最晚允许睡觉时间：第二天早上" + str(self._config["night"]["night_intime"]["late_time"]) + "点"
        else:
            msg += "\n是否要求规定时间内睡觉：否"
        
        good_sleep: bool = self._config["night"]["good_sleep"]["enable"]
        if good_sleep:
            msg += "\n是否开启优质睡眠：是"
        else:
            msg += "\n是否开启优质睡眠：否\n - 允许的最短优质睡眠：" + str(self._config["night"]["good_sleep"]["interval"]) + "小时"
        
        deep_sleep: bool = self._config["night"]["deep_sleep"]["enable"]
        if deep_sleep:
            msg += "\n是否允许深度睡眠(即清醒时长很短)：是"
        else:
            msg += "\n是否允许深度睡眠(即清醒时长很短)：否\n - 允许的最短清醒时长：" + str(self._config["night"]["deep_sleep"]["interval"]) + "小时"
        
        return MessageSegment.text(msg)

    # ------------------------------ Config ------------------------------ #
    def _change_enable(self, day_or_night: str, _setting: str, new_state: bool) -> str:
        '''
            Change and save the new state of a setting.
        '''
        self._load_config()
        self._config[day_or_night][_setting]["enable"] = new_state
        self._save_config()

        return "配置更新成功！"

    def _change_set_time(self, _day_or_night: str, _setting: str, _interval_or_early_time: int, _late_time: Optional[int] = None) -> str:
        '''
            Change the interval of a setting.
        '''
        self._load_config()
        
        if _setting == "morning_intime" or _setting == "night_intime":
            early_time: int = _interval_or_early_time
            if isinstance(_late_time, int):
                late_time: int = _late_time
            else:
                return "配置更新失败：缺少参数！"
            
            self._config[_day_or_night][_setting]["early_time"] = early_time
            self._config[_day_or_night][_setting]["late_time"] = late_time
        else:
            interval: int = _interval_or_early_time
            self._config[_day_or_night][_setting]["interval"] = interval
        
        msg: str = "配置更新成功！"
        
        # Some settings are True in default
        if _setting == "morning_intime" or _setting == "night_intime" or _setting == "good_sleep" \
            and self._config[_day_or_night][_setting]["enable"] == False:
            self._config[_day_or_night][_setting]["enable"] = True
            msg += "且此项设置已启用！"
        
        # Some settings are False in default
        if _setting == "multi_get_up" or _setting == "super_get_up" or _setting == "deep_sleep" \
            and self._config[_day_or_night][_setting]["enable"] == True:
            self._config[_day_or_night][_setting]["enable"] = False
            msg += "且此项设置已禁用！"
        
        self._save_config()
            
        return msg
        
    def daily_refresh(self) -> None:
        '''
            Reset good-morning/night count of groups of yesterday at the earliest time of daily good-night.
        '''
        self._load_data()
        
        for gid in self._morning:
            self._morning[gid]["group_count"]["daily"]["good_morning"] = 0
            self._morning[gid]["group_count"]["daily"]["good_night"] = 0
        
        self._save_data()
        logger.info("每日早晚安已刷新！")
        
    def weekly_night_refresh(self) -> None:
        '''
            1. Refresh good-night count of last week at 0 A.M. every Monday.
            2. Reset weekly good-night count at 0 A.M. every Monday.
        '''
        self._load_data()
        
        for gid in self._morning:
            for uid, user_items in self._morning[gid].items():
                user_items["weekly"]["lastweek_night_count"] = user_items["weekly"]["weekly_night_count"]
                user_items["weekly"]["weekly_night_count"] = 0
                
        self._save_data()
        
    def weekly_sleep_time_refresh(self) -> None:
        '''
            1. Refresh sleeping time & good-morning count of last week.
            2. Refresh the sleeping king UID of each groups.
            3. Reset weekly sleeping time & good-morning count.
        '''
        self._load_data()
        
        for gid in self._morning:
            _max_sleep_time: List[int] = [0, 0, 0, 0]
            _sleeping_king_uid: str = ""
            
            for uid, user_items in self._morning[gid].items():
                user_items["weekly"]["lastweek_morning_count"] = user_items["weekly"]["weekly_morning_count"]
                user_items["weekly"]["lastweek_sleep"] = user_items["weekly"]["weekly_sleep"]
                
                user_items["weekly"]["weekly_morning_count"] = 0
                user_items["weekly"]["weekly_sleep"] = [0, 0, 0, 0]
                
                # Compare two lists, day > hrs > mins / secs
                if user_items["weekly"]["lastweek_sleep"] > _max_sleep_time:
                    _max_sleep_time = user_items["weekly"]["lastweek_sleep"]
                    _sleeping_king_uid = uid
                    
            self._morning[gid]["group_count"]["weekly"]["sleeping_king"] = _sleeping_king_uid
                
        self._save_data()
        logger.info("每周睡眠时间、每周早安已刷新！")

    def morning_config(self, _mor_setting: str, *args: List[int]) -> MessageSegment:
        '''
            Configurations about morning.
        '''
        _setting: str = mor_switcher[_mor_setting]
        if _setting == "morning_intime":
            early_time: int = args[0]
            late_time: int = args[1]
            
            if early_time < 0 or early_time > 24 or late_time < 0 or late_time > 24:
                msg = "错误！您设置的时间未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("morning", _setting, early_time, late_time)
            
                # Change the data of daily good-morning/night scheduler and weekly sleeping time scheduler
                self.daily_scheduler(early_time)
                self.weekly_sleep_time_scheduler(late_time)
        else:
            interval: int = args[0]
            
            if interval < 0 or interval > 24:
                msg = "错误！您设置的时间间隔未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("morning", _setting, interval)
        
        return MessageSegment.text(msg)

    def morning_switch(self, _mor_setting: str, new_state: bool) -> MessageSegment:
        '''
            Enable/Disable of morning settings.
        '''
        _setting: str = mor_switcher[_mor_setting]
        msg: str = self._change_enable("morning", _setting, new_state)
        
        # Change the status of daily good-morning/night schedulers and weekly sleeping time scheduler
        if _setting == "morning_intime":
            # Remove the schedulers
            if not new_state:
                try:
                    scheduler.remove_job("weekly_sleep_time_scheduler")
                    logger.info(f"每周睡眠时间定时刷新任务已关闭！")
                    
                except JobLookupError as e:
                    logger.warning(f"每周睡眠时间定时刷新任务移除失败: {e}")
                    msg += "\n每周睡眠时间定时刷新任务移除失败"
                
                try:
                    scheduler.remove_job("daily_scheduler")
                    logger.info(f"每日早晚安定时刷新任务已关闭！")
                    
                except JobLookupError as e:
                    logger.warning(f"每日早晚安定时刷新任务移除失败: {e}")
                    msg += "\n每日早晚安定时刷新任务移除失败"
            
            # Add the schedulers if they don't exist
            else:
                if not scheduler.get_job("weekly_sleep_time_scheduler"):
                    self.weekly_sleep_time_scheduler()
                    logger.info("每周睡眠时间定时刷新任务已启动！")
                
                if not scheduler.get_job("daily_scheduler"):      
                    self.daily_scheduler()
                    logger.info("每日早晚安定时刷新任务已启动！")
        
        return MessageSegment.text(msg)

    def night_config(self, _nig_setting: str, *args: List[int]) -> MessageSegment:
        '''
            Configurations about night.
        '''
        _setting: str = nig_switcher[_nig_setting]
        if _setting == "night_intime":
            early_time: int = args[0]
            late_time: int = args[1]
            
            if early_time < 0 or early_time > 24 or late_time < 0 or late_time > 24:
                msg = "错误！您设置的时间未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("night", _setting, early_time, late_time)
        else:
            interval: int = args[0]
            
            if interval < 0 or interval > 24:
                msg = "错误！您设置的时间间隔未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("night", _setting, interval, None)
        
        return MessageSegment.text(msg)

    def night_switch(self, _nig_setting: str, new_state: bool) -> MessageSegment:
        '''
            Enable/Disable of night settings.
        '''
        _setting: str = nig_switcher[_nig_setting]
        msg: str = self._change_enable("night", _setting, new_state)
        
        return MessageSegment.text(msg)

    # ------------------------------ Morning Judgement ------------------------------ #
    def _morning_and_update(self, gid: str, uid: str, now_time: datetime) -> Tuple[str, Union[str, int]]:
        '''
            Morning & update data.
        '''
        self._load_data()
        
        # 起床并写数据
        sleep_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["night_time"], "%Y-%m-%d %H:%M:%S")
        in_sleep: timedelta = now_time - sleep_time
        days, hours, minutes, seconds = total_seconds2tuple_time(int(in_sleep.total_seconds()))
        
        # 睡觉时间小于24小时就同时给出睡眠时长，记录；否则隔日
        in_sleep_tmp: str = ""
        
        if in_sleep.days > 0:
            in_sleep_tmp = ""
        else:
            in_sleep_tmp = f"{hours}时{minutes}分{seconds}秒"
            self._morning[gid][uid]["weekly"]["weekly_sleep"] = sleeptime_update(self._morning[gid][uid]["weekly"]["weekly_sleep"], in_sleep)
            self._morning[gid][uid]["total"]["total_sleep"] = sleeptime_update(self._morning[gid][uid]["total"]["total_sleep"], in_sleep)

        # Daily morning time
        self._morning[gid][uid]["daily"]["morning_time"] = now_time
        # Weekly morning count add
        self._morning[gid][uid]["weekly"]["weekly_morning_count"] += 1
        # Total morning count add
        self._morning[gid][uid]["total"]["morning_count"] += 1
        
        lastweek_emt: Union[int, str] = self._morning[gid][uid]["weekly"]["lastweek_earliest_morning_time"]
        
        # If it is integer, it means no data
        if isinstance(lastweek_emt, int):
            self._morning[gid][uid]["weekly"]["lastweek_earliest_morning_time"] = now_time
        else:
            # If weekly morning time is later than daily's, update
            if not is_later(self._morning[gid][uid]["daily"]["morning_time"], self._morning[gid][uid]["weekly"]["lastweek_earliest_morning_time"]):
                self._morning[gid][uid]["weekly"]["lastweek_earliest_morning_time"] = now_time
        
        # 判断是今天第几个起床的
        self._morning[gid]["group_count"]["daily"]["good_morning"] += 1
        
        self._save_data()

        return self._morning[gid]["group_count"]["daily"]["good_morning"], in_sleep_tmp if in_sleep_tmp != "" else 0

    def get_morning_msg(self, gid: str, uid: str, sex_str: str) -> MessageSegment:
        '''
            Return good-morning info.
        '''
        self._load_config()
        
        # 若开启规定时间早安，则判断该时间是否允许早安
        now_time: datetime = datetime.now()
        if self._config["morning"]["morning_intime"]["enable"]:
            _early_time: int = self._config["morning"]["morning_intime"]["early_time"]
            _late_time: int = self._config["morning"]["morning_intime"]["late_time"]
            
            if not is_MorTimeinRange(_early_time, _late_time, now_time):
                msg = f"现在不能早安哦，可以早安的时间为{_early_time}时到{_late_time}时~"
                return MessageSegment.text(msg)

        self._init_group_data(gid)
        
        # 当数据里有过这个人的信息
        if uid in self._morning[gid]:
            # 判断是否隔日
            last_sleep_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["night_time"], "%Y-%m-%d %H:%M:%S")
            if last_sleep_time - now_time < timedelta(hours=24):
            
                # 若关闭连续多次早安，则判断在设定时间内是否多次早安
                if not self._config["morning"]["multi_get_up"]["enable"] and self._morning[gid][uid]["daily"]["morning_time"] != 0:
                    interval: int = self._config["morning"]["multi_get_up"]["interval"]
                    morning_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["morning_time"], "%Y-%m-%d %H:%M:%S")
                    
                    if now_time - morning_time < timedelta(hours=interval):
                        msg = f"{interval}小时内你已经早安过了哦~"
                        return MessageSegment.text(msg)
                
                # 若关闭超级亢奋，则判断睡眠时长是否小于设定时间
                if not self._config["morning"]["super_get_up"]["enable"]:
                    interval: int = self._config["morning"]["super_get_up"]["interval"]
                    night_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["night_time"], "%Y-%m-%d %H:%M:%S")
                    
                    if now_time - night_time < timedelta(hours=interval):
                        msg = "你可猝死算了吧？现在不能早安哦~"
                        return MessageSegment.text(msg)
            # 有信息但是隔日
            else:
                msg = random.choice(morning_prompt)
                return MessageSegment.text(msg)
                  
        # 否则说明：他还没睡过觉；即便如此，还是回复早安！
        else:
            msg = random.choice(morning_prompt)
            return MessageSegment.text(msg)
            
        # 当前面条件均符合的时候，允许早安
        num, in_sleep = self._morning_and_update(gid, uid, now_time)
        if isinstance(in_sleep, str):
            msg = f"早安成功！你的睡眠时长为{in_sleep}，\n你是今早第{num}个起床的{sex_str}！"
        else:
            msg = random.choice(morning_prompt)
 
        return MessageSegment.text(msg)

    # ------------------------------ Night Judgement ------------------------------ #
    def _night_and_update(self, gid: str, uid: str, now_time: datetime) -> Tuple[str, Union[str, int]]:
        '''
            Good night & update.
        '''
        self._load_data()
        
        # 没有晚安数据，则创建
        if uid not in self._morning[gid]:
            self._morning[gid].update({
                uid: {
                    "daily": {
                        "morning_time": 0, 
                        "night_time": now_time
                    },
                    "weekly": {
                        "weekly_morning_count": 0,          # Weekly good-morning count,                RESET at the late time of good-morning every Monday
                        "weekly_night_count": 1,            # Weekly good-night count,                  RESET at 0 A.M. every Monday
                        "weekly_sleep": [0, 0, 0, 0],       # Weekly sleeping time, list of days/hrs/mins/secs, RESET at the late time of good-morning every Monday
                        "lastweek_morning_count": 0,        # Good-morning count of last week,          REFRESH at the late time of good-morning every Monday
                        "lastweek_night_count": 0,          # Good-night count of last week,            REFRESH at 0 A.M. every Monday
                        "lastweek_sleep": [0, 0, 0, 0],     # Sleeping time of last week, list of days/hrs/mins/secs, REFRESH at the late time of good-morning every Monday
                        "lastweek_earliest_morning_time": 0,# Earliest good-morning time of last week,  REFRESH at a new daily good-morning time in
                        "lastweek_latest_night_time": 0     # Latest good-night time of last week,      REFRESH at a new daily good-night time in
                    },
                    "total": {
                        "morning_count": 0,                 # Total good-morning count, never RESET
                        "night_count": 1,                   # Total good-night count, never RESET
                        "total_sleep": [0, 0, 0, 0]         # Total sleeping time, list of days/hrs/mins/secs, REFRESH at every valid good-morning
                    }
                }
            })
            
            self._morning[gid][uid]["weekly"]["lastweek_latest_night_time"] = self._morning[gid][uid]["daily"]["night_time"]
            
        # 若有就更新数据
        else:
            # Daily night time
            self._morning[gid][uid]["daily"]["night_time"] = now_time
            # Weekly night count add
            self._morning[gid][uid]["weekly"]["weekly_night_count"] += 1
            # Total night count add
            self._morning[gid][uid]["total"]["night_count"] += 1
            
            lastweek_lnt: Union[int, str] = self._morning[gid][uid]["weekly"]["lastweek_latest_night_time"]
        
            # If lastweek_lnt is integer, it means no data
            if isinstance(lastweek_lnt, int):
                self._morning[gid][uid]["weekly"]["lastweek_latest_night_time"] = now_time
            else:
                # If daily sleep time is later than weekly's, update
                if is_later(self._morning[gid][uid]["daily"]["night_time"], self._morning[gid][uid]["weekly"]["lastweek_latest_night_time"]):
                    self._morning[gid][uid]["weekly"]["lastweek_latest_night_time"] = now_time
          
        # 当上次起床时间非0，计算清醒时长
        in_day_tmp: str = ""
        if self._morning[gid][uid]["daily"].get("morning_time", 0) != 0:
            get_up_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["morning_time"], "%Y-%m-%d %H:%M:%S")
            in_day: timedelta = now_time - get_up_time
            _, hours, minutes, seconds = total_seconds2tuple_time(int(in_day.total_seconds()))
            
            if in_day.days > 0:
                in_day_tmp = ""
            else:
                in_day_tmp = f"{hours}时{minutes}分{seconds}秒"

        # 判断是今天第几个睡觉的
        self._morning[gid]["group_count"]["daily"]["good_night"] += 1
        
        self._save_data()

        return self._morning[gid]["group_count"]["daily"]["good_night"], in_day_tmp if in_day_tmp != "" else 0

    def get_night_msg(self, gid: str, uid: str, sex_str: str) -> MessageSegment:
        '''
            Return good-night info.
        '''
        self._load_config()
        
        # 若开启规定时间晚安，则判断该时间是否允许晚安
        now_time: datetime = datetime.now()
        if self._config["night"]["night_intime"]["enable"]:
            _early_time: int = self._config["night"]["night_intime"]["early_time"]
            _late_time: int = self._config["night"]["night_intime"]["late_time"]
            
            if not is_NigTimeinRange(_early_time, _late_time, now_time):
                msg = f'现在不能晚安哦，可以晚安的时间为{_early_time}时到第二天早上{_late_time}时~'
                return MessageSegment.text(msg)

        self._init_group_data(gid)

        # 当数据里有过这个人的信息就判断:
        if uid in self._morning[gid]:
            
            # 若开启优质睡眠，则判断在设定时间内是否多次晚安
            if self._config["night"]["good_sleep"]["enable"]:
                interval: int = self._config["night"]["good_sleep"]["interval"]
                night_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["night_time"], "%Y-%m-%d %H:%M:%S")
                
                if now_time - night_time < timedelta(hours=interval):
                    msg = f'{interval}小时内你已经晚安过了哦~'
                    return MessageSegment.text(msg)
            
            # 若关闭深度睡眠，则判断不在睡觉的时长是否小于设定时长
            if isinstance(self._morning[gid][uid]["daily"]["morning_time"], str):
                if not self._config["night"]["deep_sleep"]["enable"]:
                    interval: int = self._config["night"]["deep_sleep"]["interval"]
                    morning_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["morning_time"], "%Y-%m-%d %H:%M:%S")
                    
                    if now_time - morning_time < timedelta(hours=interval):
                        msg = "睡这么久还不够？现在不能晚安哦~"
                        return MessageSegment.text(msg)

        # 当数据里没有这个人或者前面条件均符合的时候，允许晚安
        num, in_day = self._night_and_update(gid, uid, now_time)
        if isinstance(in_day, int):
            msg = f'晚安成功！你是今晚第{num}个睡觉的{sex_str}！'
        else:
            msg = f'晚安成功！你今天的清醒时长为{in_day}，\n你是今晚第{num}个睡觉的{sex_str}！'
            
        return MessageSegment.text(msg)
    
    # ------------------------------ Routine ------------------------------ #
    def get_my_routine(self, gid: str, uid: str) -> MessageSegment:
        '''
            Get user's routine.
            
            If on Monday and now is later than the latest time of good-morning of Monday, good-morning/night count of last week & sleeping time will be included.
            
            Else, add weekly info of current week.
        '''
        self._init_group_data(gid)
        
        now_time: datetime = datetime.now()
        today: int = now_time.weekday()
        
        if uid in self._morning[gid]:
            # Daily info
            get_up_time: str = self._morning[gid][uid]["daily"]["morning_time"]
            sleep_time: str = self._morning[gid][uid]["daily"]["night_time"]
            
            # Total info
            morning_count: int = self._morning[gid][uid]["total"]["morning_count"]
            night_count: int = self._morning[gid][uid]["total"]["night_count"]
            total_sleep: List[int] = self._morning[gid][uid]["total"]["total_sleep"]
            
            msg = "你的作息数据如下："
            msg += f"\n最近一次早安时间为{get_up_time}"
            msg += f"\n最近一次晚安时间为{sleep_time}"
            
            week_list: List[str] = ["一", "二", "三", "四", "五", "六", "日"]
                
            # When on Monday and now time is later than the latest time of good-morning
            if today == MONDAY:
                threshold_hour: int = self.get_refresh_time("morning", "late_time")
                
                if threshold_hour != -1 and is_later_oclock(now_time, threshold_hour):
                    lastweek_morning_count: int = self._morning[gid][uid]["weekly"]["lastweek_morning_count"]
                    lastweek_night_count: int = self._morning[gid][uid]["weekly"]["lastweek_night_count"]
                    
                    lastweek_sleep: List[int] = self._morning[gid][uid]["weekly"]["lastweek_sleep"]
                    
                    lastweek_lnt_date: datetime = datetime.strptime(self._morning[gid][uid]["weekly"]["lastweek_latest_night_time"], "%Y-%m-%d %H:%M:%S")
                    lastweek_lnt: time = datetime.strptime(lastweek_lnt_date, "%Y-%m-%d %H:%M:%S").time()
                    latest_day: int = datetime.strptime(lastweek_lnt_date, "%Y-%m-%d %H:%M:%S").weekday()
                    
                    lastweek_emt_date: datetime = datetime.strptime(self._morning[gid][uid]["weekly"]["lastweek_earliest_morning_time"], "%Y-%m-%d %H:%M:%S")
                    lastweek_emt: time = datetime.strptime(lastweek_emt_date, "%Y-%m-%d %H:%M:%S").time()
                    earliest_day: int = datetime.strptime(lastweek_emt_date, "%Y-%m-%d %H:%M:%S").weekday()
                    
                    msg += f"\n上周早安了{lastweek_morning_count}次"
                    msg += f"\n上周晚安了{lastweek_night_count}次"
                    msg += f"\n上周睡眠时间为{lastweek_sleep[0]}天{lastweek_sleep[1]}时{lastweek_sleep[2]}分{lastweek_sleep[3]}秒"
                    msg += f"\n上周最晚晚安时间是周{week_list[latest_day]} {lastweek_lnt}"
                    msg += f"\n上周最早早安时间是周{week_list[earliest_day]} {lastweek_emt}"
            
            # Not on Monday, add weekly info
            else:
                weekly_morning_count: int = self._morning[gid][uid]["weekly"]["weekly_morning_count"]
                weekly_night_count: int = self._morning[gid][uid]["weekly"]["weekly_night_count"]
                
                msg += f"\n本周早安了{weekly_morning_count}次"
                msg += f"\n本周晚安了{weekly_night_count}次"
                
            msg += f"\n一共早安了{morning_count}次"
            msg += f"\n一共晚安了{night_count}次"
            msg += f"\n一共睡眠了{total_sleep[0]}天{total_sleep[1]}时{total_sleep[2]}分{total_sleep[3]}秒"
        else:
            msg = "你本周还没有早晚安过呢！暂无数据~"
        
        return MessageSegment.text(msg)

    def get_group_routine(self, gid: str) -> Tuple[int, int, Optional[str]]:
        '''
            Get group's routine: daily good-morning/night count.
            If on Monday and now is later than the latest time of good-morning of Monday, add sleeping king of last week.
        '''
        self._init_group_data(gid)
        
        now_time: datetime = datetime.now()
        today: int = now_time.weekday()
        
        morning_count: int = self._morning[gid]["group_count"]["daily"]["good_morning"]
        night_count: int = self._morning[gid]["group_count"]["daily"]["good_night"]        
        
        if today == MONDAY:
            threshold_hour: int = self.get_refresh_time("morning", "late_time")
            
            if threshold_hour != -1 and is_later_oclock(now_time, threshold_hour):
                uid: str = self._morning[gid]["group_count"]["weekly"]["sleeping_king"]
            
            return morning_count, night_count, uid if uid != "" else None
        
        return morning_count, night_count, None

    # ------------------------------ Utils ------------------------------ #
    def _save_data(self) -> None:
        with open(self._morning_path, 'w', encoding='utf-8') as f:
            json.dump(self._morning, f, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
                
    def _save_config(self) -> None:
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=4)

    def _load_data(self) -> None:
        with open(self._morning_path, "r", encoding="utf-8") as f:
            self._morning = json.load(f)
        
    def _load_config(self) -> None:
        with open(self._config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)
            
    def get_refresh_time(self, _type: str, key: str) -> int:
        '''
            Get the time given a specific type and key.
        '''
        self._load_config()
        
        if _type == "morning":
            return self._config[_type]["morning_intime"][key] if self._config[_type]["morning_intime"]["enable"] else -1

        if _type == "night":
            return self._config[_type]["night_intime"][key] if self._config[_type]["night_intime"]["enable"] else -1
        
    def daily_scheduler(self, hours: Optional[int] = None) -> None:
        '''
            Run the scheduler for refreshing daily good-morning/night counts. Replace the existing scheduler.
        '''
        if isinstance(hours, int):
            _hours = hours
        else:
            _hours = self.get_refresh_time("night", "early_time")
        
        if _hours != -1:
            scheduler.add_job(
                self.daily_refresh,
                "cron",
                id="daily_scheduler",
                replace_existing=True,
                hour=_hours,
                minute=0,
                misfire_grace_time=60
            )

    def weekly_sleep_time_scheduler(self, hours: Optional[int] = None) -> None:
        '''
            Run the scheduler for refreshing the weekly sleeping time. Replace the existing scheduler.
        '''
        if isinstance(hours, int):
            _hours = hours
        else:
            _hours = self.get_refresh_time("morning", "late_time")
        
        if _hours != -1:
            scheduler.add_job(
                self.weekly_sleep_time_refresh,
                "cron",
                id="weekly_sleep_time_scheduler",
                replace_existing=True,
                hour=_hours,
                minute=0,
                day_of_week="1",
                misfire_grace_time=60
            )

morning_manager = MorningManager()

__all__ = [
    morning_manager
]