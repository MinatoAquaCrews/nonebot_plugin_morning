from typing import Coroutine, Any, List
from nonebot import logger, require, on_command, on_regex
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, GROUP, GROUP_OWNER, GROUP_ADMIN, Message, MessageSegment, GroupMessageEvent
from nonebot.params import Depends, CommandArg, RegexMatched, ArgStr
from .config import driver
from .data_source import morning_manager

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

__morning_version__ = "v0.3.0a5"
__morning_notes__ = f'''
おはよう！ {__morning_version__}
[早安] 早安/哦哈哟/おはよう
[晚安] 晚安/哦呀斯密/おやすみ
[我的作息] 看看自己的作息
[群友作息] 看看群友的作息
[早晚安设置] 查看当前配置
------- 设置 -------
[早安开启/关闭 xx] 开启/关闭早安的某个配置
[早安设置 xx x] 设置早安配置的数值
[晚安开启/关闭 xx] 开启/关闭晚安的某个配置
[晚安设置 xx x] 设置晚安配置的数值'''.strip()

morning = on_command(cmd="早安", aliases={"哦哈哟", "おはよう"}, permission=GROUP, priority=12)
night = on_command(cmd="晚安", aliases={"哦呀斯密", "おやすみ"}, permission=GROUP, priority=12)

# routine
my_routine = on_command(cmd="我的作息", permission=GROUP, priority=12)
group_routine = on_command(cmd="群友作息", permission=GROUP, priority=12)

# setting
configure = on_command(cmd="早安设置", aliases={"晚安设置", "早晚安设置"}, permission=GROUP, priority=11, block=True)
morning_setting = on_regex(pattern=r"^早安(开启|关闭|设置)( (时限|多重起床|超级亢奋)(( \d{1,2}){1,2})?)?$", permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN, priority=10, block=True)
night_setting = on_regex(pattern=r"^晚安(开启|关闭|设置)( (时限|优质睡眠|深度睡眠)(( \d{1,2}){1,2})?)?$", permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN, priority=10, block=True)

@morning.handle()
async def good_morning(bot: Bot, matcher: Matcher, event: GroupMessageEvent, args: Message = CommandArg()):
    args = args.extract_plain_text()
    if args == "帮助":
        await matcher.finish(__morning_notes__)
            
    uid = event.user_id
    gid = event.group_id
    mem_info = await bot.call_api("get_group_member_info", group_id=gid, user_id=uid)
    
    sex = mem_info["sex"]
    if sex == "male":
        sex_str = "少年"
    elif sex == "female":
        sex_str = "少女"
    else:
        sex_str = "群友"

    msg = morning_manager.get_morning_msg(str(gid), str(uid), sex_str)
    await matcher.finish(message=msg, at_sender=True)

@night.handle()
async def good_night(bot: Bot, matcher: Matcher, event: GroupMessageEvent, args: Message = CommandArg()):
    args = args.extract_plain_text()
    if args == "帮助":
        await matcher.finish(__morning_notes__)
            
    uid: int = event.user_id
    gid: int = event.group_id
    mem_info = await bot.call_api("get_group_member_info", group_id=gid, user_id=uid)
    
    sex = mem_info["sex"]
    if sex == "male":
        sex_str = "少年"
    elif sex == "female":
        sex_str = "少女"
    else:
        sex_str = "群友"

    msg = morning_manager.get_night_msg(str(gid), str(uid), sex_str)
    await matcher.finish(message=msg, at_sender=True)

@my_routine.handle()
async def _(matcher: Matcher, event: GroupMessageEvent):
    gid = str(event.group_id)
    uid = str(event.user_id)
    
    msg = morning_manager.get_my_routine(gid, uid)
    await matcher.finish(message=msg, at_sender=True)

@group_routine.handle()
async def _(bot: Bot, matcher: Matcher, event: GroupMessageEvent):
    gid = event.group_id
    morning_count, night_count, uid = morning_manager.get_group_routine(str(gid))
    msg: str = f"今天已经有{morning_count}位群友早安了，{night_count}位群友晚安了~"
    
    if uid:
        mem_info = await bot.call_api("get_group_member_info", group_id=gid, user_id=int(uid))
        nickname: str = mem_info["card"] if mem_info["card"] else mem_info["nickname"]
        msg += f"\n上周睡觉大王是群友：{nickname}，再接再厉～"
    
    await matcher.finish(MessageSegment.text(msg))

