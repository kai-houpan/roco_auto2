# 洛克王国：世界 — 自动孵蛋工具设计文档

> 版本: 1.3
> 日期: 2026-05-14
> 状态: 开发中

---

## 1. 项目概述

### 1.1 目标

开发一款 Windows 桌面工具，自动化完成游戏《洛克王国：世界》中的孵蛋及咕噜球契约流程。用户通过 GUI 面板配置蛋种任务队列和咕噜球类型后，程序在游戏孵蛋界面循环执行"放蛋 → 等待孵化 → 契约"的操作。

### 1.2 核心能力

- 基于 OpenCV 模板匹配识别游戏 UI 元素
- 通过 Interception 内核驱动模拟鼠标点击与滚轮操作（绕过 `LLMHF_INJECTED` 检测）
- 提供 Tkinter 图形界面，支持蛋种任务队列、启停控制、实时日志
- 多模板窗口定位（适配不同天气/场景的游戏窗口外观）
- 蛋队列：滚动耗尽自动切换下一个蛋种，放入成功后重置到队首
- 工作流结束后可选自动关闭游戏窗口 / 自动关机
- 每次工作流结束自动保存日志文件
- 支持多屏幕配置切换（2560×1440 125% / 1920×1080 100%），启动时选择，运行时锁定

---

## 2. 技术栈

| 组件     | 技术                          | 用途                         |
| -------- | ----------------------------- | ---------------------------- |
| 图像识别 | OpenCV (cv2)                  | 模板匹配，定位游戏 UI 元素   |
| 输入模拟 | Interception 内核驱动         | 鼠标移动、点击、滚轮         |
| GUI 框架 | Tkinter (clam 主题)           | 控制面板、日志展示           |
| 配置管理 | Markdown (.md) 字典表         | 蛋和咕噜球的名称-图像映射    |
| 运行环境 | Windows 11, Python 3.11+      |                              |

---

## 3. 运行环境

| 项目         | 规格                            |
| ------------ | ------------------------------- |
| 操作系统     | Windows 11 (64-bit)             |
| 屏幕分辨率   | 2560 × 1440                    |
| 缩放比例     | 125%（不可更改）                |
| 游戏窗口尺寸 | 1442 × 938（含标题栏）          |
| 游戏窗口状态 | 窗口化模式，保持在孵蛋界面      |

---

## 4. 项目结构

```
roco_auto/
├── DESIGN.md                  # 本设计文档
├── main.py                    # 程序入口，启动 GUI
├── interception.dll           # Interception 内核驱动 (x64, 需自行安装)
├── core/
│   ├── __init__.py
│   ├── automator.py           # 11 状态状态机，编排整个工作流（含蛋队列）
│   ├── recognizer.py          # OpenCV 模板匹配封装
│   ├── operator.py            # Interception 鼠标/滚轮操作封装
│   └── window_manager.py      # 游戏窗口定位（多模板 window_list/）
├── ui/
│   ├── __init__.py
│   ├── app.py                 # Tkinter 主窗口 + 回调逻辑（含自动关机/关窗口）
│   ├── control_panel.py       # 控制面板（蛋队列、球选择、启停按钮、测试匹配）
│   └── log_panel.py           # 日志面板（ScrolledText + 颜色标签 + 缓冲区）
├── config/
│   ├── __init__.py
│   ├── dictionary_loader.py   # 字典文件解析器
│   └── settings.py            # 全局常量与配置
├── assets/
│   └── reference/
│       ├── 2560x1440_125/     # 2560×1440 125% 缩放的模板图像
│       │   ├── reference_diagram/
│       │   │   ├── *.png      # 流程 UI 元素模板图 (13 张)
│       │   │   └── window_list/  # 游戏窗口多模板（8 张）
│       │   └── reference_list/
│       │       ├── eggs/      # 蛋模板图 + eggs_dictionary.md（8 种蛋）
│       │       └── gulus/     # 咕噜球模板图 + gulus_dictionary.md（13 种球）
│       └── 1920x1080_100/     # 1920×1080 100% 缩放的模板图像（镜像结构）
│           ├── reference_diagram/
│           │   └── window_list/
│           └── reference_list/
│               ├── eggs/
│               └── gulus/
└── logs/                      # 运行日志输出目录
```

---

## 5. 状态机工作流

