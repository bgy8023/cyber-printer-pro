
import os
import time
import subprocess
import sys
from datetime import datetime
from .logger import logger


class KairosDaemon:
    """
    Kairos Mode：Claude Code泄露源码原生实现的持久守护进程
    轻量级定时守护，平时休眠，到点唤醒，零CPU占用，自动日更
    """
    def __init__(self, gen_hour: int = 3, chapter_file: str = "current_chapter.txt", script_path: str = None):
        self.gen_hour = gen_hour
        self.chapter_file = os.path.abspath(chapter_file)
        self.script_path = script_path if script_path else os.path.abspath("cyber_printer_ultimate.py")
        self.running = True
        logger.info(f"✅ Kairos守护进程初始化完成，每日凌晨{gen_hour}点自动生成")

    def get_current_chapter(self) -&gt; int:
        """获取当前章节号"""
        if not os.path.exists(self.chapter_file):
            with open(self.chapter_file, "w", encoding="utf-8") as f:
                f.write("1")
            return 1
        try:
            with open(self.chapter_file, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except Exception as e:
            logger.error(f"❌ 章节号读取失败：{str(e)}", exc_info=True)
            return 1

    def update_chapter(self, new_chapter: int):
        """更新章节号"""
        try:
            with open(self.chapter_file, "w", encoding="utf-8") as f:
                f.write(str(new_chapter))
            logger.info(f"✅ 章节号已更新：{new_chapter}")
        except Exception as e:
            logger.error(f"❌ 章节号更新失败：{str(e)}", exc_info=True)

    def run_generation(self, chapter_num: int) -&gt; bool:
        """执行章节生成"""
        logger.info(f"🚀 开始自动生成第{chapter_num}章")
        try:
            result = subprocess.run(
                [sys.executable, self.script_path, "--chapter", str(chapter_num), "--words", "7500"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=600
            )
            if result.returncode == 0:
                logger.info(f"✅ 第{chapter_num}章自动生成完成")
                logger.info(f"📝 生成日志：{result.stdout}")
                return True
            else:
                logger.error(f"❌ 第{chapter_num}章生成失败，错误：{result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ 生成执行异常：{str(e)}", exc_info=True)
            return False

    def run(self):
        """守护进程主循环"""
        logger.info("🚀 Kairos守护进程已启动")
        last_gen_date = None

        while self.running:
            try:
                current_time = datetime.now()
                current_hour = current_time.hour
                current_date = current_time.date()

                if current_hour == self.gen_hour and current_date != last_gen_date:
                    chapter_num = self.get_current_chapter()
                    success = self.run_generation(chapter_num)
                    if success:
                        self.update_chapter(chapter_num + 1)
                        last_gen_date = current_date
                        time.sleep(79200)
                    else:
                        time.sleep(3600)
                else:
                    time.sleep(60)

            except KeyboardInterrupt:
                logger.info("🛑 收到停止信号，Kairos守护进程正在退出")
                self.running = False
            except Exception as e:
                logger.error(f"❌ 守护进程异常：{str(e)}", exc_info=True)
                time.sleep(60)

        logger.info("✅ Kairos守护进程已停止")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--hour", type=int, default=3, help="每日自动生成时间（小时）")
    parser.add_argument("--chapter-file", type=str, default="current_chapter.txt", help="章节号文件路径")
    args = parser.parse_args()

    daemon = KairosDaemon(gen_hour=args.hour, chapter_file=args.chapter_file)
    daemon.run()
