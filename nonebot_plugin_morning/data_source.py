from nonebot import require
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import MessageSegment
from calendar import MONDAY
from typing import Union, List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, time
import random
from .config import morning_config, default_config
from .utils import *
    
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from apscheduler.jobstores.base import JobLookupError

class MorningManager:
    def __init__(self):
        self._morning: Dict[str, Dict[str, Dict[str, Dict[str, Union[str, int, datetime, List[int]]]]]] = dict()
        self._morning_path: Path = morning_config.morning_path / "morning.json"
        
        self._config: Dict[str, Dict[str, Dict[str, Dict[str, Union[bool, int]]]]] = dict()
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

    # ------------------------------ Config ------------------------------ #
    def auto_config_trim(self):
        '''
            Auto trim specific groups if their config are the same as the DEFAULT.
        '''
        self._load_config()
        
        for gid in self._config:
            if gid == "default":
                continue
            
            if self._config[gid] == default_config:
                self._config.pop(gid)
        
        self._save_config()
        
    def get_group_config(self, gid: str) -> MessageSegment:
        '''
            Return the current configurations.
        '''
        msg: str = "早安晚安设置如下："
        self._load_config()
        
        if gid not in self._config:
            _group_config = self._config["default"]
        else:
            _group_config = self._config[gid]
        
        # Morning config
        msg += "\n是否要求规定时间内起床："
        morning_intime = _group_config["morning"]["morning_intime"]["enable"]
        if morning_intime:
            msg += "是\n - 最早允许起床时间：" + str(_group_config["morning"]['morning_intime']["early_time"]) + "点\n - 最晚允许起床时间：" + str(_group_config["morning"]["morning_intime"]["late_time"]) + "点"
        else:
            msg += "否"
        
        msg += "\n是否允许连续多次起床："
        multi_get_up = _group_config["morning"]["multi_get_up"]["enable"]
        if multi_get_up:
            msg += "是"
        else:
            msg += "否\n - 允许的最短起床间隔：" + str(_group_config["morning"]["multi_get_up"]["interval"]) + "小时"
        
        msg += "\n是否允许超级亢奋（即睡眠时长很短）："
        super_get_up= _group_config["morning"]["super_get_up"]["enable"]
        if super_get_up:
            msg += "是"
        else:
            msg += "否\n - 允许的最短睡觉时长：" + str(_group_config["morning"]["super_get_up"]["interval"]) + "小时"
        
        # Night config
        msg += "\n是否要求规定时间内睡觉："
        night_intime = _group_config["night"]["night_intime"]["enable"]
        if night_intime:
            msg += "是\n - 最早允许睡觉时间：" + str(_group_config["night"]["night_intime"]["early_time"]) + \
                "点\n - 最晚允许睡觉时间：第二天早上" + str(_group_config["night"]["night_intime"]["late_time"]) + "点"
        else:
            msg += "否"
        
        msg += "\n是否开启优质睡眠："
        good_sleep = _group_config["night"]["good_sleep"]["enable"]
        if good_sleep:
            msg += "是"
        else:
            msg += "否\n - 允许的最短优质睡眠：" + str(_group_config["night"]["good_sleep"]["interval"]) + "小时"
        
        msg += "\n是否允许深度睡眠（即清醒时长很短）："
        deep_sleep = _group_config["night"]["deep_sleep"]["enable"]
        if deep_sleep:
            msg += "是"
        else:
            msg += "否\n - 允许的最短清醒时长：" + str(_group_config["night"]["deep_sleep"]["interval"]) + "小时"
        
        return MessageSegment.text(msg)
    
    def _change_enable(self, _time: str, _setting: str, new_state: bool, gid: str) -> str:
        '''
            Change and save the new state of a setting. If group id doesn't exists, create the default first.
        '''
        self._load_config()
        
        # Once a group config is changed, create the specific config for it
        if gid not in self._config:
            self._config.update({gid: default_config})
        
        self._config[gid][_time][_setting]["enable"] = new_state
        self._save_config()

        return "配置更新成功！"

    def _change_set_time(self, gid: str, _day_or_night: str, _setting: str, _interval_or_early_time: int, _late_time: Optional[int] = None) -> str:
        '''
            Change the interval of a setting.
        '''
        self._load_config()
        
        # Once a group config is changed, create the specific config for it
        if gid not in self._config:
            self._config.update({gid: default_config})
        
        if _setting == "morning_intime" or _setting == "night_intime":
            if not isinstance(_late_time, int):
                return "配置更新失败：缺少参数！"
            
            early_time: int = _interval_or_early_time
            late_time: int = _late_time
            
            self._config[gid][_day_or_night][_setting]["early_time"] = early_time
            self._config[gid][_day_or_night][_setting]["late_time"] = late_time
        else:
            interval: int = _interval_or_early_time
            self._config[gid][_day_or_night][_setting]["interval"] = interval
        
        msg: str = "配置更新成功！"
        
        # Some settings are True in default
        if _setting == "morning_intime" or _setting == "night_intime" or _setting == "good_sleep" \
            and self._config[gid][_day_or_night][_setting]["enable"] == False:
            self._config[gid][_day_or_night][_setting]["enable"] = True
            msg += "且此项设置已启用！"
        
        # Some settings are False in default
        if _setting == "multi_get_up" or _setting == "super_get_up" or _setting == "deep_sleep" \
            and self._config[gid][_day_or_night][_setting]["enable"] == True:
            self._config[gid][_day_or_night][_setting]["enable"] = False
            msg += "且此项设置已禁用！"
        
        self._save_config()
            
        return msg

    def morning_config(self, _setting: str, gid: Optional[str] = None, *args) -> MessageSegment:
        '''
            Configurations about morning. The param _setting is a legal item.
        '''
        _setting: str = mor_switcher[_setting]
        msg: str = ""
        
        if _setting == "morning_intime":
            early_time: int = args[0]
            late_time: int = args[1]
            
            if early_time < 0 or early_time > 24 or late_time < 0 or late_time > 24:
                msg = "错误！您设置的时间未在0-24之间"
            else:
                if isinstance(gid, str):
                    # Create a specific config for the group
                    msg = self._change_set_time(gid, "morning", _setting, early_time, late_time)
                
                    # The lastest time of good morning is changed. Change the weekly sleep time scheduler.
                    self.weekly_sleep_time_scheduler(SchedulerMode.SPECIFIC_GROUP_AND_HOUR, gid, late_time)
        else:
            interval: int = args[0]
            
            if interval < 0 or interval > 24:
                msg = "错误！您设置的时间间隔未在0-24之间"
            else:
                if isinstance(gid, str):
                    msg = self._change_set_time(gid, "morning", _setting, interval)
        
        return MessageSegment.text(msg)

    def morning_switch(self, _setting: str, new_state: bool, gid: Optional[str] = None) -> MessageSegment:
        '''
            Enable/Disable of morning settings.
        '''
        setting: str = mor_switcher[_setting]
        
        if isinstance(gid, str):
            # Already created the specific config for the group here
            msg: str = self._change_enable("morning", setting, new_state, gid)
            
            # Change the status of weekly sleep time scheduler
            if setting == "morning_intime":
                # Remove the scheduler if new state is False
                if not new_state:
                    if scheduler.get_job(f"weekly_sleep_time_scheduler_{gid}"):
                        scheduler.pause_job(f"weekly_sleep_time_scheduler_{gid}")
                        logger.info(f"Group {gid} | 每周睡眠时间定时刷新任务已挂起！")
                
                # Add the scheduler if they don't exist
                else:
                    if scheduler.get_job(f"weekly_sleep_time_scheduler_{gid}"):
                        scheduler.resume_job(f"weekly_sleep_time_scheduler_{gid}")
                        logger.info(f"Group {gid} | 每周睡眠时间定时刷新任务已恢复运行！")
                    else:
                        self.weekly_sleep_time_scheduler(SchedulerMode.SPECIFIC_GROUP, gid)
                        logger.info(f"Group {gid} | 每周睡眠时间定时刷新任务已启动！")
                
        return MessageSegment.text(msg)

    def night_config(self, _setting: str, gid: Optional[str] = None, *args) -> MessageSegment:
        '''
            Configurations about night. The param _setting is a legal item.
        '''
        setting: str = nig_switcher[_setting]
        msg: str = ""
        
        if setting == "night_intime":
            early_time: int = args[0]
            late_time: int = args[1]
            
            if early_time < 0 or early_time > 24 or late_time < 0 or late_time > 24:
                msg = "错误！您设置的时间未在0-24之间"
            else:
                if isinstance(gid, str):
                    # Create a specific config for the group
                    msg = self._change_set_time(gid, "night", setting, early_time, late_time)
                    
                    # The earliest time of good night is changed. Change the daily scheduler.
                    self.daily_scheduler(SchedulerMode.SPECIFIC_GROUP_AND_HOUR, gid, early_time)
                    # The latest time of good night is changed. Change the weekly night scheduler.
                    self.weekly_night_scheduler(SchedulerMode.SPECIFIC_GROUP_AND_HOUR, gid, late_time)           
        else:
            interval: int = args[0]
            
            if interval < 0 or interval > 24:
                msg = "错误！您设置的时间间隔未在0-24之间"
            else:
                if isinstance(gid, str):
                    msg = self._change_set_time(gid, "night", setting, interval, None)
        
        return MessageSegment.text(msg)

    def night_switch(self, _setting: str, new_state: bool, gid: Optional[str] = None) -> MessageSegment:
        '''
            Enable/Disable of night settings.
        '''
        setting: str = nig_switcher[_setting]
        
        if isinstance(gid, str):
            # Already created the specific config for the group here
            msg: str = self._change_enable("night", setting, new_state, gid)
            
            # Change the status of daily scheduler
            if setting == "night_intime":
                # Remove the scheduler if new state is False
                if not new_state:
                    if scheduler.get_job(f"daily_scheduler_{gid}"):
                        scheduler.pause_job(f"daily_scheduler_{gid}")
                        logger.info(f"Group {gid} | 每日早晚安定时刷新任务已挂起！")
                    
                    if scheduler.get_job(f"weekly_night_{gid}"):
                        scheduler.pause_job(f"weekly_night_{gid}")
                        logger.info(f"Group {gid} | 每周晚安定时刷新任务已挂起！")
                
                # Add the scheduler if they don't exist
                else:
                    if scheduler.get_job(f"daily_scheduler_{gid}"):
                        scheduler.resume_job(f"daily_scheduler_{gid}")
                        logger.info(f"Group {gid} | 每日早晚安定时刷新任务已恢复运行！")
                    else:
                        self.daily_scheduler(SchedulerMode.SPECIFIC_GROUP, gid)
                        logger.info(f"Group {gid} | 每日早晚安定时刷新任务已启动！")
                    
                    if scheduler.get_job(f"weekly_night_{gid}"):
                        scheduler.resume_job(f"weekly_night_{gid}")
                        logger.info(f"Group {gid} | 每周晚安定时刷新任务已恢复运行！")
                    else:
                        self.weekly_night_scheduler(SchedulerMode.SPECIFIC_GROUP, gid)
                        logger.info(f"Group {gid} | 每周晚安定时刷新任务已启动！")
        
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
        _gid: str = "default" if gid not in self._config else gid
        
        # 若开启规定时间早安，则判断该时间是否允许早安
        now_time: datetime = datetime.now()
        if self._config[_gid]["morning"]["morning_intime"]["enable"]:
            _early_time: int = self._config[_gid]["morning"]["morning_intime"]["early_time"]
            _late_time: int = self._config[_gid]["morning"]["morning_intime"]["late_time"]
            
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
                if not self._config[_gid]["morning"]["multi_get_up"]["enable"] and self._morning[gid][uid]["daily"]["morning_time"] != 0:
                    interval: int = self._config[_gid]["morning"]["multi_get_up"]["interval"]
                    morning_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["morning_time"], "%Y-%m-%d %H:%M:%S")
                    
                    if now_time - morning_time < timedelta(hours=interval):
                        msg = f"{interval}小时内你已经早安过了哦~"
                        return MessageSegment.text(msg)
                
                # 若关闭超级亢奋，则判断睡眠时长是否小于设定时间
                if not self._config[_gid]["morning"]["super_get_up"]["enable"]:
                    interval: int = self._config[_gid]["morning"]["super_get_up"]["interval"]
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
        _gid: str = "default" if gid not in self._config else gid
        
        # 若开启规定时间晚安，则判断该时间是否允许晚安
        now_time: datetime = datetime.now()
        if self._config[_gid]["night"]["night_intime"]["enable"]:
            _early_time: int = self._config[_gid]["night"]["night_intime"]["early_time"]
            _late_time: int = self._config[_gid]["night"]["night_intime"]["late_time"]
            
            if not is_NigTimeinRange(_early_time, _late_time, now_time):
                msg = f"现在不能晚安哦，可以晚安的时间为{_early_time}时到第二天早上{_late_time}时~"
                return MessageSegment.text(msg)

        self._init_group_data(gid)

        # 当数据里有过这个人的信息就判断:
        if uid in self._morning[gid]:
            
            # 若开启优质睡眠，则判断在设定时间内是否多次晚安
            if self._config[_gid]["night"]["good_sleep"]["enable"]:
                interval: int = self._config[_gid]["night"]["good_sleep"]["interval"]
                night_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["night_time"], "%Y-%m-%d %H:%M:%S")
                
                if now_time - night_time < timedelta(hours=interval):
                    msg = f"{interval}小时内你已经晚安过了哦~"
                    return MessageSegment.text(msg)
            
            # 若关闭深度睡眠，则判断不在睡觉的时长是否小于设定时长
            if isinstance(self._morning[gid][uid]["daily"]["morning_time"], str):
                if not self._config[_gid]["night"]["deep_sleep"]["enable"]:
                    interval: int = self._config[_gid]["night"]["deep_sleep"]["interval"]
                    morning_time: datetime = datetime.strptime(self._morning[gid][uid]["daily"]["morning_time"], "%Y-%m-%d %H:%M:%S")
                    
                    if now_time - morning_time < timedelta(hours=interval):
                        msg = "睡这么久还不够？现在不能晚安哦~"
                        return MessageSegment.text(msg)

        # 当数据里没有这个人或者前面条件均符合的时候，允许晚安
        num, in_day = self._night_and_update(gid, uid, now_time)
        if isinstance(in_day, int):
            msg = f"晚安成功！你是今晚第{num}个睡觉的{sex_str}！"
        else:
            msg = f"晚安成功！你今天的清醒时长为{in_day}，\n你是今晚第{num}个睡觉的{sex_str}！"
            
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
            
            msg: str = "你的作息数据如下："
            msg += f"\n最近一次早安时间为{get_up_time}"
            msg += f"\n最近一次晚安时间为{sleep_time}"
            
            week_list: List[str] = ["一", "二", "三", "四", "五", "六", "日"]
                
            # When on Monday and now time is later than the latest time of good-morning
            if today == MONDAY:
                hour: int = self.get_refresh_time("morning", "late_time", gid)
                
                if hour != -1 and is_later_oclock(now_time, hour):
                    lastweek_morning_count: int = self._morning[gid][uid]["weekly"]["lastweek_morning_count"]
                    lastweek_night_count: int = self._morning[gid][uid]["weekly"]["lastweek_night_count"]
                    lastweek_sleep: List[int] = self._morning[gid][uid]["weekly"]["lastweek_sleep"]
                    
                    lastweek_lnt_date: datetime = datetime.strptime(self._morning[gid][uid]["weekly"]["lastweek_latest_night_time"], "%Y-%m-%d %H:%M:%S")
                    lastweek_lnt: time = lastweek_lnt_date.time()
                    latest_day: int = lastweek_lnt_date.weekday()
                    
                    lastweek_emt_date: datetime = datetime.strptime(self._morning[gid][uid]["weekly"]["lastweek_earliest_morning_time"], "%Y-%m-%d %H:%M:%S")
                    lastweek_emt: time = lastweek_emt_date.time()
                    earliest_day: int = lastweek_emt_date.weekday()
                    
                    msg += f"\n上周早安了{lastweek_morning_count}次"
                    msg += f"\n上周晚安了{lastweek_night_count}次"
                    msg += f"\n上周睡眠时间为{lastweek_sleep[0]}天{lastweek_sleep[1]}时{lastweek_sleep[2]}分{lastweek_sleep[3]}秒"
                    msg += f"\n上周最晚晚安时间是周{week_list[latest_day]} {lastweek_lnt}"
                    if random.random() > 0.5:
                        msg += f"，{random.choice(the_latest_night_prompt)}"
                        
                    msg += f"\n上周最早早安时间是周{week_list[earliest_day]} {lastweek_emt}"
                    if random.random() > 0.5:
                        msg += f"，{random.choice(the_earliest_morning_prompt)}"
                    
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
            msg: str = "你本周还没有早晚安过呢！暂无数据~"
        
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
            uid: str = ""
            hour: int = self.get_refresh_time("morning", "late_time", gid)
            
            if hour != -1 and is_later_oclock(now_time, hour):
                uid = self._morning[gid]["group_count"]["weekly"]["sleeping_king"]
            
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
            
    def get_refresh_time(self, _time: str, key: str, gid: Optional[str] = None) -> int:
        '''
            Get the time given the specific type(day or night) and key.
            If group id is NOT in specific, return default config
        '''
        self._load_config()
        
        if not isinstance(gid, str):
            # Return the default config
            return self._config["default"][_time][f"{_time}_intime"][key]

        if isinstance(gid, str):
            if gid not in self._config:
                return -1

            return self._config[gid][_time][f"{_time}_intime"][key] if self._config[gid][_time][f"{_time}_intime"]["enable"] else -1
    
    # ------------------------------ Refresh Jobs ------------------------------ #    
    def group_daily_refresh(self, gid: Optional[str] = None) -> None:
        '''
            Reset good-morning/night count of groups of yesterday at the earliest time of daily good-night.
        '''
        self._load_data()
        self._load_config()
        
        if isinstance(gid, str):
            # Refresh for groups in user config
            self._morning[gid]["group_count"]["daily"]["good_morning"] = 0
            self._morning[gid]["group_count"]["daily"]["good_night"] = 0
        else:
            # Refresh for groups in default but not in specific config
            for gid in self._morning:
                if gid not in self._config:
                    self._morning[gid]["group_count"]["daily"]["good_morning"] = 0
                    self._morning[gid]["group_count"]["daily"]["good_night"] = 0
        
        self._save_data()
        
    def weekly_night_refresh(self, mode: RefreshMode, gid: Optional[str] = None) -> None:
        '''
            1. Refresh good-night count of last week at the late time of good-night on Monday or last Sunday.
            2. Reset weekly good-night count at the late time of good-night on Monday or last Sunday.
        '''
        self._load_data()
        self._load_config()
        
        if mode == RefreshMode.DEFAULT_GROUPS:
            # Refresh for groups in default config
            for gid in self._morning:
                if gid not in self._config:
                    for uid, user_items in self._morning[gid].items():
                        # Remember to jump over the key "group_count"
                        if uid == "group_count":
                            continue
                        
                        user_items["weekly"]["lastweek_night_count"] = user_items["weekly"]["weekly_night_count"]
                        user_items["weekly"]["weekly_night_count"] = 0
        
        elif mode == RefreshMode.SPECIFIC_GROUP:
            # Refresh for groups in user config
            if isinstance(gid, str):
                self._morning[gid]["weekly"]["lastweek_night_count"] = self._morning[gid]["weekly"]["weekly_night_count"]
                self._morning[gid]["weekly"]["weekly_night_count"] = 0
               
        self._save_data()
        
    def weekly_sleep_time_refresh(self, mode: RefreshMode, gid: Optional[str] = None) -> None:
        '''
            1. Refresh sleeping time & good-morning count of last week.
            2. Refresh the sleeping king UID of each groups.
            3. Reset weekly sleeping time & good-morning count.
        '''
        self._load_data()
        self._load_config()
        
        if mode == RefreshMode.DEFAULT_GROUPS:
            # Refresh for groups in default config
            for gid in self._morning:
                if gid not in self._config:
                    _max_sleep_time: List[int] = [0, 0, 0, 0]
                    _sleeping_king_uid: str = ""
                    
                    for uid, user_items in self._morning[gid].items():
                        # Remember to jump over the key "group_count"
                        if uid == "group_count": 
                            continue
                        
                        user_items["weekly"]["lastweek_morning_count"] = user_items["weekly"]["weekly_morning_count"]
                        user_items["weekly"]["lastweek_sleep"] = user_items["weekly"]["weekly_sleep"]
                        
                        user_items["weekly"]["weekly_morning_count"] = 0
                        user_items["weekly"]["weekly_sleep"] = [0, 0, 0, 0]
                        
                        # Compare sleeping times, day > hrs > mins > secs
                        if user_items["weekly"]["lastweek_sleep"] > _max_sleep_time:
                            _max_sleep_time = user_items["weekly"]["lastweek_sleep"]
                            _sleeping_king_uid = uid
                            
                    self._morning[gid]["group_count"]["weekly"]["sleeping_king"] = _sleeping_king_uid
        
        elif mode == RefreshMode.SPECIFIC_GROUP:
            # Refresh for groups in user config
            if isinstance(gid, str):
                _max_sleep_time: List[int] = [0, 0, 0, 0]
                _sleeping_king_uid: str = ""
                
                user_items = self._morning[gid].items()
                user_items["weekly"]["lastweek_morning_count"] = user_items["weekly"]["weekly_morning_count"]
                user_items["weekly"]["lastweek_sleep"] = user_items["weekly"]["weekly_sleep"]
                
                user_items["weekly"]["weekly_morning_count"] = 0
                user_items["weekly"]["weekly_sleep"] = [0, 0, 0, 0]
                
                # Compare sleeping times, day > hrs > mins > secs
                if user_items["weekly"]["lastweek_sleep"] > _max_sleep_time:
                    _max_sleep_time = user_items["weekly"]["lastweek_sleep"]
                    _sleeping_king_uid = uid
                        
                self._morning[gid]["group_count"]["weekly"]["sleeping_king"] = _sleeping_king_uid
                    
        self._save_data()
        
    def startup_daily_scheduler(self):
        # For DEFAULT groups to initialize daily schedulers
        hour: int = self.get_refresh_time("night", "early_time")
        scheduler.add_job(
            func=self.group_daily_refresh,
            trigger="cron",
            args=[None],
            id=f"daily_scheduler_default",
            replace_existing=True,
            hour=hour,
            minute=0,
            misfire_grace_time=60
        )
        # For OTHER specific groups to initialize daily schedulers
        for gid in self._config:
            if gid == "default":
                continue

            hour: int = self.get_refresh_time("night", "early_time", gid)
            if hour != -1:
                scheduler.add_job(
                    func=self.group_daily_refresh,
                    trigger="cron",
                    args=[gid],
                    id=f"daily_scheduler_{gid}",
                    replace_existing=True,
                    hour=hour,
                    minute=0,
                    misfire_grace_time=60
                )

    def add_daily_scheduler(self):
        pass
            
    def daily_scheduler(self, mode: SchedulerMode, _gid: Optional[str] = None, _hour: Optional[int] = None) -> None:
        '''
            Run schedulers for refreshing daily good-morning/night counts for ALL groups.
            Replace the existing schedulers.
        '''
        self._load_config()
        
        if mode == SchedulerMode.ALL_GROUP:
            # For DEFAULT groups to initialize daily schedulers
            hour: int = self.get_refresh_time("night", "early_time")
            scheduler.add_job(
                func=self.group_daily_refresh,
                trigger="cron",
                args=[RefreshMode.DEFAULT_GROUPS],
                id=f"daily_scheduler_default",
                replace_existing=True,
                hour=hour,
                minute=0,
                misfire_grace_time=60
            )
            # For OTHER specific groups to initialize daily schedulers
            for gid in self._config:
                if gid == "default":
                    continue

                hour: int = self.get_refresh_time("night", "early_time", gid)
                if hour != -1:
                    scheduler.add_job(
                        func=self.group_daily_refresh,
                        trigger="cron",
                        args=[RefreshMode.SPECIFIC_GROUP, gid],
                        id=f"daily_scheduler_{gid}",
                        replace_existing=True,
                        hour=hour,
                        minute=0,
                        misfire_grace_time=60
                    )
        # Specify the group id but not hour
        elif mode == SchedulerMode.SPECIFIC_GROUP:
            if isinstance(_gid, str):
                hour = self.get_refresh_time("night", "early_time", _gid)
                scheduler.add_job(
                    func=self.group_daily_refresh,
                    trigger="cron",
                    args=[RefreshMode.SPECIFIC_GROUP, _gid],
                    id=f"daily_scheduler_{_gid}",
                    replace_existing=True,
                    hour=hour,
                    minute=0,
                    misfire_grace_time=60
                )
        # Specify the group id and the hour
        elif mode == SchedulerMode.SPECIFIC_GROUP_AND_HOUR:
            if isinstance(_gid, str) and isinstance(_hour, int):
                scheduler.add_job(
                    func=self.group_daily_refresh,
                    trigger="cron",
                    args=[RefreshMode.SPECIFIC_GROUP, _gid],
                    id=f"daily_scheduler_{_gid}",
                    replace_existing=True,
                    hour=_hour,
                    minute=0,
                    misfire_grace_time=60
                )
        else:
            logger.warning(f"Mode: {mode} for daily scheduler is illigal!")
    
    def weekly_night_scheduler(self, mode: SchedulerMode, _gid: Optional[str] = None, _hour: Optional[int] = None) -> None:
        '''
            Run the schedulers for refreshing the weekly good-night time. Replace the existing schedulers.
        '''
        self._load_config()
        
        if mode == SchedulerMode.ALL_GROUP:
            # For DEFAULT groups to initialize daily schedulers
            hour: int = self.get_refresh_time("night", "late_time")
            day_of_week: str = "0" if hour < 12 else "6"    # From Monday to Sunday: 0~6
            scheduler.add_job(
                func=self.weekly_night_refresh,
                trigger="cron",
                args=[RefreshMode.DEFAULT_GROUPS],
                id=f"weekly_night_scheduler_default",
                replace_existing=True,
                hour=hour,
                minute=0,
                day_of_week=day_of_week,
                misfire_grace_time=60
            )
            # For OTHER specific groups to initialize daily schedulers
            for gid in self._config:
                if gid == "default":
                    continue

                hour: int = self.get_refresh_time("night", "late_time", gid)
                day_of_week: str = "0" if hour < 12 else "6"    # From Monday to Sunday: 0~6
                if hour != -1:
                    scheduler.add_job(
                        func=self.weekly_night_refresh,
                        trigger="cron",
                        args=[RefreshMode.SPECIFIC_GROUP, gid],
                        id=f"weekly_night_scheduler_{gid}",
                        replace_existing=True,
                        hour=hour,
                        minute=0,
                        day_of_week=day_of_week,
                        misfire_grace_time=60
                    )
        # Specify the group id but not hour
        elif mode == SchedulerMode.SPECIFIC_GROUP:
            if isinstance(_gid, str):
                hour: int = self.get_refresh_time("night", "late_time", _gid)
                day_of_week: str = "0" if hour < 12 else "6"    # From Monday to Sunday: 0~6
                scheduler.add_job(
                    func=self.weekly_night_refresh,
                    trigger="cron",
                    args=[RefreshMode.SPECIFIC_GROUP, _gid],
                    id=f"weekly_night_scheduler_{_gid}",
                    replace_existing=True,
                    hour=hour,
                    minute=0,
                    day_of_week=day_of_week,
                    misfire_grace_time=60
                )
        # Specify the group id and the hour
        elif mode == SchedulerMode.SPECIFIC_GROUP_AND_HOUR:
            if isinstance(_gid, str) and isinstance(_hour, int):
                day_of_week: str = "0" if _hour < 12 else "6"    # From Monday to Sunday: 0~6
                scheduler.add_job(
                    func=self.weekly_night_refresh,
                    trigger="cron",
                    args=[RefreshMode.SPECIFIC_GROUP, _gid],
                    id=f"weekly_night_scheduler_{_gid}",
                    replace_existing=True,
                    hour=_hour,
                    minute=0,
                    day_of_week=day_of_week,
                    misfire_grace_time=60
                )
        else:
            logger.warning(f"Mode: {mode} for weekly night scheduler is illigal!")
                
    def weekly_sleep_time_scheduler(self, mode: SchedulerMode, _gid: Optional[str] = None, _hour: Optional[int] = None) -> None:
        '''
            Run the schedulers for refreshing the weekly sleeping time. Replace the existing schedulers.
        '''
        if mode == SchedulerMode.ALL_GROUP:
            # For DEFAULT groups to initialize daily schedulers
            hour: int = self.get_refresh_time("morning", "late_time")
            scheduler.add_job(
                func=self.weekly_sleep_time_refresh,
                trigger="cron",
                args=[RefreshMode.DEFAULT_GROUPS],
                id=f"weekly_sleep_time_scheduler_default",
                replace_existing=True,
                hour=hour,
                minute=0,
                day_of_week="0",    # From Monday to Sunday: 0~6
                misfire_grace_time=60
            )
            # For OTHER specific groups to initialize daily schedulers
            for gid in self._config:
                if gid == "default":
                    continue

                hour: int = self.get_refresh_time("morning", "late_time", gid)
                if hour != -1:
                    scheduler.add_job(
                        func=self.weekly_sleep_time_refresh,
                        trigger="cron",
                        args=[RefreshMode.SPECIFIC_GROUP, gid],
                        id=f"weekly_sleep_time_scheduler_{gid}",
                        replace_existing=True,
                        hour=hour,
                        minute=0,
                        day_of_week="0",    # From Monday to Sunday: 0~6
                        misfire_grace_time=60
                    )
        # Specify the group id but not hour
        elif mode == SchedulerMode.SPECIFIC_GROUP:
            if isinstance(_gid, str):
                hour: int = self.get_refresh_time("morning", "late_time", _gid)
                scheduler.add_job(
                    func=self.weekly_sleep_time_refresh,
                    trigger="cron",
                    args=[RefreshMode.SPECIFIC_GROUP, _gid],
                    id=f"weekly_sleep_time_scheduler_{_gid}",
                    replace_existing=True,
                    hour=hour,
                    minute=0,
                    day_of_week="0",    # From Monday to Sunday: 0~6
                    misfire_grace_time=60
                )
        # Specify the group id and the hour
        elif mode == SchedulerMode.SPECIFIC_GROUP_AND_HOUR:
            if isinstance(_gid, str) and isinstance(_hour, int):
                scheduler.add_job(
                    func=self.weekly_sleep_time_refresh,
                    trigger="cron",
                    args=[RefreshMode.SPECIFIC_GROUP, _gid],
                    id=f"weekly_sleep_time_scheduler_{_gid}",
                    replace_existing=True,
                    hour=_hour,
                    minute=0,
                    day_of_week="0",    # From Monday to Sunday: 0~6
                    misfire_grace_time=60
                )
        else:
            logger.warning(f"Mode: {mode} for weekly sleep time scheduler is illigal!")

morning_manager = MorningManager()