### 5.1 当前状态结构（11 状态）

```
STATE_1  定位窗口（多模板 window_list/）
  ↓
STATE_2  检测空装置 (noegg_selected)
  ├── 有 → STATE_3  放入蛋入口 (putin → putin_wait)
  │         ↓
  │       STATE_4  选蛋 (滚动 → 模板匹配 0.95 → 验证选中态)
  │         │        滚动 100 次耗尽 → 切换队列下一个蛋
  │         │        队列全部耗尽 → STOP
  │         ↓
  │       STATE_5  确认放入 (putin_1 → sleep 2s → takeout)
  │         │        成功 → egg_index = 0, → STATE_2
  │
  └── 无 → STATE_6  未选中空位 (noegg_notselected)
            ├── 有 → 点击选中 → STATE_2
            └── 无 → STATE_7  孵化轮询 (iterative while-loop)
                      ├── finished_selected     → STATE_8
                      └── finished_notselected  → STATE_8

STATE_8  契约入口 (contract → contract_wait)
  ↓
STATE_9  选咕噜球 (滚动 → 模板匹配 → 验证选中态)
  ↓
STATE_10 确认契约 (contract_1 → 等待动画 8s → 轮询 click.png)
  ↓
STATE_11 最终确认 (固定位置点击 → sleep 2s → site 验证) → STATE_2
```

### 5.2 关键设计决策

#### STATE_4: 蛋队列

- 使用 `self.egg_queue: list[EggEntry]` + `self.egg_index`
- `_current_egg()` 返回当前目标蛋
- 每次滚动 `_egg_scroll_total++`，找到目标蛋时归零
- 滚动 100 次仍未找到当前蛋 → `_rollback_egg_list()` 向上回滚等量齿数归位列表 → `egg_index++`，有下一个蛋则重新进入 STATE_4
- 队列全部耗尽 → STOP
- STATE_5 放入成功 → `egg_index = 0`，`_egg_scroll_total = 0`（重置到队首，下轮重新从第一个蛋开始）
- 匹配阈值 0.95（`MATCH_THRESHOLD_EGG`），滚动上限 100 次（`MAX_SCROLL_RETRIES_EGG`）

#### STATE_7: 迭代轮询，消除递归

问题：原 STATE_7 ↔ STATE_12 互相递归。孵化需数小时，0.5s 轮询一次，递归深度可达几万层栈 → `RecursionError`。

方案：合并为单一 `while` 循环：
1. 检测 `finished_selected` → 处理，成功则进入 STATE_8
2. 检测 `finished_notselected` → 处理，成功则进入 STATE_8
3. 都未找到，若 `poll_count == 0` 则日志"开始等待孵化中..."
4. `poll_count++`，每 20 次（~10s）心跳日志，`sleep(0.5)`，继续循环
5. 检查 `_stop_event`，用户停止则退出

#### STATE_10: 动画等待

- 点击 `contract_1.png`（模板匹配），等待动画播放完毕
- 轮询 `click.png`，间隔 0.5s，超时 8s
- 最多 3 次动画重试，全部超时则回 STATE_9

已知问题：`contract_1.png` 与 `click.png` 视觉相似，轮询时可能误匹配。

#### STATE_11: 固定位置点击 + 延迟验证

不使用模板匹配 `click.png` 的坐标，直接点击窗口相对坐标 `(win_x + 700, win_y + 800)`。点击后额外 `sleep(DELAY_SITE_VERIFY=2.0s)` 再验证 `site.png`。避免模板误匹配导致的坐标偏移和 UI 未就绪导致的验证失败。

#### STATE_5: 延迟验证

展开 `_click_and_verify` 为手动循环，点击 `putin_1.png` 后额外 `sleep(DELAY_PUTIN_VERIFY=2.0s)` 再验证 `takeout.png`，给游戏服务器足够响应时间。

#### 停止机制

`threading.Event` 在以下位置检查：
- `_run()` 主循环每轮开始
- `_check_window()` 窗口重定位前
- 每个状态方法入口（STATE_2, STATE_6, STATE_7 循环顶, STATE_10 动画循环内等）

轮询间隔 0.5s，最长停止延迟 2-8s。

---

## 6. 图像识别系统

### 6.1 模板匹配