@configure.handle()
async def _(matcher: Matcher):
    msg = morning_manager.get_current_config()
    await matcher.finish(msg)

def parse_item(_key: str) -> Coroutine[Any, Any, None]:
    '''
        Parser setting item
    '''
    async def _item_parser(matcher: Matcher, arg: str = ArgStr("item")) -> None:
        if arg == "取消":
            await matcher.finish("操作已取消")
        
        if arg == "时限" or arg == "多重起床" or arg == "超级亢奋" or \
            arg == "优质睡眠" or arg == "深度睡眠":
            matcher.set_arg("item", arg)
        else:
            if _key == "morning":
                await matcher.reject_arg("item", "输入配置不合法，可选时限/多重起床/超级亢奋")
            else:
                await matcher.reject_arg("item", "输入配置不合法，可选时限/优质睡眠/深度睡眠")
    
    return _item_parser

def parse_params() -> Coroutine[Any, Any, None]:
    '''
        Parser extra params
    '''
    async def _params_parser(matcher: Matcher, input_args: str = ArgStr("param1")) -> None:
        args: List[str] = input_args.split()
        
        logger.info(f"check in _params_parser: {args}")
        
        if args[0] == "取消":
            await matcher.finish("操作已取消")
        
        item = matcher.get_arg("item", None)
        if not item:
            await matcher.finish("配置出错，操作已取消")
            
        if item != "时限":
            if len(args) > 1:
                await matcher.send("输入参数过多，仅取第一个参数")
            
            try:
                _ = int(args[0])
            except ValueError:
                await matcher.reject_arg("param1", "输入参数必须是纯数字")
                
            matcher.set_arg("param1", args[0])
            matcher.set_arg("param2", 0)
        else:
            if len(args) == 1:
                await matcher.reject_arg("param1", "缺少输入参数")
            else:
                try:
                    _ = int(args[0])
                    _ = int(args[1])
                except ValueError:
                    await matcher.send("输入参数必须是纯数字，请重新输入")
                
                matcher.set_arg("param1", args[0])
                matcher.set_arg("param2", args[1])

    return _params_parser

@morning_setting.handle()
async def _(matcher: Matcher, matched: str = RegexMatched()):
    args: List[str] = matched.split()
    arg_len: int = len(args)
    
    if args[0][-2:] == "开启" or args[0][-2:] == "关闭" or args[0][-2:] == "设置":
        matcher.set_arg("op_type", args[0][-2:])
        if args[0][-2:] == "开启" or args[0][-2:] == "关闭":
            matcher.set_arg("param1", 0)   # Ignore state["param1"] and state["param2"]
            matcher.set_arg("param2", 0)
    else:
        await matcher.finish("输入指令不合法，可选：开启/关闭/设置")
    
    if arg_len > 1:
        if args[1] == "时限" or args[1] == "多重起床" or args[1] == "超级亢奋":
            matcher.set_arg("item", args[1])
        else:
            await matcher.finish("输入配置不合法，可选：时限/多重起床/超级亢奋")
    
    # Params are numbers, but store in state in string
    if arg_len > 2:
        if args[1] != "时限":
            try:
                _ = int(args[2])
            except ValueError:
                await matcher.send("输入参数必须是纯数字，请重新输入")

            matcher.set_arg("param1", args[2])
            matcher.set_arg("param2", 0)
            if arg_len > 3:
                await matcher.send("输入参数过多，仅取第一个参数")
        else:
            if arg_len < 4:
                await matcher.finish("缺少输入参数，配置项【时限】需两个参数")
            else:
                if arg_len > 4:
                    await matcher.send("输入参数过多，仅取前两个参数")
                try:
                    _ = int(args[2])
                    _ = int(args[3])
                except ValueError:
                    await matcher.send("输入参数必须是纯数字，请重新输入")
                
                matcher.set_arg("param1", args[2])
                matcher.set_arg("param2", args[3])

@morning_setting.got(
    "item",
    prompt="请选择配置项，可选：时限/多重起床/超级亢奋，输入取消以取消操作",
    parameterless=[Depends(parse_item("morning"))]
)
async def handle_skip(matcher: Matcher):
    matcher.skip()

