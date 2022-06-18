from typing import Coroutine, Union, Any, List
from nonebot import logger
from nonebot import on_command, on_regex
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, GROUP, GROUP_OWNER, GROUP_ADMIN, Message, GroupMessageEvent
from nonebot.params import Depends, CommandArg, RegexMatched, Arg, ArgStr
from nonebot_plugin_apscheduler import scheduler
from .config import Op_Type, Param_Type
from .data_source import morning_manager

__morning_version__ = "v0.3.0a1"
__morning_notes__ = f'''
おはよう！ {__morning_version__}
[早安] 早安/哦哈哟/おはよう
[晚安] 晚安/哦呀斯密/おやすみ
[我的作息] 看看自己的作息
[群友作息] 看看群友的作息
[早晚安设置] 查看当前配置
===== 设置 =====
[早安开启/关闭 xx] 开启/关闭早安的某个配置
[早安设置 xx x] 设置早安配置的数值
[晚安开启/关闭 xx] 开启/关闭晚安的某个配置
[晚安设置 xx x] 设置晚安配置的数值'''.strip()

morning = on_command(cmd="早安", aliases={"哦哈哟", "おはよう"}, permission=GROUP, priority=11)
night = on_command(cmd="晚安", aliases={"哦呀斯密", "おやすみ"}, permission=GROUP, priority=11)
# routine
my_routine = on_command(cmd="我的作息", permission=GROUP, priority=11)
group_routine = on_command(cmd="群友作息", permission=GROUP, priority=11)
# setting
configure = on_command(cmd="早晚安设置", permission=GROUP, priority=10, block=True)
morning_setting = on_regex(pattern=r"^早安(开启|关闭|设置)( (时限|多重起床|超级亢奋)(( \d{1,2}){1,2})?)?$", permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN, priority=10, block=True)
night_setting = on_regex(pattern=r"^晚安(开启|关闭|设置)( (时限|多重起床|超级亢奋)(( \d{1,2}){1,2})?)?$", permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN, priority=10, block=True)
    
