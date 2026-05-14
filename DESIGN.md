# 洛克王国：世界 — 自动孵蛋工具设计文档

> 版本: 1.1
> 日期: 2026-05-14
> 状态: 开发中

---

## 1. 项目概述

### 1.1 目标

开发一款 Windows 桌面工具，自动化完成游戏《洛克王国：世界》中的孵蛋及咕噜球契约流程。用户通过 GUI 面板选择目标蛋种和咕噜球类型后，程序在游戏孵蛋界面循环执行"放蛋 → 等待孵化 → 契约"的操作。

### 1.2 核心能力

- 基于 OpenCV 模板匹配识别游戏 UI 元素
- 通过 Interception 内核驱动模拟鼠标点击与滚轮操作（绕过 `LLMHF_INJECTED` 检测）
- 提供 Tkinter 图形界面，支持蛋/球选择、启停控制和实时日志
- 健壮的错误处理与重试机制，异常时自动停止并记录原因
- 每次工作流结束自动保存日志文件

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
roco_auto2/
├── DESIGN.md                  # 本设计文档
├── main.py                    # 程序入口，启动 GUI
├── interception.dll           # Interception 内核驱动 (x64, 需自行安装)
├── core/
│   ├── __init__.py
│   ├── automator.py           # 11 状态状态机，编排整个工作流
│   ├── recognizer.py          # OpenCV 模板匹配封装
│   ├── operator.py            # Interception 鼠标/滚轮操作封装
│   └── window_manager.py      # 游戏窗口定位与管理
├── ui/
│   ├── __init__.py
│   ├── app.py                 # Tkinter 主窗口 + 回调逻辑
│   ├── control_panel.py       # 控制面板（蛋/球选择、启停按钮、测试匹配）
│   └── log_panel.py           # 日志面板（ScrolledText + 颜色标签 + 缓冲区）
├── config/
│   ├── __init__.py
│   ├── dictionary_loader.py   # 字典文件解析器
│   └── settings.py            # 全局常量与配置
├── assets/
│   └── reference/
│       ├── reference_diagram/ # 流程 UI 元素模板图 (~14 张 png)
│       └── reference_list/
│           ├── eggs/          # 蛋模板图 + eggs_dictionary.md
│           └── gulus/         # 咕噜球模板图 + gulus_dictionary.md
└── logs/                      # 运行日志输出目录
```

---

## 5. 状态机工作流

### 5.1 当前状态结构（11 状态）

```
STATE_1  定位窗口
  ↓
STATE_2  检测空装置 (noegg_selected)
  ├── 有 → STATE_3  放入蛋入口 (putin → putin_wait)
  │         ↓
  │       STATE_4  选蛋 (滚动列表 → 模板匹配 → 点击 → 验证选中态)
  │         ↓
  │       STATE_5  确认放入 (putin_1 → takeout) → STATE_2
  │
  └── 无 → STATE_6  未选中空位 (noegg_notselected)
            ├── 有 → 点击选中 → STATE_2
            └── 无 → STATE_7  孵化轮询 (iterative while-loop)
                      ├── finished_selected     → STATE_8
                      └── finished_notselected  → STATE_8

STATE_8  契约入口 (contract → contract_wait)
  ↓
STATE_9  选咕噜球 (滚动列表 → 模板匹配 → 点击 → 验证选中态)
  ↓
STATE_10 确认契约 (contract_1 → 等待动画 8s → 轮询 click.png)
  ↓
STATE_11 最终确认 (固定位置点击 → site 验证) → STATE_2
```

### 5.2 关键设计决策

#### STATE_7: 迭代轮询，消除递归

问题：原 STATE_7 ↔ STATE_12 互相递归。孵化需数小时，0.5s 轮询一次，递归深度可达几万层栈 → `RecursionError`。

方案：合并为单一 `while` 循环（第 816fb9a 次提交）：
1. 检测 `finished_selected` → 处理，成功则进入 STATE_8
2. 检测 `finished_notselected` → 处理，成功则进入 STATE_8
3. 都未找到 → `poll_count++`，每 20 次（~10s）心跳日志，`sleep(0.5)`，继续循环
4. 检查 `_stop_event`，用户停止则退出

无递归，栈不增长，可无限轮询。

#### STATE_10: 动画等待

- 点击 `contract_1.png`（模板匹配），等待动画播放完毕
- 轮询 `click.png`，间隔 0.5s，超时 8s
- 最多 3 次动画重试，全部超时则回 STATE_9

已知问题：`contract_1.png` 与 `click.png` 视觉相似，轮询时可能误匹配。待改为固定位置方案。

#### STATE_11: 固定位置点击（第 816fb9a 后修改）

不使用模板匹配 `click.png` 的坐标，直接点击窗口相对坐标 `(win_x + 700, win_y + 800)`，然后验证 `site.png`。避免模板误匹配导致的坐标偏移。

#### 停止机制

`threading.Event` 在以下位置检查：
- `_run()` 主循环每轮开始
- `_check_window()` 窗口重定位前
- 每个状态方法入口（STATE_2, STATE_6, STATE_7 循环顶, STATE_10 动画循环内等）

轮询间隔 0.5s，最长停止延迟 2-8s。

#### 心跳日志

STATE_7 孵化等待期间，每 20 次轮询（~10s）输出 "等待孵化中... (已轮询 N 次)"。

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
| `WINDOW_MATCH_THRESHOLD` | 0.7  | 仅 `window.png` 窗口定位               |

窗口识别阈值更低是因为游戏窗口截图可能与参考图存在细微差异（天气、特效等），UI 元素是固定的。

### 6.3 API

```python
match_template(name, dir, region?, threshold?)  → (cx, cy) | None
match_template_raw(name, dir, region?)           → (cx, cy, confidence)
match_template_in_window(name, dir, wx, wy, w, h) → (cx, cy) | None
```

- 所有函数返回匹配区域的**中心坐标**
- `match_template_raw` 无阈值门控，始终返回置信度，供测试匹配功能使用
- `match_template` 内部调用 `match_template_raw`，阈值过滤后返回

### 6.4 参考图像清单（reference_diagram）

| 文件名                   | 用途                   |
| ------------------------ | ---------------------- |
| window.png               | 游戏窗口定位           |
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
```

