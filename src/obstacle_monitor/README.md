# `obstacle_monitor` — ROS2 Python Package

> **Day 3-4 核心包**：TurtleBot3 避障感知 + 决策节点（Nav2 导航见 [`config/nav2_burger_sim.yaml`](config/nav2_burger_sim.yaml)）
>
> 顶层项目 README：[`/README.md`](../../README.md) — 仓库介绍 / 多包布局 / 跨包运行步骤 / 6 条踩坑 / 简历描述

---

## 1. 包概览

| 项 | 值 |
|---|---|
| 包名 | `obstacle_monitor` |
| 构建类型 | `ament_python` |
| 入口可执行 | `obstacle_detector`、`obstacle_avoider` |
| 资源 | `launch/obstacle_monitor.launch.py`、`config/nav2_burger_sim.yaml` |
| 依赖 | `rclpy sensor_msgs std_msgs geometry_msgs` |

---

## 2. 节点 API

### 2.1 `obstacle_detector`（感知层）

**职责**：订阅激光雷达，发布前向障碍物告警布尔。

| 端口 | 方向 | 类型 | 频率 | 说明 |
|---|---|---|---|---|
| `/scan` | sub | `sensor_msgs/LaserScan` | 10 Hz | Gazebo 雷达输出 |
| `/obstacle_warning` | pub | `std_msgs/Bool` | 跟随 `/scan` | true = 前向扇区内检测到障碍物 |

**参数**（节点内常量，目前需改源码调，未来可改 `declare_parameter`）：

| 参数 | 默认值 | 单位 | 含义 |
|---|---|---|---|
| `front_angle_range` | 60 | 度 | 前向扇区总宽度（覆盖斜前方避免漏检） |
| `threshold` | 0.5 | 米 | 触发告警的最小距离 |

**算法**：

```
n = len(ranges)                              # 通常 360
center = n // 2
half_window = int(angle_range / (angle_increment * 180 / π))
front = ranges[center - half_window : center + half_window]
valid = [r for r in front if range_min < r < range_max]   # 滤 inf / nan
warning = min(valid) < threshold
```

**典型日志**（`ros2 run` 触发）：

```
[WARN] [obstacle_detector]: ⚠️ 前向扇区 ±30° 障碍物 0.42m (< 0.5m)
```

### 2.2 `obstacle_avoider`（决策层）

**职责**：12 扇区扫描 + 左右半边平均 + 0.1m 迟滞带，发布避障速度。

| 端口 | 方向 | 类型 | 频率 | 说明 |
|---|---|---|---|---|
| `/scan` | sub | `sensor_msgs/LaserScan` | 10 Hz | 雷达 |
| `/cmd_vel` | pub | `geometry_msgs/TwistStamped` | 跟随 `/scan` | **Jazzy 强制**（带 `header.stamp` + `frame_id`） |

**参数**：

| 参数 | 默认值 | 单位 | 含义 |
|---|---|---|---|
| `safe_distance` | 0.5 | 米 | 前向 < 此值触发转向 |
| `linear_speed` | 0.2 | m/s | 前进速度 |
| `angular_speed` | 0.5 | rad/s | 转弯角速度 |

**算法**：

```
12 扇区（每扇区 30°）→ sector_mins[0..11]
front_sectors = [sector_mins[11], sector_mins[0]]   # 跨越 0° 边界
front_min = min(front_sectors)

left_avg  = mean(sector_mins[0:6])    # 扇区 0-5  = 左半边 (0°..180°)
right_avg = mean(sector_mins[6:12])   # 扇区 6-11 = 右半边 (180°..360°)

if front_min < safe_distance:
    # 0.1m 迟滞带：左右差 < 0.1m → 保持上一帧方向（治撞墙原地左右抖）
    if |left_avg - right_avg| < 0.1 and last_turn_dir is not None:
        turn = last_turn_dir
    elif left_avg > right_avg:
        turn = +1   # 左转（REP-103: angular.z > 0 = 左）
    else:
        turn = -1   # 右转
    cmd_vel = (0, ±angular_speed)
else:
    cmd_vel = (linear_speed, 0)
```

**与 Nav2 抢 `/cmd_vel` 的处理**：avoider 和 Nav2 不能同时开（详见顶层 README 踩坑 #5）。本包默认走 Nav2 模式，avoider 仅作 Day 3 学习 demo。

---

## 3. Launch

### `launch/obstacle_monitor.launch.py`

同时启动 detector + avoider：

```bash
ros2 launch obstacle_monitor obstacle_monitor.launch.py
```

输出示例（两个节点 stdout 混在终端）：

```
[obstacle_detector-1] [INFO] [...]: 节点已就绪
[obstacle_avoider-1] [INFO] [...]: 节点已就绪
```

