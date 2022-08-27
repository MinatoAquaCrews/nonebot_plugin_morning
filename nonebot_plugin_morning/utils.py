from datetime import datetime, timedelta, date
from typing import Union, Tuple, List
import json

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
    _time1: datetime = datetime.strptime(time1, "%Y-%m-%d %H:%M:%S") if isinstance(time1, str) else time1
    _time2: datetime = datetime.strptime(time2, "%Y-%m-%d %H:%M:%S") if isinstance(time2, str) else time2
    
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
    '''
    t_old: timedelta = timedelta(days=_lold[0], hours=_lold[1], minutes=_lold[2], seconds=_lold[3])
    t_new: timedelta = t_old + _sleep
    
    days, hours, minutes, seconds = total_seconds2tuple_time(int(t_new.total_seconds()))
    
    return [days, hours, minutes, seconds]