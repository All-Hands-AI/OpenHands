"""
OpenHands 编码配置

这个模块集中管理 OpenHands 项目中的所有编码相关配置，
确保跨平台兼容性。
"""

import os
import sys
from typing import List


class EncodingConfig:
    """编码配置类"""
    
    # 默认编码
    DEFAULT_ENCODING = 'utf-8'
    
    # 回退编码列表（按优先级排序）
    FALLBACK_ENCODINGS = [
        'utf-8-sig',  # UTF-8 with BOM
        'latin-1',    # ISO-8859-1, 可以解码任何字节序列
        'cp1252',     # Windows-1252
        'gbk',        # 中文编码
        'big5',       # 繁体中文编码
    ]
    
    # 错误处理方式
    ERROR_HANDLING = 'replace'  # 使用替换字符
    
    # 平台特定配置
    WINDOWS_ENCODINGS = ['cp1252', 'gbk', 'big5']
    UNIX_ENCODINGS = ['utf-8', 'latin-1']
    
    @classmethod
    def get_system_encoding(cls) -> str:
        """获取系统默认编码"""
        return sys.getdefaultencoding()
    
    @classmethod
    def get_preferred_encoding(cls) -> str:
        """获取首选编码"""
        return cls.DEFAULT_ENCODING
    
    @classmethod
    def get_fallback_encodings(cls) -> List[str]:
        """获取回退编码列表"""
        return cls.FALLBACK_ENCODINGS.copy()
    
    @classmethod
    def get_platform_encodings(cls) -> List[str]:
        """获取平台特定的编码列表"""
        if sys.platform == 'win32':
            return cls.WINDOWS_ENCODINGS.copy()
        else:
            return cls.UNIX_ENCODINGS.copy()
    
    @classmethod
    def get_all_encodings(cls) -> List[str]:
        """获取所有可能的编码列表"""
        encodings = [cls.DEFAULT_ENCODING]
        encodings.extend(cls.get_fallback_encodings())
        return encodings
    
    @classmethod
    def is_encoding_supported(cls, encoding: str) -> bool:
        """检查编码是否受支持"""
        try:
            'test'.encode(encoding)
            return True
        except (LookupError, UnicodeError):
            return False


# 全局配置实例
encoding_config = EncodingConfig()


# 便捷函数
def get_default_encoding() -> str:
    """获取默认编码"""
    return encoding_config.get_preferred_encoding()


def get_fallback_encodings() -> List[str]:
    """获取回退编码列表"""
    return encoding_config.get_fallback_encodings()


def get_all_encodings() -> List[str]:
    """获取所有编码列表"""
    return encoding_config.get_all_encodings()


def is_encoding_supported(encoding: str) -> bool:
    """检查编码是否受支持"""
    return encoding_config.is_encoding_supported(encoding)