| 参数       | 默认值              | 说明                     |
| ---------- | ------------------- | ------------------------ |
| 算法       | TM_CCOEFF_NORMED    | 归一化相关系数匹配       |
| 搜索区域   | 全屏 / 窗口区域     | 性能敏感场景限定在窗口区域 |

### 6.2 阈值分层

| 常量                     | 值   | 用途                                   |
| ------------------------ | ---- | -------------------------------------- |
| `MATCH_THRESHOLD`        | 0.8  | 所有 UI 元素（按钮、图标等）           |
| `WINDOW_MATCH_THRESHOLD` | 0.7  | 窗口模板匹配                           |
| `MATCH_THRESHOLD_EGG`    | 0.95 | 蛋图片匹配（最小模板，最高精度要求）     |

### 6.3 窗口多模板匹配

`locate_window()` 遍历 `reference_diagram/window_list/` 下所有 PNG（8 张：empty / steel / flying / grass / fire / ice / electric / illusion），依次用每个模板匹配全屏（阈值 0.7），首个命中即返回窗口左上角坐标。适配不同天气/属性场景下的窗口外观变化。

### 6.4 API

```python
match_template(name, dir, region?, threshold?)     → (cx, cy) | None
match_template_raw(name, dir, region?)              → (cx, cy, confidence)
match_template_in_window(name, dir, wx, wy, w, h, threshold?) → (cx, cy) | None
```

- 所有函数返回匹配区域的**中心坐标**
- `match_template_raw` 无阈值门控，始终返回置信度，供测试匹配功能使用
- `match_template` 内部调用 `match_template_raw`，阈值过滤后返回

### 6.5 参考图像清单

#### 流程 UI（reference_diagram）

| 文件名                   | 用途                   |
| ------------------------ | ---------------------- |
| noegg_selected.png       | 孵蛋装置空缺 - 已选中  |
| noegg_notselected.png    | 孵蛋装置空缺 - 未选中  |
| putin.png                | "放入"按钮             |
| putin_wait.png           | 放入后的等待确认       |
| putin_1.png              | 选蛋后的确认放入按钮   |
| takeout.png              | 放入成功后的界面标识   |
| finished_selected.png    | 孵化完成 - 已选中      |
| finished_notselected.png | 孵化完成 - 未选中      |
| contract.png             | "契约"按钮             |
| contract_wait.png        | 契约确认等待           |
| contract_1.png           | 选球后的确认契约按钮   |
| click.png                | 契约流程中的确认点击   |
| site.png                 | 最终确认后的界面标识   |

#### 窗口模板（reference_diagram/window_list/）

| 文件名              | 适配场景   |
| ------------------- | ---------- |
| window_empty.png    | 无属性     |
| window_steel.png    | 钢属性     |
| window_flying.png   | 飞属性     |
| window_grass.png    | 草属性     |
| window_fire.png     | 火属性     |
| window_ice.png      | 冰属性     |
| window_electric.png | 电属性     |
| window_illusion.png | 幻属性     |

#### 蛋种（reference_list/eggs）— 8 种

| 中文名称     | 图像                        | 检验图像                        |
| ------------ | --------------------------- | ------------------------------- |
| 神奇的蛋     | shenqi_egg.png              | shenqi_egg_selected.png         |
| 奇丽草的蛋   | qilicao_egg.png             | qilicao_egg_selected.png        |
| 治愈兔的蛋   | zhiyutu_egg.png             | zhiyutu_egg_selected.png        |
| 大耳帽兜的蛋 | daermaodou_egg.png          | daermaodou_egg_selected.png     |
| 拉特的蛋     | late_egg.png                | late_egg_selected.png           |
| 呼呼猪的蛋   | huhuzhu_egg.png             | huhuzhu_egg_selected.png        |
| 粉星仔的蛋   | fenxingzai_egg.png          | fenxingzai_egg_selected.png     |
| 火红尾的蛋   | huohongwei_egg.png          | huohongwei_egg_selected.png     |

#### 咕噜球（reference_list/gulus）— 13 种

