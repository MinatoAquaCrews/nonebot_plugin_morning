<div align="center">

# Good Morning

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
_🌈 おはよう！ 🌈_
<!-- prettier-ignore-end -->

</div>
<p align="center">
  
  <a href="https://github.com/KafCoppelia/nonebot_plugin_morning/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-informational">
  </a>
  
  <a href="https://github.com/nonebot/nonebot2">
    <img src="https://img.shields.io/badge/nonebot2-2.0.0alpha.16-green">
  </a>
  
  <a href="">
    <img src="https://img.shields.io/badge/release-v0.1.1-orange">
  </a>
  
</p>

</p>

## 版本

v0.1.1

⚠ 适配nonebot2-2.0.0alpha.16；

👉 适配beta.1版本参见[beta.1分支](https://github.com/KafCoppelia/nonebot_plugin_morning/tree/beta.1)

[更新日志](https://github.com/KafCoppelia/nonebot_plugin_morning/releases/tag/v0.1.1)

## 安装

1. 通过`pip`或`nb`安装，版本指定`0.1.1`；

2. 用户数据`data.json`及早晚安配置文件`config.json`位于`./resource`下，可在`env`内设置`MORNING_PATH`更改：

```python
MORNING_PATH="your-path-to-resource"
```

## 功能

1. 和Bot说早晚安，记录睡眠时间，培养良好作息；

2. 群管及超管可设置早安时限、晚安时限、优质睡眠、深度睡眠等；

3. 分群管理群友作息；

4. おはよう！🌈

## 命令

1. 早晚安：早安/晚安，记录睡眠时间；

2. 查看我的作息：我的作息；

3. 查看群友作息：群友作息，看看今天几个人睡觉或起床了；

4. 查看配置当前安晚安规则：早晚安设置；

5. [群管或群主或超管] 设置命令

    - 开启/关闭某个配置： 早安/晚安开启/关闭某项功能；

    - 早安/晚安设置：设置功能的参数；

    - 详见规则配置；

## 规则配置

**新增** `confg.json`文件已默认写入下述预置配置，当其不存在时则默认下载仓库的预置配置文件：

```python
{
    "morning": {
        "get_up_intime": {      # 是否只能在规定时间起床
            "enable": true,     # 默认开启，若关闭则下面两项无效
            "early_time": 6,    # 允许的最早的起床时间，默认早上6点
            "late_time": 12     # 允许的最晚的起床时间，默认中午12点
        },
        "multi_get_up": {       # 是否允许多次起床
            "enable": false,    # 默认不允许，若允许则下面一项无效
            "interval": 6       # 两次起床间隔的时间，小于这个时间就不允许起床
        },
        "super_get_up": {       # 是否允许超级亢奋
            "enable": false,    # 默认不允许，若允许则下面一项无效
            "interval": 3       # 这次起床和上一次睡觉的时间间隔，小于这个时间就不允许起床，不怕猝死？给我睡！
        }
    },
    "night": {
        "sleep_intime": {       # 是否只能在规定时间睡觉
            "enable": true,     # 默认开启，若关闭则下面两项无效
            "early_time": 21,   # 允许的最早的睡觉时间，默认晚上21点
            "late_time": 6      # 允许的最晚的睡觉时间，默认次日早上6点
        },
        "good_sleep": {         # 是否开启优质睡眠
            "enable": true,     # 默认开启，若关闭则下面一项无效
            "interval": 6       # 两次睡觉间隔的时间，小于这个时间就不允许睡觉
        },
        "deep_sleep": {         # 是否允许深度睡眠
            "enable": false,    # 默认不允许，若允许则下面一项无效
            "interval": 3       # 这次睡觉和上一次起床的时间间隔，小于这个时间就不允许睡觉，睡个锤子，快起床！
        }
    }
}
```

1. 默认配置（如上）

    - 早安：

      是否要求规定时间内起床：是

      是否允许连续多次起床：否

      是否允许超级亢奋(即睡眠时长很短)：否

    - 晚安：

      是否要求规定时间内睡觉：是

      是否开启优质睡眠：是
      
      是否允许深度睡眠(即清醒时长很短)：否

2. 早安配置
    
    - [早安开启 xx] 开启某个配置选项，xx可选值目前有[时限|多重起床|超级亢奋]；
    
    - [早安关闭 xx] 关闭某个配置选项，xx可选值目前有[时限|多重起床|超级亢奋]；
    
    - [早安设置 xx x] 设置某个配置的参数，xx可选值目前有[时限|多重起床|超级亢奋]，x可选值为0到24的整数；
      
      ※ 当设置时限时需要两个参数，命令为：[早安设置 时限 x y]，当不是时限时只需一个参数，命令为：[早安设置 xx x]

3. 晚安配置
    
    - [晚安开启 xx] 开启某个配置选项，xx可选值目前有[时限|优质睡眠|深度睡眠]；
    
    - [晚安关闭 xx] 关闭某个配置选项，xx可选值目前有[时限|优质睡眠|深度睡眠]；
    
    - [晚安设置 xx x] 设置某个配置的参数，xx可选值目前有[时限|优质睡眠|深度睡眠]，x可选值为0到24的整数；
      
      ※ 当设置时限时需要两个参数，命令为：[晚安设置 时限 x y]，当不是时限时只需一个参数，命令为：[晚安设置 xx x]

## 本插件改自

[hoshinobot-good_morning](https://github.com/azmiao/good_morning)

1. 修改代码结构；

2. 修改部分配置名称、功能，修改群组数据储存格式；

3. 参考并修改配置部分README；