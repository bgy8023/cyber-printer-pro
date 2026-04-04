
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from .logger import logger


@dataclass
class GenerationMetrics:
    """生成任务指标"""
    chapter_num: int
    target_words: int
    actual_words: int
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_msg: Optional[str] = None
    agent_times: Dict[str, float] = None
    
    def __post_init__(self):
        if self.agent_times is None:
            self.agent_times = {}


class MetricsCollector:
    """
    性能监控收集器
    收集生成任务的性能指标，支持导出和可视化
    """
    def __init__(self, metrics_dir: str = "logs/metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.metrics_dir / "generation_metrics.jsonl"
        self.current_metrics: Optional[GenerationMetrics] = None
        self.agent_start_times: Dict[str, float] = {}
        logger.info("✅ MetricsCollector 初始化完成")

    def start_generation(self, chapter_num: int, target_words: int) -> GenerationMetrics:
        """开始记录生成任务"""
        self.current_metrics = GenerationMetrics(
            chapter_num=chapter_num,
            target_words=target_words,
            actual_words=0,
            start_time=time.time(),
            end_time=0,
            duration=0,
            success=False
        )
        logger.info(f"📊 开始记录第{chapter_num}章生成指标")
        return self.current_metrics

    def start_agent(self, agent_name: str):
        """记录 Agent 开始时间"""
        self.agent_start_times[agent_name] = time.time()
        logger.debug(f"⏱️ Agent {agent_name} 开始计时")

    def end_agent(self, agent_name: str):
        """记录 Agent 结束时间"""
        if agent_name in self.agent_start_times:
            duration = time.time() - self.agent_start_times[agent_name]
            if self.current_metrics:
                self.current_metrics.agent_times[agent_name] = duration
            logger.debug(f"⏱️ Agent {agent_name} 耗时：{duration:.2f}秒")

    def end_generation(self, actual_words: int, success: bool, error_msg: Optional[str] = None):
        """结束记录生成任务"""
        if self.current_metrics:
            self.current_metrics.end_time = time.time()
            self.current_metrics.duration = self.current_metrics.end_time - self.current_metrics.start_time
            self.current_metrics.actual_words = actual_words
            self.current_metrics.success = success
            self.current_metrics.error_msg = error_msg
            
            # 保存指标
            self._save_metrics(self.current_metrics)
            
            # 输出统计
            self._log_summary()
            
            logger.info(f"📊 第{self.current_metrics.chapter_num}章生成指标记录完成")

    def _save_metrics(self, metrics: GenerationMetrics):
        """保存指标到文件"""
        try:
            with open(self.metrics_file, 'a', encoding='utf-8') as f:
                metrics_dict = asdict(metrics)
                metrics_dict['timestamp'] = datetime.now().isoformat()
                f.write(json.dumps(metrics_dict, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"❌ 指标保存失败：{str(e)}")

    def _log_summary(self):
        """输出指标摘要"""
        if self.current_metrics:
            m = self.current_metrics
            logger.info(f"📈 生成统计：")
            logger.info(f"   章节：第{m.chapter_num}章")
            logger.info(f"   目标字数：{m.target_words}")
            logger.info(f"   实际字数：{m.actual_words}")
            logger.info(f"   完成率：{m.actual_words/m.target_words*100:.1f}%")
            logger.info(f"   总耗时：{m.duration:.2f}秒")
            logger.info(f"   平均速度：{m.actual_words/m.duration:.1f}字/秒")
            logger.info(f"   状态：{'✅ 成功' if m.success else '❌ 失败'}")
            
            if m.agent_times:
                logger.info(f"   Agent耗时：")
                for agent, duration in m.agent_times.items():
                    logger.info(f"      {agent}: {duration:.2f}秒")

    def get_recent_metrics(self, n: int = 10) -> List[Dict[str, Any]]:
        """获取最近的 n 条指标"""
        metrics = []
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-n:]:
                        metrics.append(json.loads(line.strip()))
        except Exception as e:
            logger.error(f"❌ 读取指标失败：{str(e)}")
        return metrics

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        all_metrics = self.get_recent_metrics(1000)  # 获取最近1000条
        
        if not all_metrics:
            return {"message": "暂无数据"}
        
        total_chapters = len(all_metrics)
        successful_chapters = sum(1 for m in all_metrics if m.get('success', False))
        total_words = sum(m.get('actual_words', 0) for m in all_metrics)
        total_duration = sum(m.get('duration', 0) for m in all_metrics)
        
        return {
            "总章节数": total_chapters,
            "成功章节数": successful_chapters,
            "成功率": f"{successful_chapters/total_chapters*100:.1f}%",
            "总字数": total_words,
            "总耗时": f"{total_duration/60:.1f}分钟",
            "平均速度": f"{total_words/total_duration:.1f}字/秒" if total_duration > 0 else "0字/秒",
            "平均每章字数": f"{total_words/total_chapters:.0f}字" if total_chapters > 0 else "0字"
        }

    def export_report(self, filepath: str):
        """导出性能报告"""
        try:
            stats = self.get_statistics()
            recent = self.get_recent_metrics(50)
            
            report = {
                "生成时间": datetime.now().isoformat(),
                "统计摘要": stats,
                "最近50章详情": recent
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📊 性能报告已导出：{filepath}")
        except Exception as e:
            logger.error(f"❌ 报告导出失败：{str(e)}")