| 中文名称   | 图像                      | 检验图像                      |
| ---------- | ------------------------- | ----------------------------- |
| 普通咕噜球 | putong_gulu.png           | putong_gulu_selected.png      |
| 高级咕噜球 | gaoji_gulu.png            | gaoji_gulu_selected.png       |
| 国王球     | guowang_gulu.png          | guowang_gulu_selected.png     |
| 美妙球     | meimiao_gulu.png          | meimiao_gulu_selected.png     |
| 好战球     | haozhan_gulu.png          | haozhan_gulu_selected.png     |
| 光合球     | guanghe_gulu.png          | guanghe_gulu_selected.png     |
| 网兜球     | wangdou_gulu.png          | wangdou_gulu_selected.png     |
| 暗星球     | anxing_gulu.png           | anxing_gulu_selected.png      |
| 调温球     | tiaowen_gulu.png          | tiaowen_gulu_selected.png     |
| 绝缘球     | jueyuan_gulu.png          | jueyuan_gulu_selected.png     |
| 淘沙球     | taosha_gulu.png           | taosha_gulu_selected.png      |
| 变幻球     | bianhuan_gulu.png         | bianhuan_gulu_selected.png    |
| 捕光球     | buguang_gulu.png          | buguang_gulu_selected.png     |

---

## 7. 输入系统 — Interception 驱动

### 7.1 为什么不用 PyAutoGUI

《洛克王国：世界》检测 `LLMHF_INJECTED` 标志位。`SendInput()` / PyAutoGUI 发出的点击带有该标志，游戏直接忽略。Interception 是内核级驱动，注入的事件不带注入标志。

### 7.2 架构

```
operator.py
  InterceptionDriver (singleton, lazy-init)
    ├── move_to(x, y)    → MOUSE_MOVE_ABSOLUTE (0x0001)
    ├── left_down()      → MOUSE_LEFT_DOWN     (0x001)
    ├── left_up()        → MOUSE_LEFT_UP       (0x002)
    └── scroll(clicks)   → MOUSE_WHEEL         (0x0400)

click(x, y):
  1. move_to(x, y)          # 绝对坐标，归一化到 0x0000-0xFFFF
  2. sleep(0.15)            # 移动稳定延迟
  3. left_down()
  4. sleep(0.02)            # 按下-释放间隔
  5. left_up()
  6. sleep(CLICK_WAIT=1.0)  # 点击后 UI 响应等待

scroll_at(x, y, clicks):
  1. move_to(x, y)
  2. scroll(clicks)         # 负值 = 向下滚动
  3. sleep(SCROLL_WAIT=0.3)

scroll_up_at(x, y, clicks):
  1. move_to(x, y)
  2. scroll(+clicks)        # 正值 = 向上滚动（蛋列表回滚用）
  3. sleep(SCROLL_WAIT=0.3)
```

- 纯输出模式：不设置 interception filter，物理鼠标不受影响
- 设备 ID = 11（`INTERCEPTION_MOUSE(0)`）

---

## 8. 窗口管理

### 8.1 初始定位

`locate_window()`: 遍历 `window_list/` 下所有 PNG（8 张），依次全屏匹配（阈值 0.7），首个命中返回窗口左上角 `(win_x, win_y)`。

### 8.2 每轮校验

`_check_window()`: 每轮循环开始时重新匹配 `window_list/`。若位置偏移 > 20px，更新坐标并日志提醒。连续 5 次匹配失败则判定窗口丢失，停止工作流。

---

## 9. GUI 设计

### 9.1 布局

```
┌──────────────────────────────────────┐
│  🥚 洛克王国自动孵蛋工具              │
├──────────────────────────────────────┤
│  屏幕设置:  [▼ 2560x1440 125%  ]     │
│                                      │
│  选择目标蛋:  [▼ 神奇的蛋  ] [＋加入队列]│
│                                      │
│  任务队列:                           │
│  ┌──────────────────────────────────┐│
│  │ 1. 神奇的蛋                     ││
│  │ 2. 治愈兔的蛋                   ││
│  └──────────────────────────────────┘│
│  [移除] [▲ 上移] [▼ 下移]            │
│                                      │
│  选择咕噜球:  [▼ 普通咕噜球  ]         │
│                                      │
│  [▶ 启动] [⏹ 停止] [🔍 测试匹配]    │
│                                      │
│  状态: ● 已停止                      │
│  循环次数: 0                         │
│  ☐ 工作流结束后自动关闭游戏窗口        │
│  ☐ 工作流结束后自动关机               │
│                                      │
├──────────────────────────────────────┤
│  ┌─ 运行日志 ───────────────────┐    │
│  │ ...                          │    │
│  └──────────────────────────────┘    │
├──────────────────────────────────────┤
│  日志文件: logs/                     │
└──────────────────────────────────────┘
```

