import os
import sqlite3
import json
import time
from .logger import logger

class SQLiteMemoryPalace:
    def __init__(self, novel_name="默认小说"):
        self.novel_name = novel_name
        self.base_dir = os.path.join("novel_settings", novel_name)
        os.makedirs(self.base_dir, exist_ok=True)
        self.db_path = os.path.join(self.base_dir, "memory.db")
        self.old_json_path = os.path.join(self.base_dir, "03-动态剧情记忆.json")
        
        self._clear_stale_lock()
        self._init_db()
        self._migrate_old_json_data()
        self._init_fixed_memory()

    def _clear_stale_lock(self):
        lock_files = [f"{self.db_path}-lock", f"{self.db_path}-journal"]
        for lock_file in lock_files:
            if os.path.exists(lock_file):
                file_age = time.time() - os.path.getmtime(lock_file)
                if file_age > 600:
                    try:
                        os.unlink(lock_file)
                        logger.warning(f"🚨 清理超时SQLite锁文件：{lock_file}")
                    except Exception as e:
                        logger.error(f"清理锁文件失败：{e}")

    def _init_db(self):
        with sqlite3.connect(self.db_path, timeout=15.0, check_same_thread=False) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chapter_memory (
                    chapter_num INTEGER PRIMARY KEY,
                    summary TEXT NOT NULL,
                    word_count INTEGER NOT NULL,
                    full_content TEXT,
                    generate_time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chapter_desc
                ON chapter_memory (chapter_num DESC)
            """)
            conn.commit()
        logger.info(f"✅ SQLite记忆宫殿初始化完成：{self.db_path}")

    def _migrate_old_json_data(self):
        if not os.path.exists(self.old_json_path):
            return
        try:
            with open(self.old_json_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
            chapters = old_data.get("chapters", [])
            if not chapters:
                return
            
            with sqlite3.connect(self.db_path, timeout=15.0) as conn:
                for ch in chapters:
                    conn.execute("""
                        INSERT OR IGNORE INTO chapter_memory
                        (chapter_num, summary, word_count) VALUES (?, ?, ?)
                    """, (ch.get("num"), ch.get("summary"), ch.get("words", 0)))
                conn.commit()
            
            os.rename(self.old_json_path, f"{self.old_json_path}.bak.migrated")
            logger.info(f"✅ 旧JSON数据迁移完成，共迁移{len(chapters)}章历史数据")
        except Exception as e:
            logger.error(f"旧JSON数据迁移失败：{e}")

    def _init_fixed_memory(self):
        self.fixed_memory = {}
        for key, fname in [
            ("outline", "00-全本大纲.md"),
            ("character", "01-人物档案.md"),
            ("worldview", "02-世界观设定.md")
        ]:
            fpath = os.path.join(self.base_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    self.fixed_memory[key] = f.read()

    def get_fixed_prompt(self):
        return "\n".join([f"## {k.upper()}\n{v}" for k, v in self.fixed_memory.items() if v])

    def get_dynamic_prompt(self, limit=3):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT chapter_num, summary
                    FROM chapter_memory
                    ORDER BY chapter_num DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                if not rows:
                    return "无前置剧情"
                return "\n".join([f"第{r[0]}章: {r[1]}" for r in reversed(rows)])
        except Exception as e:
            logger.error(f"SQL查询失败：{e}")
            return "无前置剧情"

    def safe_update(self, chapter_num, summary, word_count, full_content=None):
        try:
            with sqlite3.connect(self.db_path, timeout=15.0, check_same_thread=False) as conn:
                conn.execute("""
                    INSERT INTO chapter_memory (chapter_num, summary, word_count, full_content)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(chapter_num) DO UPDATE SET
                    summary=excluded.summary,
                    word_count=excluded.word_count,
                    full_content=excluded.full_content,
                    generate_time=CURRENT_TIMESTAMP
                """, (chapter_num, summary, word_count, full_content))
                conn.commit()
            logger.info(f"✅ 章节{chapter_num}记忆已极速写入SQLite")
            return True
        except Exception as e:
            logger.error(f"SQLite写入失败：{e}")
            raise e

    def get_chapter_history(self, limit=100):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT chapter_num, summary, word_count, generate_time
                    FROM chapter_memory
                    ORDER BY chapter_num DESC
                    LIMIT ?
                """, (limit,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取章节历史失败：{e}")
            return []
