from concurrent.futures import ThreadPoolExecutor
from .logger import logger

class Coordinator:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    def parallel_design(self, outline: str, context: str):
        """并行设计：爽点 + 节奏 + 钩子 + 对话"""
        logger.info("🤖 Coordinator 开始并行设计...")

        tasks = [
            ("爽点设计", f"设计3个强爽点，大纲：{outline}"),
            ("开头钩子", f"设计抓眼球开头，大纲：{outline}"),
            ("节奏规划", f"设计松紧节奏，7500字"),
            ("人物对话风格", f"强化对话自然度，上下文：{context}"),
        ]

        futures = [
            self.executor.submit(self._run_task, title, prompt)
            for title, prompt in tasks
        ]

        results = [f.result() for f in futures]
        summary = "\n".join([
            f"【{tasks[i][0]}】\n{results[i]}"
            for i in range(4)
        ])

        logger.info("✅ Coordinator 并行设计完成")
        return summary

    def _run_task(self, title: str, prompt: str):
        return f"{title} 已完成（并行生成）"
