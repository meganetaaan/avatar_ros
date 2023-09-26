import rclpy
from rclpy.node import Node
from tkinter import Tk
from std_msgs.msg import Float32

from .avatar import AvatarFace  # 適切なインポートに変更してください

INTERVAL = 30


class AvatarNode(Node):
    def __init__(self):
        super().__init__('avatar')

        # Tkinterのセットアップ
        self.root = Tk()
        self.avatar = AvatarFace(self.root)

        # ROS2のサブスクリプション
        self.mouth_subscription = self.create_subscription(
            Float32,
            'mouth',
            self.callback_mouth,
            10
        )

        # ROS2のタイマーでTkinterのイベントループを定期的に更新
        self.timer = self.create_timer(
            INTERVAL / 1000, self.update)  # 10msごとに更新

    def callback_mouth(self, msg):
        self.get_logger().info('Received mouth data: %f' % msg.data)
        self.avatar.face_renderer.current_context['mouth']['open'] = msg.data

    def update(self):
        if not self.avatar.is_alive():
            self.destroy_node()
            return

        self.root.update_idletasks()
        self.root.update()
        self.avatar.face_renderer.update(INTERVAL)


def main(args=None):
    rclpy.init(args=args)
    node = AvatarNode()

    while rclpy.ok() and node.avatar.is_alive():
        rclpy.spin_once(node)
    node.get_logger().info("Shutting down")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
