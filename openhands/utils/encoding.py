"""
统一编码配置和工具函数

这个模块提供了 OpenHands 项目中所有文件操作的统一编码配置，
确保跨平台兼容性，特别是在 Windows 系统上。
"""

import os
import sys
from typing import TextIO, BinaryIO, Union, Optional

from openhands.core.encoding_config import encoding_config


# 统一编码配置（从配置类导入）
DEFAULT_ENCODING = encoding_config.DEFAULT_ENCODING
FALLBACK_ENCODINGS = encoding_config.FALLBACK_ENCODINGS
ERROR_HANDLING = encoding_config.ERROR_HANDLING


def get_system_encoding() -> str:
    """获取系统默认编码"""
    return sys.getdefaultencoding()


def get_preferred_encoding() -> str:
    """获取首选的文本编码"""
    return DEFAULT_ENCODING


def get_fallback_encodings() -> list[str]:
    """获取回退编码列表"""
    return FALLBACK_ENCODINGS.copy()


def open_text_file(
    file_path: Union[str, os.PathLike],
    mode: str = 'r',
    encoding: Optional[str] = None,
    errors: str = ERROR_HANDLING,
    **kwargs
) -> TextIO:
    """
    打开文本文件，使用统一的编码配置
    
    Args:
        file_path: 文件路径
        mode: 打开模式 ('r', 'w', 'a', 'r+', 'w+', 'a+')
        encoding: 指定编码，如果为 None 则使用默认配置
        errors: 错误处理方式
        **kwargs: 其他 open() 参数
    
    Returns:
        文件对象
    """
    if encoding is None:
        encoding = get_preferred_encoding()
    
    # 如果是写入模式，确保目录存在
    if 'w' in mode or 'a' in mode or 'x' in mode:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    return open(file_path, mode, encoding=encoding, errors=errors, **kwargs)


def read_text_file(
    file_path: Union[str, os.PathLike],
    encoding: Optional[str] = None,
    fallback_encodings: Optional[list[str]] = None
) -> str:
    """
    读取文本文件，自动尝试多种编码
    
    Args:
        file_path: 文件路径
        encoding: 首选编码
        fallback_encodings: 回退编码列表
    
    Returns:
        文件内容
    
    Raises:
        UnicodeDecodeError: 所有编码都失败时抛出
    """
    if encoding is None:
        encoding = get_preferred_encoding()
    
    if fallback_encodings is None:
        fallback_encodings = encoding_config.get_fallback_encodings()
    
    # 尝试首选编码
    try:
        with open_text_file(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        pass
    
    # 尝试回退编码
    for fallback_encoding in fallback_encodings:
        try:
            with open_text_file(file_path, 'r', encoding=fallback_encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    # 如果所有编码都失败，使用错误替换模式
    try:
        with open_text_file(file_path, 'r', encoding=encoding, errors='replace') as f:
            return f.read()
    except Exception as e:
        raise UnicodeDecodeError(
            encoding, b'', 0, 1, f"Unable to decode file with any encoding: {e}"
        )


def write_text_file(
    file_path: Union[str, os.PathLike],
    content: str,
    encoding: Optional[str] = None,
    **kwargs
) -> None:
    """
    写入文本文件，使用统一的编码配置
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 编码，如果为 None 则使用默认配置
        **kwargs: 其他 open() 参数
    """
    if encoding is None:
        encoding = get_preferred_encoding()
    
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open_text_file(file_path, 'w', encoding=encoding, **kwargs) as f:
        f.write(content)


def open_binary_file(
    file_path: Union[str, os.PathLike],
    mode: str = 'rb',
    **kwargs
) -> BinaryIO:
    """
    打开二进制文件
    
    Args:
        file_path: 文件路径
        mode: 打开模式
        **kwargs: 其他 open() 参数
    
    Returns:
        文件对象
    """
    # 如果是写入模式，确保目录存在
    if 'w' in mode or 'a' in mode or 'x' in mode:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    return open(file_path, mode, **kwargs)


# 便捷函数
def safe_read(file_path: Union[str, os.PathLike]) -> str:
    """安全读取文本文件，自动处理编码问题"""
    return read_text_file(file_path)


def safe_write(file_path: Union[str, os.PathLike], content: str) -> None:
    """安全写入文本文件，使用统一编码"""
    write_text_file(file_path, content)


def safe_open(file_path: Union[str, os.PathLike], mode: str = 'r', **kwargs) -> Union[TextIO, BinaryIO]:
    """安全打开文件，根据模式自动选择文本或二进制模式"""
    if 'b' in mode:
        return open_binary_file(file_path, mode, **kwargs)
    else:
        return open_text_file(file_path, mode, **kwargs)
