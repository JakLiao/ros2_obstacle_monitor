from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='obstacle_monitor',
            executable='obstacle_detector',
            name='obstacle_detector',
            output='screen',
        ),
        Node(
            package='obstacle_monitor',
            executable='obstacle_avoider',
            name='obstacle_avoider',
            output='screen',
        ),
    ])
