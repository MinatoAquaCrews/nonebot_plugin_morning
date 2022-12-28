from datetime import datetime, timedelta, date
from typing import Union, Tuple, List, Dict
import json

mor_switcher: Dict[str, str] = {
    "时限": "morning_intime",
    "多重起床": "multi_get_up",
    "超级亢奋": "super_get_up"
}

nig_switcher: Dict[str, str] = {
    "时限": "night_intime",
    "优质睡眠": "good_sleep",
    "深度睡眠": "deep_sleep"
}

morning_prompt: List[str] = [
    "早安！",
    "おはよう！",
    "早安～",
    "哦哈哟！"
]

the_latest_night_prompt: List[str] = [
    "是加班到这么晚吗？",
    "睡这么晚不怕猝死吗？",
    "想什么呢睡不着？是在想我吗？"
]

the_earliest_morning_prompt: List[str] = [
    "懒狗怎么起这么早？",
    "早起的鸟儿有虫吃！"
]


class DateTimeEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")

        return json.JSONEncoder.default(self, obj)


def is_later(time1: Union[str, datetime], time2: Union[str, datetime]) -> bool:
    '''
        Return True if time #1 is later than time #2 of time part.
    '''
    _time1: datetime = datetime.strptime(
        time1, "%Y-%m-%d %H:%M:%S") if isinstance(time1, str) else time1
    _time2: datetime = datetime.strptime(
        time2, "%Y-%m-%d %H:%M:%S") if isinstance(time2, str) else time2

    return _time1.time() > _time2.time()


def datetime2timedelta(_datetime: datetime) -> timedelta:
    return _datetime - datetime(_datetime.year, _datetime.month, _datetime.day, 0, 0, 0)


def is_later_oclock(now_time: datetime, oclock: int) -> bool:
    return datetime2timedelta(now_time) > timedelta(hours=oclock)


def is_MorTimeinRange(early_time: int, late_time: int, now_time: datetime) -> bool:
    '''
        判断早安时间是否在范围内
        - early_time: 较早的开始时间
        - late_time: 较晚的结束时间
    '''
    return timedelta(hours=early_time) < datetime2timedelta(now_time) < timedelta(hours=late_time)


def is_NigTimeinRange(early_time: int, late_time: int, now_time: datetime) -> bool:
    '''
        判断晚安时间是否在范围内，注意次日判断
        - early_time: 较早的开始时间
        - late_time: 较晚的结束时间
    '''
    return datetime2timedelta(now_time) > timedelta(hours=early_time) or datetime2timedelta(now_time) < timedelta(hours=late_time)


def total_seconds2tuple_time(secs: int) -> Tuple[int, int, int, int]:
    days: int = secs // (3600 * 24)
    hours: int = (secs - days * 3600 * 24) // 3600
    minutes: int = (secs - days * 3600 * 24 - hours * 3600) // 60
    seconds: int = secs - days * 3600 * 24 - hours * 3600 - minutes * 60

    return days, hours, minutes, seconds


def sleeptime_update(_lold: List[int], _sleep: timedelta) -> List[int]:
    '''
        Add a timedelta to another one
        - _lold: days, hrs, mins, secs
    '''
    t_old: timedelta = timedelta(
        days=_lold[0], hours=_lold[1], minutes=_lold[2], seconds=_lold[3])
    t_new: timedelta = t_old + _sleep

    days, hours, minutes, seconds = total_seconds2tuple_time(
        int(t_new.total_seconds()))

    return [days, hours, minutes, seconds]

# A compatible transfer from old version format of data.json into new version's(morning.json)


def morning_json_update(_ofile: Dict[str, Dict[str, Dict[str, int]]]) -> Dict[str, Dict[str, Dict[str, Dict[str, Union[str, int, List[int]]]]]]:
    _nfile: Dict[str, Dict[str,
                           Dict[str, Dict[str, Union[str, int, List[int]]]]]] = dict()

    for gid in _ofile:
        # Create groups' info
        _nfile.update({
            gid: {
                "group_count": {
                    "daily": {
                        "good_morning": _ofile[gid]["today_count"]["morning"],
                        "good_night": _ofile[gid]["today_count"]["night"]
                    },
                    "weekly": {
                        "sleeping_king": ""
                    }
                }
            }
        })
        for uid in _ofile[gid]:
            if uid == "today_count":
                continue
            else:
                # Create users' info
                _nfile[gid].update({
                    uid: {
                        "daily": {
                            "morning_time": _ofile[gid][uid]["get_up_time"],
                            "night_time": _ofile[gid][uid]["sleep_time"]
                        },
                        "weekly": {
                            "weekly_morning_count": 0,
                            "weekly_night_count": 0,
                            "weekly_sleep": [0, 0, 0, 0],
                            "lastweek_morning_count": 0,
                            "lastweek_night_count": 0,
                            "lastweek_sleep": [0, 0, 0, 0],
                            "lastweek_earliest_morning_time": _ofile[gid][uid]["get_up_time"],
                            "lastweek_latest_night_time": _ofile[gid][uid]["sleep_time"]
                        },
                        "total": {
                            "morning_count": _ofile[gid][uid]["morning_count"],
                            "night_count": _ofile[gid][uid]["night_count"],
                            "total_sleep": [0, 0, 0, 0]
                        }
                    }
                })

    return _nfile
