
import os
from filelock import FileLock
from typing import Optional, Any, ContextManager
from .logger import logger


class FileLockManager:
    """
    文件锁管理器
    解决并发读写冲突，确保记忆宫殿文件的安全操作
    """
    def __init__(self, lock_dir: str = ".locks"):
        self.lock_dir = lock_dir
        os.makedirs(self.lock_dir, exist_ok=True)
        self.locks: dict[str, FileLock] = {}
        logger.info("✅ FileLockManager 初始化完成")

    def get_lock_path(self, file_path: str) -> str:
        """获取锁文件路径"""
        filename = os.path.basename(file_path)
        lock_filename = f"{filename}.lock"
        return os.path.join(self.lock_dir, lock_filename)

    def acquire_lock(self, file_path: str, timeout: float = 30.0) -> Optional[FileLock]:
        """获取文件锁"""
        lock_path = self.get_lock_path(file_path)
        lock = FileLock(lock_path)
        
        try:
            logger.debug(f"🔒 尝试获取文件锁：{file_path}")
            lock.acquire(timeout=timeout)
            self.locks[file_path] = lock
            logger.debug(f"✅ 文件锁获取成功：{file_path}")
            return lock
        except Exception as e:
            logger.error(f"❌ 文件锁获取失败：{file_path}，错误：{str(e)}")
            return None

    def release_lock(self, file_path: str):
        """释放文件锁"""
        if file_path in self.locks:
            try:
                lock = self.locks[file_path]
                lock.release()
                del self.locks[file_path]
                logger.debug(f"🔓 文件锁已释放：{file_path}")
            except Exception as e:
                logger.error(f"❌ 文件锁释放失败：{file_path}，错误：{str(e)}")

    def with_lock(self, file_path: str, timeout: float = 30.0) -> ContextManager:
        """上下文管理器，自动获取和释放锁"""
        lock_path = self.get_lock_path(file_path)
        return FileLock(lock_path, timeout=timeout)

    def is_locked(self, file_path: str) -> bool:
        """检查文件是否被锁定"""
        lock_path = self.get_lock_path(file_path)
        return os.path.exists(lock_path)

    def clear_all_locks(self):
        """清除所有锁"""
        for file_path in list(self.locks.keys()):
            self.release_lock(file_path)
        
        # 清理锁文件
        for lock_file in os.listdir(self.lock_dir):
            lock_path = os.path.join(self.lock_dir, lock_file)
            if lock_file.endswith(".lock"):
                try:
                    os.remove(lock_path)
                    logger.debug(f"🗑️  已清理锁文件：{lock_file}")
                except Exception as e:
                    logger.error(f"❌ 清理锁文件失败：{lock_file}，错误：{str(e)}")


# 全局文件锁管理器实例
lock_manager = FileLockManager()
