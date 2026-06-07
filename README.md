# ros2_hello

ROS2 Jazzy 学习项目（Day 2 通信三件套：Topic + Service + Action）。

## 项目结构

| 目录 | 类型 | 内容 |
|------|------|------|
| `src/py_tutorial/` | ament_python | Python pub/sub 节点（Hello World demo） |
| `src/py_srvcli/` | ament_python | Service client/server（AddTwoInts） |
| `src/tutorial_interfaces/` | ament_cmake | 自定义 msg/srv 接口（Num / AddThreeInts） |
| `src/custom_action_interfaces/` | ament_cmake + 单文件 Python | 自定义 action 接口（Fibonacci）+ 教程原版单文件 server/client |

## 通信三件套

| 通信 | 形式 | 适用 | 本项目示例 |
|------|------|------|-----------|
| **Topic** | pub/sub 单向数据流 | 传感器/状态/控制指令的持续流 | `py_tutorial` 的 talker/listener |
| **Service** | 请求-响应 同步 | 立刻要答案的一次性调用 | `py_srvcli` 的 AddTwoInts |
| **Action** | goal + feedback + result 异步 | 长任务 + 进度监控 + 可取消 | `custom_action_interfaces` 的 Fibonacci |

## 运行

### 0. 准备（首次）

```bash
# 装 ROS2 Jazzy + rosdep
sudo apt install ros-jazzy-desktop python3-rosdep
sudo rosdep init && rosdep update

# 装依赖 + 编译
cd ~/ros2_ws
rosdep install -i --from-path src --rosdistro jazzy -y
colcon build --merge-install
```

### 1. 激活环境（每个终端都要）

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

### 2. Topic pub/sub

```bash
# 终端 1
ros2 run py_tutorial talker

# 终端 2
ros2 run py_tutorial listener
```

**预期输出**：
- talker：`Publishing: "Hello World: 0"` `Publishing: "Hello World: 1"` ...
- listener：`I heard: "Hello World: 0"` `I heard: "Hello World: 1"` ...

### 3. Service client/server

```bash
# 终端 1
ros2 run py_srvcli service

# 终端 2
ros2 run py_srvcli client 2 3
```

**预期输出**：
- service：`Incoming request` `a: 2 b: 3`
- client：`Result of add_two_ints: for 2 + 3 = 5`

### 4. Action server + client

教程原文：<https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Writing-an-Action-Server-Client/Py.html>

```bash
# 终端 1
python3 src/custom_action_interfaces/fibonacci_action_server.py

# 终端 2
python3 src/custom_action_interfaces/fibonacci_action_client.py
```

**预期输出**：
- server：`Executing goal...` `Feedback: [0, 1, 1, 2, ...]`（每 1 秒一次）
- client：`Goal accepted :)` `Result: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]`

### 4b. Action 命令行验证（不写 client 也行）

```bash
ros2 action send_goal --feedback fibonacci custom_action_interfaces/action/Fibonacci "{order: 5}"
```

**预期输出**：feedback 持续输出 `partial_sequence`，result 是 `[0, 1, 1, 2, 3, 5]`

## 教程

- 鱼香 ROS BV764419101 P6-P10
- ROS2 Jazzy 官方 tutorial：<https://docs.ros.org/en/jazzy/Tutorials.html>
- ROS2 Action tutorial（本项目 Action 部分）：<https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Writing-an-Action-Server-Client/Py.html>

## 环境

- ROS2 Jazzy（Ubuntu 24.04 WSL2）
- Python 3.12
- colcon build + ament_cmake / ament_python
- RMW：`rmw_fastrtps_cpp`（Jazzy 默认）

## 已知问题

- `src/tutorial_interfaces` 在 colcon build 时报 `ModuleNotFoundError: No module named 'ament_package'`（Jazzy 装法需要 `echo "/opt/ros/jazzy/lib/python3.12/site-packages" | sudo tee /usr/lib/python3/dist-packages/ros-jazzy.pth` 修复）。本项目**主流程不依赖此包**（用 `custom_action_interfaces` + 标准 `example_interfaces`），所以暂未修。

## 学习日志

详见 `_projects/ros2-study-day2-guide.md`。