@morning.handle()
async def good_morning(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    args = args.extract_plain_text()
    if args == "帮助":
        await morning.finish(__morning_notes__)
            
    uid = event.user_id
    gid = event.group_id
    mem_info = await bot.get_group_member_info(group_id=gid, user_id=uid)
    
    sex = mem_info["sex"]
    if sex == "male":
        sex_str = "少年"
    elif sex == "female":
        sex_str = "少女"
    else:
        sex_str = "群友"

    msg = morning_manager.get_morning_msg(str(gid), str(uid), sex_str)
    await morning.finish(message=msg, at_sender=True)

@night.handle()
async def good_night(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    args = args.extract_plain_text()
    if args == "帮助":
        await night.finish(__morning_notes__)
            
    uid = event.user_id
    gid = event.group_id
    mem_info = await bot.get_group_member_info(group_id=gid, user_id=uid)
    
    sex = mem_info["sex"]
    if sex == "male":
        sex_str = "少年"
    elif sex == "female":
        sex_str = "少女"
    else:
        sex_str = "群友"

    msg = morning_manager.get_night_msg(str(gid), str(uid), sex_str)
    await night.finish(message=msg, at_sender=True)

@my_routine.handle()
async def _(event: GroupMessageEvent):
    gid = str(event.group_id)
    uid = str(event.user_id)
    
    msg = morning_manager.get_my_routine(gid, uid)
    await my_routine.finish(message=msg, at_sender=True)

@group_routine.handle()
async def _(event: GroupMessageEvent):
    gid = str(event.group_id)
    msg = morning_manager.get_group_routine(gid)
    await group_routine.finish(msg)

@configure.handle()
async def _(matcher: Matcher):
    msg = morning_manager.get_current_config()
    await matcher.finish(msg)

def parse_type() -> Coroutine[Any, Any, None]:
    '''
        Parser param type
    '''
    async def _param_parser(matcher: Matcher, state: T_State, input_arg: str = ArgStr("param_type")) -> None:
        arg: str = input_arg
        if arg == "取消":
            await matcher.finish("操作已取消")
        elif arg == "时限":
            state["param_type"] = Param_Type.TIME_LIMIT
        elif arg == "多重起床":
            state["param_type"] = Param_Type.MULTI_GET_UP
        elif arg == "超级亢奋":
            state["param_type"] = Param_Type.SUPER_GET_UP
        elif arg == "优质睡眠":
            state["param_type"] = Param_Type.GOOD_SLEEP
        elif arg == "深度睡眠":
            state["param_type"] = Param_Type.DEEP_SLEEP
        else:
            await matcher.reject_arg("param_type", "输入配置不合法")
    
    return _param_parser

def parse_params() -> Coroutine[Any, Any, None]:
    '''
        Parser extra params
    '''
    async def _params_parser(matcher: Matcher, state: T_State, input_args: str = ArgStr("params")) -> None:
        args: List[str] = input_args.split()
        param_type = state["param_type"]
        if args[0] == "取消":
            await matcher.finish("操作已取消")
        
        if len(args) > 1:
            if param_type != Param_Type.TIME_LIMIT:
                try:
                    state["params"] = int(args[0])
                    await matcher.send("输入参数过多，仅取第一个参数")
                except ValueError:
                    await matcher.reject_arg("params", "输入参数必须是纯数字")
            else:
                try:
                    state["params"] = [int(args[0]), int(args[1])]
                except ValueError:
                    await matcher.reject_arg("params", "输入参数必须是纯数字")
        
        if len(args) == 1:
            if param_type == Param_Type.TIME_LIMIT:
                await matcher.reject_arg("params", "缺少输入参数")
            else:
                try:
                    state["params"] = int(args[0])
                except ValueError:
                    await matcher.reject_arg("params", "输入参数必须是纯数字")
    
    return _params_parser

@morning_setting.handle()
async def _(matcher: Matcher, matched: str = RegexMatched()):
    args: List[str] = matched.split()
    arg_len: int = len(args)

    if args[0][-2:] == "开启":
        matcher.set_arg("op_type", Op_Type.TURN_ON)
    elif args[0][-2:] == "关闭":
        matcher.set_arg("op_type", Op_Type.TURN_OFF)
    elif args[0][-2:] == "设置":
        matcher.set_arg("op_type", Op_Type.SETTING)
    else:
        await matcher.finish("输入指令不合法，可选：早安开启/关闭/设置")
    
    if arg_len > 1:
        if args[1] == "时限":
            matcher.set_arg("param_type", Param_Type.TIME_LIMIT)
        elif args[1] == "多重起床":
            matcher.set_arg("param_type", Param_Type.MULTI_GET_UP)
        elif args[1] == "超级亢奋":
            matcher.set_arg("param_type", Param_Type.SUPER_GET_UP)
        else:
            await matcher.finish("输入配置不合法，可选：时限/多重起床/超级亢奋")
    
    if arg_len > 2:
        if args[1] != "时限":
            matcher.set_arg("params", args[2])
            if arg_len > 3:
                await matcher.send("输入参数过多，仅取第一个参数")
        else:
            if arg_len > 3:
                matcher.set_arg("params", [args[2], args[3]])
            else:
                await matcher.finish("缺少输入参数，配置项【时限】需两个参数")

@morning_setting.got(
    "param_type",
    prompt="请选择配置项，可选：时限/多重起床/超级亢奋，输入取消以取消操作",
    parameterless=[Depends(parse_type())]
)
async def _(state: T_State, _param_type: Param_Type = Arg()):
    _op_type = state["op_type"]
    if _op_type == Op_Type.TURN_ON:
        msg = morning_manager.morning_switch(_param_type.value, True)
        await morning_setting.finish(msg)
    elif _op_type == Op_Type.TURN_OFF:
        msg = morning_manager.morning_switch(_param_type.value, False)
        await morning_setting.finish(msg)

@morning_setting.got(
    "params",
    prompt="请输入设置参数，时限配置项请输入允许的最早/晚的睡觉时间（空格间隔），其余配置项请输入一个时间间隔，输入取消以取消操作",
    parameterless=[Depends(parse_params())]
)
async def _(state: T_State, _param: Union[int, List[int]] = Arg()):
    _param_type = state["param_type"]
    
    msg = morning_manager.morning_config(_param_type.value, *_param)
    await morning_setting.finish(msg)
    
@night_setting.handle()
async def _(matcher: Matcher, matched: str = RegexMatched()):
    args: List[str] = matched.split()
    arg_len: int = len(args)

    if args[0][-2:] == "开启":
        matcher.set_arg("op_type", Op_Type.TURN_ON)
    elif args[0][-2:] == "关闭":
        matcher.set_arg("op_type", Op_Type.TURN_OFF)
    elif args[0][-2:] == "设置":
        matcher.set_arg("op_type", Op_Type.SETTING)
    else:
        await matcher.finish("输入指令不合法，可选：早安开启/关闭/设置")
    
    if arg_len > 1:
        if args[1] == "时限":
            matcher.set_arg("param_type", Param_Type.TIME_LIMIT)
        elif args[1] == "优质睡眠":
            matcher.set_arg("param_type", Param_Type.GOOD_SLEEP)
        elif args[1] == "深度睡眠":
            matcher.set_arg("param_type", Param_Type.DEEP_SLEEP)
        else:
            await matcher.finish("输入配置不合法，可选：时限/优质睡眠/深度睡眠")
    
    if arg_len > 2:
        if args[1] != "时限":
            matcher.set_arg("params", args[2])
            if arg_len > 3:
                await matcher.send("输入参数过多，仅取第一个参数")
        else:
            if arg_len > 3:
                matcher.set_arg("params", [args[2], args[3]])
            else:
                await matcher.finish("缺少输入参数，配置项【时限】需两个参数")

@night_setting.got(
    "param_type",
    prompt="请选择配置项，可选：时限/优质睡眠/深度睡眠，输入取消以取消操作",
    parameterless=[Depends(parse_type())]
)
async def _(state: T_State, _param_type: Param_Type = Arg()):
    _op_type = state["op_type"]
    if _op_type == Op_Type.TURN_ON:
        msg = morning_manager.night_switch(_param_type.value, True)
        await night_setting.finish(msg)
    elif _op_type == Op_Type.TURN_OFF:
        msg = morning_manager.night_switch(_param_type.value, False)
        await night_setting.finish(msg)

@night_setting.got(
    "params",
    prompt="请输入设置参数，时限配置项请输入允许的最早/晚的睡觉时间（空格间隔），其余配置项请输入一个时间间隔，输入取消以取消操作",
    parameterless=[Depends(parse_params())]
)
async def _(state: T_State, _param: Union[int, List[int]] = Arg()):
    _param_type: Param_Type = state["param_type"]
    
    logger.info(_param_type.value)
    logger.info(_param)
    
    msg = morning_manager.night_config(_param_type.value, *_param)
    await night_setting.finish(msg)
        
# 重置一天的早安晚安计数
@scheduler.scheduled_job("cron", hour=0, minute=0, misfire_grace_time=60)
async def _():
    morning_manager.reset_data()
    logger.info("早晚安已刷新！")