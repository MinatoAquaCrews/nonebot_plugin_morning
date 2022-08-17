<div align="center">

# Good Morning

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
_🌈 おはよう！ 🌈_
<!-- prettier-ignore-end -->

</div>
<p align="center">
  
  <a href="https://github.com/MinatoAquaCrews/nonebot_plugin_morning/blob/beta/LICENSE">
    <img src="https://img.shields.io/github/license/MinatoAquaCrews/nonebot_plugin_morning?color=blue">
  </a>
  
  <a href="https://github.com/nonebot/nonebot2">
    <img src="https://img.shields.io/badge/nonebot2-2.0.0b3+-green">
  </a>
  
  <a href="https://github.com/MinatoAquaCrews/nonebot_plugin_morning/releases/tag/v0.3.0a4">
    <img src="https://img.shields.io/github/v/release/MinatoAquaCrews/nonebot_plugin_morning?color=orange&include_prereleases">
  </a>

  <a href="https://www.codefactor.io/repository/github/MinatoAquaCrews/nonebot_plugin_morning">
    <img src="https://img.shields.io/codefactor/grade/github/MinatoAquaCrews/nonebot_plugin_morning/main?color=red">
  </a>
  
</p>

## 版本

v0.3.0a4

⚠ 适配nonebot2-2.0.0beta.3+

[更新日志](https://github.com/MinatoAquaCrews/nonebot_plugin_morning/releases/tag/v0.3.0a4)

## 安装

1. 通过`pip`或`nb`安装；

2. 用户数据`data.json`及早晚安配置文件`config.json`位于`./resource`下，可在`env`内设置`MORNING_PATH`更改：

    ```python
    MORNING_PATH="your-path-to-resource"  # For example: ./my_data/morning_resource/
    ```

## 功能

1. 和Bot说早晚安，记录睡眠时间，培养良好作息；

2. 群管及超管可设置早安时限、晚安时限、优质睡眠、深度睡眠等，参见规则配置；

3. 分群管理群友作息，群友的早晚安数据会记录至`morning.json`内，形如：

    ``` python
    {
        "123456789": {                  # 群号
            "today_count": {            # 群统计
                "morning": 1,           # 群早安次数
                "night": 0              # 群晚安次数
            },
            "123456": {                 # 群友QQ号
                "get_up_time": "1234",  # 群友起床时间
                "morning_count": 3,     # 群友共早安次数
                "sleep_time": "1234",   # 群友睡觉时间
                "night_count": 3        # 群友共晚安次数
            },
            "654321": {
                "get_up_time": "4321",
                "morning_count": 5,
                "sleep_time": "4321",
                "night_count": 5 
            }           
        }
    }
    ```

4. おはよう！🌈

## 命令

1. 早晚安：[早安/晚安]，记录睡眠时间；

2. 查看我的作息：[我的作息]；

3. 查看群友作息：[群友作息]，看看今天几个人睡觉或起床了；

4. 查看当前安早晚安配置（规则）：[早晚安设置]；

5. [管理员或超管] 设置命令

    - 开启/关闭某个配置：早安/晚安开启/关闭某项功能；

    - 早安/晚安设置：设置功能的参数；

    - 详见规则配置；

## 规则配置

`confg.json`文件已默认写入下述配置，当其不存在时则尝试从仓库中下载预置的配置文件：

⚠ 不确保下载成功

``` python
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
    
    - [早安开启 xx] 开启某个配置选项，配置项有：时限/多重起床/超级亢奋；例如，[早安开启 多重起床]；
    
    - [早安关闭 xx] 关闭某个配置选项，配置项有：时限/多重起床/超级亢奋；例如，[早安关闭 时限]；
    
    - [早安设置 xx x] 设置某个配置的参数，配置项有：时限/多重起床/超级亢奋；（x可选值为0到24的整数）
      
		⚠ 配置参数时，可一次性输入规定的参数，也可通过引导一步步设置
	  
		⚠ 当**设置时限**时需要两个参数，命令为：[早安设置 时限 x y]，其余只需一个参数，例如，[早安设置 超级亢奋 5]

		⚠ 配置项具体含义参见上述规则配置
		
		⚠ 当配置某个选项时，会自动启用该选项

3. 晚安配置
    
    - [晚安开启 xx] 开启某个配置选项，配置项有：时限/优质睡眠/深度睡眠；例如，[晚安开启 优质睡眠]；
    
    - [晚安关闭 xx] 关闭某个配置选项，配置项有：时限/优质睡眠/深度睡眠；例如，[晚安关闭 深度睡眠]；
    
    - [晚安设置 xx x] 设置某个配置的参数，配置项有：时限/优质睡眠/深度睡眠；（x可选值为0到24的整数）
      
		⚠ 注意事项参考早安配置

## 本插件改自

[hoshinobot-good_morning](https://github.com/azmiao/good_morning)