@morning_setting.got(
    "param1",
    prompt="请输入设置参数，时限配置项请输入允许的最早/晚的睡觉时间（空格间隔），其余配置项请输入一个时间，输入取消以取消操作",
    parameterless=[Depends(parse_params())]
)
async def _(matcher: Matcher):
    _op_type: str = matcher.get_arg("op_type", None)
    _item: str = matcher.get_arg("item", None)
    _param1: str = matcher.get_arg("param1", 0)
    _param2: str = matcher.get_arg("param2", 0)
    
    if _op_type == "设置":
        msg = morning_manager.morning_config(_item, int(_param1), int(_param2))
    elif _op_type == "开启":
        msg = morning_manager.morning_switch(_item, True)
    elif _op_type == "关闭":
        msg = morning_manager.morning_switch(_item, False)
        
    await morning_setting.finish(msg)
    
@night_setting.handle()
async def _(matcher: Matcher, matched: str = RegexMatched()):
    args: List[str] = matched.split()
    arg_len: int = len(args)
    
    logger.info(f"check in handle: {args}")

    if args[0][-2:] == "开启" or args[0][-2:] == "关闭" or args[0][-2:] == "设置":
        matcher.set_arg("op_type", args[0][-2:])
        if args[0][-2:] == "开启" or args[0][-2:] == "关闭":
            matcher.set_arg("param1", 0)   # Ignore state["param1"] and state["param2"]
            matcher.set_arg("param2", 0)
    else:
        await matcher.finish("输入指令不合法，可选：开启/关闭/设置")
    
    if arg_len > 1:
        if args[1] == "时限" or args[1] == "优质睡眠" or args[1] == "深度睡眠":
            matcher.set_arg("item", args[1])
        else:
            await matcher.finish("输入配置不合法，可选：时限/优质睡眠/深度睡眠")
            
    # Params are numbers, but store in state in string
    if arg_len > 2:
        if args[1] != "时限":
            try:
                _ = int(args[2])
            except ValueError:
                await matcher.send("输入参数必须是纯数字，请重新输入")

            matcher.set_arg("param1", args[2])
            matcher.set_arg("param2", 0)
            if arg_len > 3:
                await matcher.send("输入参数过多，仅取第一个参数")
        else:
            if arg_len < 4:
                await matcher.finish("缺少输入参数，配置项【时限】需两个参数")
            else:
                if arg_len > 4:
                    await matcher.send("输入参数过多，仅取前两个参数")
                try:
                    _ = int(args[2])
                    _ = int(args[3])
                except ValueError:
                    await matcher.send("输入参数必须是纯数字，请重新输入")
                
                matcher.set_arg("param1", args[2])
                matcher.set_arg("param2", args[3])
                
@night_setting.got(
    "item",
    prompt="请选择配置项，可选：时限/优质睡眠/深度睡眠，输入取消以取消操作",
    parameterless=[Depends(parse_item("night"))]
)
async def handle_skip(matcher: Matcher):
    matcher.skip()

@night_setting.got(
    "param1",
    prompt="请输入设置参数，时限配置项请输入允许的最早/晚的睡觉时间（空格间隔），其余配置项请输入一个时间，输入取消以取消操作",
    parameterless=[Depends(parse_params())]
)
async def _(matcher: Matcher):
    _op_type: str = matcher.get_arg("op_type", None)
    _item: str = matcher.get_arg("item", None)
    _param1: str = matcher.get_arg("param1", 0)
    _param2: str = matcher.get_arg("param2", 0)
    
    if _op_type == "设置":
        msg = morning_manager.night_config(_item, int(_param1), int(_param2))
    elif _op_type == "开启":
        msg = morning_manager.night_switch(_item, True)
    elif _op_type == "关闭":
        msg = morning_manager.night_switch(_item, False)
    
    await night_setting.finish(msg)

# 每日最早晚安时间，重置昨日早晚安计数
@driver.on_startup
async def daily_refresh():
    morning_manager.daily_scheduler()
    logger.info("每日早晚安定时刷新任务已启动！")

# 每周一零点统计部分周数据
@scheduler.scheduled_job("cron", hour=0, minute=0, day_of_week="1", misfire_grace_time=60)
async def monday_refresh():
    morning_manager.weekly_night_refresh()
    logger.info("每周晚安已刷新！")

# 每周一最晚早安时间，统计上周睡眠时间、早安并重置
@driver.on_startup
async def weekly_refresh():
    morning_manager.weekly_sleep_time_scheduler()
    logger.info("每周睡眠时间定时刷新任务已启动！")