### 9.2 蛋队列交互

| 操作               | 行为                                       |
| ------------------ | ------------------------------------------ |
| "＋ 加入队列"     | 将下拉框当前选中的蛋追加到队列末尾         |
| "移除"            | 删除队列中选中的条目                       |
| "▲ 上移" / "▼ 下移" | 调整队列中条目的顺序                     |
| 队列非空时启动     | 使用队列内容；队列空则回退到下拉框单蛋选择 |
| 运行中             | 队列相关按钮、下拉框全部禁用               |

### 9.3 工作流结束后选项

| 选项                           | 行为                                                    |
| ------------------------------ | ------------------------------------------------------- |
| 自动关闭游戏窗口               | 点击 `(win_x + 1412, win_y + 17)`，轮询至窗口消失（15s） |
| 自动关机                       | `shutdown /s /t 60`，60 秒倒计时，可 `shutdown /a` 取消  |

两个选项独立，同时勾选时先关窗口、再关机。

### 9.4 测试匹配功能（"🔍 测试匹配"按钮）

截取全屏，遍历 `reference_diagram/` 下所有 PNG + 当前选中蛋/咕噜球的模板图，逐一执行 `match_template_raw`，按置信度降序输出：
- OK (≥0.8), WARN (≥0.7), FAIL (<0.7)

### 9.5 配色

| 元素       | 颜色            | 色值        |
| ---------- | --------------- | ----------- |
| 主背景     | 白色            | white       |
| 强调色     | 洛克蓝          | `#112DA5`   |
| 按钮       | 白色背景 + 黑色文字 + 2px raised 边框 |  |
| 队列选中   | `#112DA5` 背景 + 白色文字 |        |

### 9.6 日志标签颜色

| 标签   | 颜色      | 用途               |
| ------ | --------- | ------------------ |
| START  | `#3C5A7D` | 阶段开始、标记     |
| OK     | `#2D6A2D` | 匹配成功、操作确认 |
| FAIL   | `#B5451A` | 匹配失败、验证失败 |
| ACT    | `#20548B` | 点击操作           |
| SCROLL | `#20548B` | 滚动操作           |
| WARN   | `#8B7500` | 警告               |
| ERROR  | `#CC2200` | 异常               |
| STOP   | `#B5451A` | 工作流结束         |

### 9.7 日志自动保存

LogPanel 维护 `_buffer: list[str]`，`_write()` 每行追加。工作流结束时 `_handle_stopped()` 将缓冲区写入 `logs/YYYYMMDD_HHMMSS.log` (UTF-8)。

### 9.8 线程安全

Automator 在 daemon 线程运行，日志通过 `root.after(0, callback, message)` 回主线程写入 ScrolledText。自动关窗口操作在独立 daemon 线程执行，不阻塞 UI。

---

## 10. 配置常量

| 常量                     | 值             | 说明                           |
| ------------------------ | -------------- | ------------------------------ |
| `SCREEN_W` / `_H`        | 2560 / 1440    | 屏幕分辨率                     |
| `GAME_WINDOW_W` / `_H`   | 1442 / 938     | 游戏窗口尺寸                   |
| `MATCH_THRESHOLD`        | 0.8            | UI 元素匹配阈值                |
| `WINDOW_MATCH_THRESHOLD` | 0.7            | 窗口模板匹配阈值               |
| `MATCH_THRESHOLD_EGG`    | 0.95           | 蛋图片匹配阈值                 |
| `CLICK_WAIT`             | 1.0s           | 每次点击后等待                 |
| `SCROLL_WAIT`            | 0.3s           | 每次滚动后等待                 |
| `POLL_INTERVAL`          | 0.5s           | 通用轮询间隔                   |
| `ANIMATION_POLL_INTERVAL`| 0.5s           | STATE_10 动画检测间隔          |
| `ANIMATION_TIMEOUT`      | 8.0s           | STATE_10 动画超时              |
| `MAX_CLICK_RETRIES`      | 3              | 点击-验证重试上限              |
| `MAX_SCROLL_RETRIES`     | 10             | 咕噜球列表滚动重试上限         |
| `MAX_SCROLL_RETRIES_EGG` | 100            | 蛋列表滚动重试上限             |
| `MAX_WINDOW_LOST_CHECKS` | 5              | 窗口丢失确认次数               |
| `MAX_ANIMATION_RETRIES`  | 3              | STATE_10 动画重试上限          |
| `DELAY_PUTIN_VERIFY`     | 2.0s           | STATE_5 点击后额外等待         |
| `DELAY_SITE_VERIFY`      | 2.0s           | STATE_11 点击后额外等待        |
| `SCROLL_REL_X` / `_Y`    | 1160 / 500     | 滚动触发的相对窗口坐标         |
| `SCROLL_CLICKS`          | 24             | 每次滚动的滚轮齿数             |
| `WHEEL_DELTA`            | 120            | Windows 标准滚轮 delta         |
| `MOVE_DELAY`             | 0.02s          | 按下-释放之间的微延迟          |