- 纯输出模式：不设置 interception filter，物理鼠标不受影响
- 设备 ID = 11（`INTERCEPTION_MOUSE(0)`）

---

## 8. 窗口管理

### 8.1 初始定位

`locate_window()`: 使用 `window.png` 全屏模板匹配（阈值 0.7），找到游戏窗口中心坐标，换算为左上角 `(win_x, win_y)`。

### 8.2 每轮校验

`_check_window()`: 每轮循环开始时重新匹配 `window.png`。若位置偏移 > 20px，更新坐标并日志提醒。连续 5 次匹配失败则判定窗口丢失，停止工作流。

---

## 9. GUI 设计

### 9.1 当前配色

| 元素       | 颜色            | 色值        |
| ---------- | --------------- | ----------- |
| 主背景     | 白色            | white       |
| 强调色     | 洛克蓝          | `#112DA5`   |
| 按钮       | 白色背景 + 黑色文字 + 2px raised 边框 |  |
| 按钮-按下  | sunken          |             |
| 按钮-禁用  | `#F5F5F5`       |             |
| 下拉框选中 | `#112DA5` 背景 + 白字 |        |

### 9.2 日志标签颜色（白色背景下深色文字）

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

### 9.3 测试匹配功能（"🔍 测试匹配"按钮）

截取全屏，遍历 `reference_diagram/` 下所有 PNG + 当前选中蛋/咕噜球的模板图，逐一执行 `match_template_raw`，按置信度降序输出：
- OK (≥0.8), WARN (≥0.7), FAIL (<0.7)

### 9.4 日志自动保存

LogPanel 维护 `_buffer: list[str]`，`_write()` 每行追加。工作流结束时 `_handle_stopped()` 将缓冲区写入 `logs/YYYYMMDD_HHMMSS.log` (UTF-8)。

### 9.5 线程安全

Automator 在 daemon 线程运行，日志通过 `root.after(0, callback, message)` 回主线程写入 ScrolledText。

---

## 10. 配置常量

| 常量                     | 值             | 说明                           |
| ------------------------ | -------------- | ------------------------------ |
| `SCREEN_W` / `_H`        | 2560 / 1440    | 屏幕分辨率                     |
| `GAME_WINDOW_W` / `_H`   | 1442 / 938     | 游戏窗口尺寸                   |
| `MATCH_THRESHOLD`        | 0.8            | UI 元素匹配阈值                |
| `WINDOW_MATCH_THRESHOLD` | 0.7            | 窗口定位匹配阈值               |
| `CLICK_WAIT`             | 1.0s           | 每次点击后等待                 |
| `SCROLL_WAIT`            | 0.3s           | 每次滚动后等待                 |
| `POLL_INTERVAL`          | 0.5s           | 通用轮询间隔                   |
| `ANIMATION_POLL_INTERVAL`| 0.5s           | STATE_10 动画检测间隔          |
| `ANIMATION_TIMEOUT`      | 8.0s           | STATE_10 动画超时              |
| `MAX_CLICK_RETRIES`      | 3              | 点击-验证重试上限              |
| `MAX_SCROLL_RETRIES`     | 10             | 列表滚动查找重试上限           |
| `MAX_WINDOW_LOST_CHECKS` | 5              | 窗口丢失确认次数               |
| `MAX_ANIMATION_RETRIES`  | 3              | STATE_10 动画重试上限          |
| `SCROLL_REL_X` / `_Y`    | 1160 / 500     | 滚动触发的相对窗口坐标         |
| `SCROLL_CLICKS`          | 24             | 每次滚动的滚轮齿数             |
| `WHEEL_DELTA`            | 120            | Windows 标准滚轮 delta         |
| `MOVE_DELAY`             | 0.02s          | 按下-释放之间的微延迟          |

---

## 11. 日志规范

### 11.1 级别

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

### 11.2 格式

```
[HH:MM:SS.ff] LEVEL  message
```

### 11.3 输出

1. GUI 日志面板：实时滚动
2. 日志文件：工作流结束时保存至 `logs/YYYYMMDD_HHMMSS.log` (UTF-8)

---

## 12. 重试策略汇总

| 场景                   | 重试次数 | 耗尽后行为                           |
| ---------------------- | -------- | ------------------------------------ |
| 点击后验证失败（常规） | 3 次     | 返回上级状态重新识别                 |
| 蛋列表滚动搜索         | 10 次    | 停止工作流                           |
| 咕噜球列表滚动搜索     | 10 次    | 停止工作流                           |
| STATE_10 动画等待      | 8s 超时  | 重试点击 contract_1（最多 3 次）     |
| STATE_11 site 验证     | 3 次     | 停止工作流                           |
| 窗口丢失连续检测       | 5 次     | 停止工作流                           |

---

## 13. Git 历史

| 提交       | 内容                                             |
| ---------- | ------------------------------------------------ |
| `185c93b`  | chore: 初始脚手架 + 核心框架                      |
| `c1f9bd3`  | feat: PyAutoGUI → Interception 驱动迁移           |
| `c74baef`  | refactor: 阈值分离、心跳日志、停止检查、白色 UI   |
| `816fb9a`  | fix: 消除孵化轮询中无限递归                       |
