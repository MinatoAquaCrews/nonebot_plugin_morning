from calendar import MONDAY
from nonebot import require
from nonebot.adapters.onebot.v11 import MessageSegment
from typing import Union, List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, time
from .config import *
from .utils import *
try:
    import ujson as json
except ModuleNotFoundError:
    import json
    
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from apscheduler.jobstores.base import JobLookupError

class MorningManager:
    def __init__(self):
        self._morning: Dict[str, Dict[str, Dict[str, Dict[str, Union[str, int, clocktime]]]]] = dict()
        self._morning_path: Path = morning_config.morning_path / "morning.json"
        
        self._config: Dict[str, Dict[str, Dict[str, Union[bool, int]]]] = dict()
        self._config_path: Path = morning_config.morning_path / "config.json"

    def _init_group_data(self, gid: str) -> None:
        '''
            Initialize group data
        '''
        self._load_data()
        if gid not in self._morning:
            self._morning.update({
                gid: {
                    "group_count": {
                        "daily": {
                            "good_morning": 0,
                            "good_night": 0 
                        },
                        "weekly": {
                            # "weekly_sleeping_king": ""
                        }
                    }
                }
            })
            
            self._save_data()

    def get_current_config(self) -> MessageSegment:
        '''
            Return current configure
        '''
        msg = "早安晚安设置如下："
        self._load_config()
        
        # morning config
        morning_intime = self._config["morning"]["morning_intime"]["enable"]
        if morning_intime:
            msg += "\n是否要求规定时间内起床：是\n - 最早允许起床时间：" + str(self._config["morning"]['morning_intime']["early_time"]) + "点\n - 最晚允许起床时间：" + str(self._config["morning"]["morning_intime"]["late_time"]) + "点"
        else:
            msg += "\n是否要求规定时间内起床：否"
            
        multi_get_up = self._config["morning"]["multi_get_up"]["enable"]
        if multi_get_up:
            msg += "\n是否允许连续多次起床：是"
        else:
            msg += "\n是否允许连续多次起床：否\n - 允许的最短起床间隔：" + str(self._config["morning"]["multi_get_up"]["interval"]) + "小时"
        
        super_get_up = self._config["morning"]["super_get_up"]["enable"]
        if super_get_up:
            msg += "\n是否允许超级亢奋(即睡眠时长很短)：是"
        else:
            msg += "\n是否允许超级亢奋(即睡眠时长很短)：否\n - 允许的最短睡觉时长：" + str(self._config["morning"]["super_get_up"]["interval"]) + "小时"
        
        # night config
        night_intime = self._config["night"]["night_intime"]["enable"]
        if night_intime:
            msg += "\n是否要求规定时间内睡觉：是\n - 最早允许睡觉时间：" + str(self._config["night"]["night_intime"]["early_time"]) + \
                "点\n - 最晚允许睡觉时间：第二天早上" + str(self._config["night"]["night_intime"]["late_time"]) + "点"
        else:
            msg += "\n是否要求规定时间内睡觉：否"
        
        good_sleep = self._config["night"]["good_sleep"]["enable"]
        if good_sleep:
            msg += "\n是否开启优质睡眠：是"
        else:
            msg += "\n是否开启优质睡眠：否\n - 允许的最短优质睡眠：" + str(self._config["night"]["good_sleep"]["interval"]) + "小时"
        
        deep_sleep = self._config["night"]["deep_sleep"]["enable"]
        if deep_sleep:
            msg += "\n是否允许深度睡眠(即清醒时长很短)：是"
        else:
            msg += "\n是否允许深度睡眠(即清醒时长很短)：否\n - 允许的最短清醒时长：" + str(self._config["night"]["deep_sleep"]["interval"]) + "小时"
        
        return MessageSegment.text(msg)

    # ------------------------------ Config ------------------------------ #
    def _change_enable(self, day_or_night: str, _setting: str, new_state: bool) -> str:
        '''
            Change and save new state of setting
        '''
        self._load_config()
        self._config[day_or_night][_setting]["enable"] = new_state
        self._save_config()

        return "配置更新成功！"

    def _change_set_time(self, _day_or_night: str, _setting: str, _interval_or_early_time: int, _late_time: Optional[int] = None) -> str:
        '''
            Change time interval
        '''
        self._load_config()
        
        if _setting == "morning_intime" or _setting == "night_intime":
            early_time = _interval_or_early_time
            if isinstance(_late_time, int):
                late_time = _late_time
            else:
                return "配置更新失败：缺少参数！"
            
            self._config[_day_or_night][_setting]["early_time"] = early_time
            self._config[_day_or_night][_setting]["late_time"] = late_time
        else:
            interval = _interval_or_early_time
            self._config[_day_or_night][_setting]["interval"] = interval
        
        msg = "配置更新成功！"
        
        if _setting == "morning_intime" or _setting == "night_intime" or _setting == "good_sleep" \
            and self._config[_day_or_night][_setting]["enable"] == False:
            self._config[_day_or_night][_setting]["enable"] = True	# True is the default setting
            msg += "且此项设置已启用！"
        
        # Some settings are False in default
        if _setting == "multi_get_up" or _setting == "super_get_up" or _setting == "deep_sleep" \
            and self._config[_day_or_night][_setting]["enable"] == True:
            self._config[_day_or_night][_setting]["enable"] = False	# False is the default setting
            msg += "且此项设置已禁用！"
        
        self._save_config()
            
        return msg
    
    def daily_refresh(self) -> None:
        '''
            1. Reset every day morning/night count of groups
            2. Every Monday at 0AM, store the weekly morning/night count of weekly info to "lastweek_" AND reset
            3. Every Tuesday at 0AM, reset lastweek morning/night count of weekly info
        '''
        self._load_data()
        
        for gid in self._morning:
            self._morning[gid]["group_count"]["daily"]["good_morning"] = 0
            self._morning[gid]["group_count"]["daily"]["good_night"] = 0
        
        self._save_data()
        
    def weekly_data_refresh(self) -> None:
        '''
            Refresh weekly morning/night count every Monday EXCEPT sleep time
        '''
        self._load_data()
        
        for gid in self._morning:
            for uid in self._morning[gid]:
                self._morning[gid][uid]["weekly"]["lastweek_morning_count"] = self._morning[gid][uid]["weekly"]["weekly_morning_count"]
                self._morning[gid][uid]["weekly"]["lastweek_night_count"] = self._morning[gid][uid]["weekly"]["weekly_night_count"]

                self._morning[gid][uid]["weekly"]["weekly_morning_count"] = 0
                self._morning[gid][uid]["weekly"]["weekly_night_count"] = 0
                
        self._save_data()
        
    def weekly_sleep_time_refresh(self) -> None:
        '''
            Refresh weekly sleep time at "late_time" of "morning_intime" every Monday
        '''
        self._load_data()
        
        for gid in self._morning:
            for uid in self._morning[gid]:
                self._morning[gid][uid]["weekly"]["lastweek_sleep"] = self._morning[gid][uid]["weekly"]["weekly_sleep"]
                self._morning[gid][uid]["weekly"]["weekly_sleep"] = 0
                
        self._save_data()

    def morning_config(self, _mor_setting: str, *args: List[int]) -> MessageSegment:
        '''
            Config about morning
        '''
        _setting = mor_switcher[_mor_setting]
        if _setting == "morning_intime":
            early_time = args[0]
            late_time = args[1]
            
            if early_time < 0 or early_time > 24 or late_time < 0 or late_time > 24:
                msg = "错误！您设置的时间未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("morning", _setting, early_time, late_time)
            
                # Change the data of weekly_sleep_time_refresh_scheduler
                self.weekly_scheduler_run(late_time)
        else:
            interval = args[0]
            
            if interval < 0 or interval > 24:
                msg = "错误！您设置的时间间隔未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("morning", _setting, interval)
        
        return MessageSegment.text(msg)

    def morning_switch(self, _mor_setting: str, new_state: bool) -> MessageSegment:
        '''
            Enable/Disable of morning settings
        '''
        _setting = mor_switcher[_mor_setting]
        msg = self._change_enable("morning", _setting, new_state)
        
        # Change the status of weekly_sleep_time_refresh_scheduler
        if _setting == "morning_intime":
            # Remove the scheduler
            if not new_state:
                try:
                    scheduler.remove_job("weekly_sleep_time_refresh_scheduler")
                except JobLookupError as e:
                    logger.warning(f"每周睡眠时间定时刷新任务移除失败: {e}")
                    msg += "\n每周睡眠时间定时刷新任务移除失败"
            
            # Add the scheduler if it dosen't exist
            else:
                if not scheduler.get_job("weekly_sleep_time_refresh_scheduler"):
                    hours: int = self.get_refresh_time()
                    
                    if hours != -1:
                        self.weekly_scheduler_run(hours)
        
        return MessageSegment.text(msg)

    def night_config(self, _nig_setting: str, *args: List[int]) -> MessageSegment:
        '''
            Config about night
        '''
        _setting = nig_switcher[_nig_setting]
        if _setting == "night_intime":
            early_time = args[0]
            late_time = args[1]
            
            if early_time < 0 or early_time > 24 or late_time < 0 or late_time > 24:
                msg = "错误！您设置的时间未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("night", _setting, early_time, late_time)
        else:
            interval = args[0]
            
            if interval < 0 or interval > 24:
                msg = "错误！您设置的时间间隔未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("night", _setting, interval, None)
        
        return MessageSegment.text(msg)

    def night_switch(self, _nig_setting: str, new_state: bool) -> MessageSegment:
        '''
            Enable/Disable of night settings
        '''
        _setting = nig_switcher[_nig_setting]
        msg = self._change_enable("night", _setting, new_state)
        
        return MessageSegment.text(msg)

    # ------------------------------ Morning Judgement ------------------------------ #
    def _morning_and_update(self, gid: str, uid: str, now_time: datetime) -> Tuple[str, Union[str, int]]:
        '''
            Morning & update data
        '''
        # 起床并写数据
        sleep_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["night_time"], "%Y-%m-%d %H:%M:%S")
        in_sleep: clocktime = now_time - sleep_time
        
        # 睡觉时间小于24小时就同时给出睡眠时长，记录；否则隔日
        in_sleep_tmp: Union[str, int] = 0
        
        if in_sleep.days > 0:
            in_sleep_tmp = 0
        else:
            in_sleep_tmp = f"{in_sleep.hours}时{in_sleep.minutes}分{in_sleep.seconds}秒"
            self._morning[gid][uid]["weekly"]["weekly_sleep"] += in_sleep
            self._morning[gid][uid]["total"]["total_sleep"] += in_sleep

        self._load_data()
        
        # Daily morning time
        self._morning[gid][uid]["daily"]["morning_time"] = now_time.strftime("%Y-%m-%d %H:%M:%S")
        # Weekly morning count add
        self._morning[gid][uid]["weekly"]["weekly_morning_count"] += 1
        # Total morning count add
        self._morning[gid][uid]["total"]["morning_count"] += 1
        
        # If weekly morning time is later than daily's, update
        if not is_later(self._morning[gid][uid]["daily"]["morning_time"], self._morning[gid][uid]["weekly"]["lastweek_earliest_morning_time"]):
            self._morning[gid][uid]["weekly"]["lastweek_earliest_morning_time"] = self._morning[gid][uid]["daily"]["morning_time"]
        
        # 判断是今天第几个起床的
        self._morning[gid]["group_count"]["daily"]["good_morning"] += 1
        self._save_data()

        return self._morning[gid]["group_count"]["daily"]["good_morning"], in_sleep_tmp

    def get_morning_msg(self, gid: str, uid: str, sex_str: str) -> MessageSegment:
        '''
            Return good morning info
        '''
        self._load_config()
        msg: str = ""
        
        # 若开启规定时间早安，则判断该时间是否允许早安
        now_time: datetime = datetime.now()
        if self._config["morning"]["morning_intime"]["enable"]:
            _early_time: int = self._config["morning"]["morning_intime"]["early_time"]
            _late_time: int = self._config["morning"]["morning_intime"]["late_time"]
            if not is_MorTimeinRange(_early_time, _late_time, now_time):
                msg = f"现在不能早安哦，可以早安的时间为{_early_time}时到{_late_time}时~"
                return MessageSegment.text(msg)

        self._init_group_data(gid)
        
        # 当数据里有过这个人的信息就判断：是否隔日
        last_sleep_time: str = self._morning[gid][uid]["daily"]["night_time"]
        if uid in self._morning[gid] and is_TimeinInterval(last_sleep_time, now_time, 24):
            
            # 若关闭连续多次早安，则判断在设定时间内是否多次早安
            if not self._config["morning"]["multi_get_up"]["enable"] and self._morning[gid][uid]["daily"]["morning_time"] != 0:
                interval: int = self._config["morning"]["multi_get_up"]["interval"]
                morning_time: str = self._morning[gid][uid]["daily"]["morning_time"]
                if is_TimeinInterval(morning_time, now_time, interval):
                    msg = f"{interval}小时内你已经早安过了哦~"
                    return MessageSegment.text(msg)
            
            # 若关闭超级亢奋，则判断睡眠时长是否小于设定时间
            if not self._config["morning"]["super_get_up"]["enable"]:
                interval: int = self._config["morning"]["super_get_up"]["interval"]
                night_time: str = self._morning[gid][uid]["daily"]["night_time"]
                if is_TimeinInterval(night_time, now_time, interval):
                    msg = "你可猝死算了吧？现在不能早安哦~"
                    return MessageSegment.text(msg)
                  
        # 否则说明：他还没睡过觉、或为隔日早安
        else:
            msg = "你还没睡过觉呢！不能早安哦~"
            return MessageSegment.text(msg)
            
        # 当前面条件均符合的时候，允许早安
        num, in_sleep = self._morning_and_update(gid, uid, now_time)
        if isinstance(in_sleep, str):
            msg = f"早安成功！你的睡眠时长为{in_sleep}，\n你是今天第{num}个起床的{sex_str}！"
        else:
            msg = "你还没睡过觉呢！不能早安哦~"
 
        return MessageSegment.text(msg)

    # ------------------------------ Night Judgement ------------------------------ #
    def _night_and_update(self, gid: str, uid: str, now_time: datetime) -> Tuple[str, Union[str, int]]:
        '''
            Good night & update
        '''
        self._load_data()
        
        # 没有晚安数据，则创建
        if uid not in self._morning[gid]:
            self._morning[gid].update({
                uid: {
                    "daily": {
                        "morning_time": 0, 
                        "night_time": now_time.strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "weekly": {
                        "weekly_morning_count": 0,          # 周早安天数
                        "weekly_night_count": 1,            # 周晚安天数
                        "weekly_sleep": clocktime(),        # 周睡眠时长
                        "lastweek_night_count": 0,
                        "lastweek_morning_count": 0,
                        "lastweek_sleep": clocktime(),
                        "lastweek_latest_night_time": 0,    # 周晚安最晚的时间
                        "lastweek_earliest_morning_time": 0 # 周早起最早的时间
                    },
                    "total": {
                        "night_count": 1,                   # 总晚安次数
                        "morning_count": 0,                 # 总早安次数
                        "total_sleep": 0                    # 总睡眠时间
                    }
                }
            })
            
            self._morning[gid][uid]["weekly"]["lastweek_latest_night_time"] = self._morning[gid][uid]["daily"]["night_time"]
            
        # 若有就更新数据
        else:
            # Daily night time
            self._morning[gid][uid]["daily"]["night_time"] = now_time.strftime("%Y-%m-%d %H:%M:%S")
            # Weekly night count add
            self._morning[gid][uid]["weekly"]["weekly_night_count"] += 1
            # Total night count add
            self._morning[gid][uid]["total"]["night_count"] += 1
            
            # If daily sleep time is later than weekly's, update
            if is_later(self._morning[gid][uid]["daily"]["night_time"], self._morning[gid][uid]["weekly"]["lastweek_latest_night_time"]):
                self._morning[gid][uid]["weekly"]["lastweek_latest_night_time"] = self._morning[gid][uid]["daily"]["night_time"]
          
        # 当上次起床时间非0，计算清醒时长
        in_day_tmp: Union[str, int] = 0
        if self._morning[gid][uid]["daily"].get("morning_time", 0) != 0:
            get_up_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["morning_time"], "%Y-%m-%d %H:%M:%S")
            in_day: clocktime = now_time - get_up_time
            
            if in_day.days > 0:
                in_day_tmp = 0
            else:
                in_day_tmp = f"{in_day.hours}时{in_day.minutes}分{in_day.seconds}秒"

        # 判断是今天第几个睡觉的
        self._morning[gid]["group_count"]["daily"]["good_night"] += 1
        self._save_data()

        return self._morning[gid]["group_count"]["daily"]["good_night"], in_day_tmp

    def get_night_msg(self, gid: str, uid: str, sex_str: str) -> MessageSegment:
        '''
            Return good night info
        '''
        self._load_config()
        msg: str = ""
        
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
                night_time: str = self._morning[gid][uid]["daily"]["night_time"]
                if is_TimeinInterval(night_time, now_time, interval):
                    msg = f'{interval}小时内你已经晚安过了哦~'
                    return MessageSegment.text(msg)
            
            # 若关闭深度睡眠，则判断不在睡觉的时长是否小于设定时长
            morning_time: Union[str, int] = self._morning[gid][uid]["daily"].get("morning_time", 0)
            if not self._config["night"]["deep_sleep"]["enable"] and isinstance(morning_time, str):
                interval: int = self._config["night"]["deep_sleep"]["interval"]
                if is_TimeinInterval(morning_time, now_time, interval):
                    msg = "睡这么久还不够？现在不能晚安哦~"
                    return MessageSegment.text(msg)

        # 当数据里没有这个人或者前面条件均符合的时候，允许晚安
        num, in_day = self._night_and_update(gid, uid, now_time)
        if isinstance(in_day, int):
            msg = f'晚安成功！你是今天第{num}个睡觉的{sex_str}！'
        else:
            msg = f'晚安成功！你今天的清醒时长为{in_day}，\n你是今天第{num}个睡觉的{sex_str}！'
            
        return MessageSegment.text(msg)
    
    # ------------------------------ Routine ------------------------------ #
    def get_my_routine(self, gid: str, uid: str) -> MessageSegment:
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
            total_sleep: clocktime = self._morning[gid][uid]["total"]["total_sleep"]
            
            msg = "你的作息数据如下："
            msg += f"\n最近一次早安时间为{get_up_time}"
            msg += f"\n最近一次晚安时间为{sleep_time}"
            
            week_list: List[str] = ["一", "二", "三", "四", "五", "六", "日"]
                
            # If today is Monday, add these info:
            if today == MONDAY:
                lastweek_morning_count: int = self._morning[gid][uid]["weekly"]["lastweek_morning_count"]
                lastweek_night_count: int = self._morning[gid][uid]["weekly"]["lastweek_night_count"]
                
                msg += f"\n上周早安了{lastweek_morning_count}次"
                msg += f"\n上周晚安了{lastweek_night_count}次"
                
                threshold_hour: int = self.get_refresh_time()
                
                # When now time is later than the late time of morning time of Monday, the sleep times are refreshed
                if threshold_hour != -1:
                    if now_time.hour > threshold_hour or (now_time.hour == threshold_hour and (now_time.minute > 0 or now_time.second > 0)):
                        lastweek_sleep: clocktime = self._morning[gid][uid]["weekly"]["lastweek_sleep"]
                        lastweek_lnt_date: datetime = datetime.strptime(self._morning[gid][uid]["weekly"]["lastweek_latest_night_time"], "%Y-%m-%d %H:%M:%S")
                        lastweek_lnt: time = datetime.strptime(lastweek_lnt_date, "%Y-%m-%d %H:%M:%S").time()
                        latest_day: int = datetime.strptime(lastweek_lnt_date, "%Y-%m-%d %H:%M:%S").weekday()
                        
                        lastweek_emt_date: datetime = datetime.strptime(self._morning[gid][uid]["weekly"]["lastweek_earliest_morning_time"], "%Y-%m-%d %H:%M:%S")
                        lastweek_emt: time = datetime.strptime(lastweek_emt_date, "%Y-%m-%d %H:%M:%S").time()
                        earliest_day: int = datetime.strptime(lastweek_emt_date, "%Y-%m-%d %H:%M:%S").weekday()
                        
                        msg += f"\n上周睡眠时间为{lastweek_sleep.days}天{lastweek_sleep.hours}时{lastweek_sleep.minutes}分{lastweek_sleep.seconds}秒"
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
            msg += f"\n一共睡眠了{total_sleep.days}天{total_sleep.hours}时{total_sleep.minutes}分{total_sleep.seconds}秒"
        else:
            msg = "你本周还没有早安晚安过呢！暂无数据~"
        
        return MessageSegment.text(msg)

    def get_group_routine(self, gid: str) -> MessageSegment:
        self._init_group_data(gid)
        
        moring_count: int = self._morning[gid]["group_count"]["daily"]["good_morning"]
        night_count: int = self._morning[gid]["group_count"]["daily"]["good_night"]
        
        msg = f"今天已经有{moring_count}位群友早安了，{night_count}位群友晚安了~"
        
        return MessageSegment.text(msg)

    # ------------------------------ Utils ------------------------------ #
    def _save_data(self) -> None:
        with open(self._morning_path, 'w', encoding='utf-8') as f:
            json.dump(self._morning, f, ensure_ascii=False, indent=4)
                
    def _save_config(self) -> None:
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=4)

    def _load_data(self) -> None:
        with open(self._morning_path, "r", encoding="utf-8") as f:
            self._morning = json.load(f)
        
    def _load_config(self) -> None:
        with open(self._config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)
            
    def get_refresh_time(self) -> int:
        self._load_config()
        
        return self._config["morning"]["morning_intime"]["late_time"] if self._config["morning"]["morning_intime"]["enable"] else -1

    def weekly_scheduler_run(self, _hours: int) -> None:
        '''
            Run the scheduler for refreshing the weekly sleep time. Replace the existing scheduler.
        '''
        scheduler.add_job(
            self.weekly_sleep_time_refresh(),
            "cron",
            id="weekly_sleep_time_refresh_scheduler",
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