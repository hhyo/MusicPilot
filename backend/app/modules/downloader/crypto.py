"""
网易云音乐加密工具
处理网易云音乐 API 的加密和签名
"""
import hashlib
import random
import base64
from typing import Dict, Any


def encrypted_id(id_str: str) -> str:
    """
    加密歌曲 ID

    Args:
        id_str: 歌曲 ID

    Returns:
        加密后的 ID
    """
    # 网易云音乐的加密算法
    magic = '3go8&$8*3*3h0k(2)2'
    song_id = str(id_str)
    magic_len = 18
    song_id_len = len(song_id)
    magic_id = ''

    for i in range(song_id_len):
        magic_id += chr(ord(song_id[i]) ^ ord(magic[i % magic_len]))

    encrypted = hashlib.new('md5')
    encrypted.update(magic_id.encode('utf-8'))
    result = encrypted.hexdigest()

    # 将结果转换为特定格式
    magic_str = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    output = ''

    for i in range(len(result)):
        char = result[i]
        index = magic_str.find(char)
        if index != -1:
            output += magic_str[(index + 6) % len(magic_str)]
        else:
            output += char

    return output


def create_params(params: Dict[str, Any]) -> str:
    """
    创建加密参数

    Args:
        params: 参数字典

    Returns:
        加密后的参数字符串
    """
    import json
    import random

    # 转换为 JSON 字符串
    text = json.dumps(params, separators=(',', ':'), ensure_ascii=False)

    # 加密密钥
    key = '0CoJUm6Qyw8W8jud'

    # 第一轮 AES 加密
    def aes_encrypt(text: str, key: str) -> str:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad

        iv = '0102030405060708'
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
        encrypted = cipher.encrypt(pad(text.encode('utf-8'), 16))
        return base64.b64encode(encrypted).decode('utf-8')

    # 第二轮加密，使用随机密钥
    random_key = ''.join(random.sample('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 16))
    encrypted = aes_encrypt(text, key)
    encrypted = aes_encrypt(encrypted, random_key)

    return encrypted


def create_signature(params: str, timestamp: int) -> str:
    """
    创建签名

    Args:
        params: 加密后的参数
        timestamp: 时间戳

    Returns:
        签名
    """
    # 注意：真实的网易云音乐签名算法更复杂
    # 这里提供一个简化版本

    def md5_encrypt(text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    # 网易云音乐的签名密钥（需要从 JavaScript 提取）
    secret = '6a25c4b8f9d3e7a1c2b4d6f8e9a0b3c'

    signature = md5_encrypt(params + str(timestamp) + secret)

    return signature


def get_common_params() -> Dict[str, Any]:
    """
    获取通用参数

    Returns:
        通用参数字典
    """
    return {
        'timestamp': int(__import__('time').time() * 1000),
    }