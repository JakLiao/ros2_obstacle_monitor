import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool


class ObstacleDetector(Node):
    def __init__(self):
        super().__init__('obstacle_detector')
        self.subscription = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)
        self.publisher = self.create_publisher(Bool, '/obstacle_warning', 10)
        # 前向扇区总宽度（60° = ±30°，覆盖斜前方障碍物避免漏检）
        self.front_angle_range = 60  # degrees
        self.threshold = 0.5  # meters

    def scan_callback(self, msg: LaserScan):
        n = len(msg.ranges)
        # 计算前向扇区索引
        center = n // 2
        half_window = int(self.front_angle_range / (msg.angle_increment * 180 / 3.14159))
        front_ranges = msg.ranges[center - half_window : center + half_window]
        # 过滤 inf 和 nan
        valid = [r for r in front_ranges if r > msg.range_min and r < msg.range_max]
        if not valid:
            return
        min_front = min(valid)
        warning = Bool()
        warning.data = min_front < self.threshold
        self.publisher.publish(warning)
        if warning.data:
            self.get_logger().warn(f'⚠️ 前向扇区 ±{self.front_angle_range // 2}° 障碍物 {min_front:.2f}m (< {self.threshold}m)')


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
