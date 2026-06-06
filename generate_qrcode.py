"""
生成通用二维码脚本
"""

import qrcode
import os
import socket
from pathlib import Path

# ===== 获取本机IP =====
def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ===== 配置 =====
LOCAL_IP = get_local_ip()
QR_URL = f"http://{LOCAL_IP}:5000/"  # 本机IP地址
OUTPUT_PATH = Path(__file__).parent / "qrcode.png"

# ===== 生成二维码 =====
def generate_qrcode():
    print("正在生成二维码...")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(QR_URL)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(OUTPUT_PATH)

    print(f"✓ 二维码已生成: {OUTPUT_PATH}")
    print(f"✓ 本机IP: {LOCAL_IP}")
    print(f"✓ 二维码链接: {QR_URL}")
    print("\n使用说明:")
    print("1. 打印此二维码（推荐A5或A6大小）")
    print("2. 贴在办公桌显眼位置")
    print("3. 需要借阅时，用手机扫描二维码")
    print("4. 填写表单即可")

if __name__ == "__main__":
    generate_qrcode()

