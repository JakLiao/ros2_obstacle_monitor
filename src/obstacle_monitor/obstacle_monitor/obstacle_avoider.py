import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped  # Jazzy: 必须用 TwistStamped 跟 ros_gz_bridge 匹配


class ObstacleAvoider(Node):
    def __init__(self):
        super().__init__('obstacle_avoider')
        self.subscription = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)
        self.publisher = self.create_publisher(TwistStamped, '/cmd_vel', 10)  # Jazzy
        self.safe_distance = 0.5  # m
        self.linear_speed = 0.2   # m/s
        self.angular_speed = 0.5  # rad/s

    def scan_callback(self, msg: LaserScan):
        twist = TwistStamped()  # Jazzy
        twist.header.stamp = self.get_clock().now().to_msg()  # Jazzy: 必须带 timestamp
        twist.header.frame_id = 'base_footprint'              # Jazzy: 必须带 frame_id
        n = len(msg.ranges)
        # 12 个扇区（30°/扇区）
        sector_size = n // 12
        sector_mins = []
        for i in range(12):
            sector = msg.ranges[i * sector_size : (i + 1) * sector_size]
            valid = [r for r in sector if msg.range_min < r < msg.range_max]
            sector_mins.append(min(valid) if valid else msg.range_max)
        # 前方扇区 = 扇区 11（330-360°）+ 扇区 0（0-30°），跨越 0° 边界
        front_sectors = [sector_mins[11], sector_mins[0]]
        front_min = min(front_sectors)
        if front_min < self.safe_distance:
            # 前方堵死 → 找最安全的扇区
            best_sector = sector_mins.index(max(sector_mins))
            # 扇区 0-5 = 左半边 (0°..180°)，扇区 6-11 = 右半边 (180°..360°)
            # ROS2 REP-103: angular.z > 0 = 左转（从上往下看逆时针）
            if best_sector < 6:
                twist.twist.angular.z = self.angular_speed   # 左转（TwistStamped 是嵌套结构）
            else:
                twist.twist.angular.z = -self.angular_speed  # 右转
            twist.twist.linear.x = 0.0
        else:
            # 前方安全 → 直行
            twist.twist.linear.x = self.linear_speed
            twist.twist.angular.z = 0.0
        self.publisher.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoider()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