> 如果只想要 avoider（避开 Nav2 抢 `/cmd_vel`）：注释掉 `Node(obstacle_detector)` 或另写一个 `avoider_only.launch.py`。

---

## 4. 配置

### `config/nav2_burger_sim.yaml`（451 行）

Nav2 全栈项目级 `params_file`，顶层 `use_sim_time: true` + 13 个 Nav2 节点同步注入。完整内容见文件，**关键节点**：

| 节点 | 关键参数 | 说明 |
|---|---|---|
| `amcl` | `set_initial_pose: false`（按设计） | 启动后等 `/initialpose` topic；需在 rviz2 给 2D Pose Estimate |
| `amcl` | `base_frame_id: "base_footprint"` | TB3 Burger 标配 |
| `planner_server` | `planner_plugins: ["GridBased"]` | smac_planner 2D |
| `controller_server` | `controller_plugins: ["FollowPath"]` | DWB LocalPlanner |
| `bt_navigator` | `default_nav_to_pose_bt_xml` | 内置行为树 |

**为什么需要项目级 params_file**：Jazzy 的 `nav2_bringup launch` 不接受命令行 `use_sim_time:=true`（lifecycle_manager 抛 exception），必须 YAML 顶层注入。详见顶层 README 踩坑 #1。

---

## 5. 扩展开发

### 5.1 加新节点

```bash
# 1. 在 src/obstacle_monitor/obstacle_monitor/ 下新建 my_node.py
# 2. 编辑 src/obstacle_monitor/setup.py entry_points 加：
'console_scripts': [
    'my_node = obstacle_monitor.my_node:main',
    # ... 原有
]
# 3. 编辑 package.xml 加新依赖（如果有）
# 4. 重新编译
cd ~/ros2_ws
colcon build --packages-select obstacle_monitor
source install/setup.bash
# 5. 跑
ros2 run obstacle_monitor my_node
```

### 5.2 加新 Launch 文件

在 `src/obstacle_monitor/launch/` 下新建 `my_launch.py`，`setup.py` 的 `data_files` 已自动 include `launch/*.launch.py`，无需改 setup.py。

### 5.3 加新配置

把 YAML 放 `src/obstacle_monitor/config/`，**setup.py 不需要改**（ament_python 默认不会 install config/，需手动加 `data_files` glob，或运行时用绝对路径 `params_file:=/abs/path/...`）。

### 5.4 跑测试

```bash
cd ~/ros2_ws
colcon build --packages-select obstacle_monitor --cmake-args -DBUILD_TESTING=ON
source install/setup.bash
colcon test --packages-select obstacle_monitor
# 详细输出
colcon test-result --verbose
```

包内含 3 个 linter 测试（`test/test_copyright.py` / `test_flake8.py` / `test_pep257.py`），CI 跑 ament 规范检查。

---

## 6. 包内文件清单

```
obstacle_monitor/
├── README.md                  # 本文件（包开发者视角）
├── package.xml                # ament_python 包描述
├── setup.py                   # 入口声明 + 资源 glob
├── setup.cfg                  # ament 默认配置
├── obstacle_monitor/          # Python 源码
│   ├── __init__.py
│   ├── obstacle_detector.py   # 感知层
│   └── obstacle_avoider.py    # 决策层
├── launch/
│   └── obstacle_monitor.launch.py
├── config/
│   └── nav2_burger_sim.yaml   # Nav2 全栈 params_file
├── docs/
│   └── rqt_graph_nav2.png     # 节点拓扑截图（顶层 README 引用）
├── resource/
│   └── obstacle_monitor       # ament 索引标记文件
└── test/
    ├── test_copyright.py
    ├── test_flake8.py
    └── test_pep257.py
```

---

## 7. 跨包依赖图

```
            ┌─────────────────────────────────────┐
            │ 顶层 / 跨包运行步骤 / 6 条踩坑 / 简历描述  │
            │         → /README.md (项目 README)    │
            └─────────────────────────────────────┘
                              ▲
                              │ 引用
            ┌─────────────────┴──────────────────┐
            │  本 README（包开发者视角）              │
            │  - 节点 API/参数/算法                 │
            │  - Launch / 配置 / 扩展开发            │
            └─────────────────┬──────────────────┘
                              │ 依赖
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
 obstacle_detector.py   obstacle_avoider.py   nav2_burger_sim.yaml
 （感知 / /scan → /obstacle_warning） （决策 / /scan → /cmd_vel）   （Nav2 全栈 / 13 节点）
```

> 简历项目描述（中文+英文）见顶层 README §1，**不在此重复**以保持单一来源。

---

## 8. License

MIT © JakLiao
