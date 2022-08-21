from datetime import datetime, timedelta

class clocktime(timedelta):
    
    def __init__(self, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        self._hours = hours
        self._minutes = minutes
    
    @property
    def hours(self):
        """hours"""
        return self._hours
    
    @property
    def minutes(self):
        """minutes"""
        return self._minutes
    

def is_later(_time1: str, _time2: str) -> bool:
    '''
        Return True if time #1 is later 24 hours than time #2
    '''
    return datetime.strptime(_time1, "%Y-%m-%d %H:%M:%S") - datetime.strptime(_time2, "%Y-%m-%d %H:%M:%S") > timedelta(hours=24)
    
def is_MorTimeinRange(early_time: int, late_time: int, now_time: datetime) -> bool:
    '''
        判断早安时间是否在范围内
        - early_time: 较早的开始时间
        - late_time: 较晚的结束时间
    '''
    pass_time = now_time - datetime(now_time.year, now_time.month, now_time.day, 0, 0, 0)

    return timedelta(hours=early_time) < pass_time < timedelta(hours=late_time)

def is_NigTimeinRange(early_time: int, late_time: int, now_time: datetime) -> bool:
    '''
        判断晚安时间是否在范围内，注意次日判断
        - early_time: 较早的开始时间
        - late_time: 较晚的结束时间
    '''
    pass_time = now_time - datetime(now_time.year, now_time.month, now_time.day, 0, 0, 0)
    
    return pass_time > timedelta(hours=early_time) or pass_time < timedelta(hours=late_time)

def is_TimeinInterval(_datetime: str, now_time: datetime, interval: int) -> bool:
    '''
        1. 判断是否多次早安，上次早安时间和现在时间相差不超过interval，True则成立。此时，_datetime = good_morning_time
        2. 判断是否超级亢奋，上次晚安时间和现在时间相差不超过interval，True则成立。此时，_datetime = good_night_time
        3. 判断是否优质睡眠，上次晚安时间和现在时间相差不超过interval，True则成立
        4. 判断是否深度睡眠，上次早安时间和现在时间相差不超过interval，True则成立
        5. 判断早安是否隔日(interval=24)，例如存在此情况：
            在01-01 23:00:00 晚安
            在01-03 07:00:00 早安
            True: 则未隔日
    '''
    return now_time - datetime.strptime(_datetime, '%Y-%m-%d %H:%M:%S') < timedelta(hours=interval)

#TODO: A compatible transfer from old morning data to new version's

__all__ = [
    clocktime, is_later, is_MorTimeinRange, is_NigTimeinRange, is_TimeinInterval
]

if __name__ == "__main__":
    c1 = clocktime(days=1, hours=2, minutes=3, seconds=4)
    c2 = clocktime(days=0, hours=3, minutes=4, seconds=5)
    print(c1.hours)
