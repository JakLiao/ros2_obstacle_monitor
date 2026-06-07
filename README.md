# ros2_hello

ROS2 Jazzy 学习项目（Day 2 通信三件套）。

## 内容

- `src/tutorial_interfaces/`：自定义 .msg / .srv / .action 接口
- `src/py_tutorial/`：Python pub/sub + service + action 节点

## 运行

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

# 终端 1
ros2 run py_tutorial talker

# 终端 2
ros2 run py_tutorial listener