---

## 11. 多分辨率配置

### 11.1 配置切换

`config/settings.py` 中 `SCREEN_CONFIGS` 字典存储每个屏幕配置的独立参数，通过 `activate_config(name)` 切换。所有模块通过 `from config import settings as _cfg` 读取运行时值，而非导入时捕获。

### 11.2 每配置参数

| 参数               | 2560×1440 125% | 1920×1080 100% | 说明                     |
| ------------------ | -------------- | -------------- | ------------------------ |
| `game_window_w/h`  | 1442 × 938     | 1150 × 750     | 游戏窗口像素尺寸         |
| `scroll_rel_x/y`   | 1160, 500      | 920, 400       | 滚动区域相对窗口坐标     |
| `state11_offset_x/y`| 700, 800      | 500, 400       | STATE_11 固定点击偏移    |
| `close_offset_x/y` | 1412, 17       | 1120, 20       | 关闭按钮相对窗口偏移     |

### 11.3 资产隔离

每种配置的模板图像存放在 `assets/reference/<config_name>/` 下，镜像目录结构。切换配置后自动重载字典并刷新 UI。

---

## 12. 日志规范

### 12.1 级别

| 前缀   | 含义               |
| ------ | ------------------ |
| START  | 阶段开始/标记      |
| OK     | 图像匹配/验证成功  |
| FAIL   | 图像匹配/验证失败  |
| ACT    | 执行操作           |
| SCROLL | 滚轮操作           |
| WARN   | 警告（不影响运行） |
| ERROR  | 异常错误           |
| STOP   | 工作流停止及原因   |

### 12.2 格式

```
[HH:MM:SS.ff] LEVEL  message
```

### 12.3 输出

1. GUI 日志面板：实时滚动
2. 日志文件：工作流结束时保存至 `logs/YYYYMMDD_HHMMSS.log` (UTF-8)

---

## 13. 重试策略汇总

| 场景                   | 重试次数 | 耗尽后行为                           |
| ---------------------- | -------- | ------------------------------------ |
| 点击后验证失败（常规） | 3 次     | 返回上级状态重新识别                 |
| 蛋列表滚动搜索         | 100 次   | 切换队列下一个蛋，全部耗尽则 STOP    |
| 咕噜球列表滚动搜索     | 10 次    | 停止工作流                           |
| STATE_10 动画等待      | 8s 超时  | 重试点击 contract_1（最多 3 次）     |
| STATE_11 site 验证     | 3 次     | 停止工作流                           |
| 窗口丢失连续检测       | 5 次     | 停止工作流                           |

---

## 14. Git 历史

| 提交       | 内容                                                        |
| ---------- | ----------------------------------------------------------- |
| `185c93b`  | chore: 初始脚手架 + 核心框架                                |
| `c1f9bd3`  | feat: PyAutoGUI → Interception 驱动迁移                     |
| `c74baef`  | refactor: 阈值分离、心跳日志、停止检查、白色 UI             |
| `816fb9a`  | fix: 消除孵化轮询中无限递归                                 |
| `f68d0a4`  | feat: 测试匹配面板、日志自动保存、STATE_11 固定位置点击     |
| `b216391`  | feat: 多模板窗口匹配、新蛋/球资产、孵化轮询优化、工作流后选项 |
| `1c9e82a`  | chore: 清理误提交文件                                       |
| *(待提交)*  | feat: 多分辨率配置切换、蛋列表滚动回滚              |
