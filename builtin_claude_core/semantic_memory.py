# semantic_memory.py - 语义记忆系统
# 基于 Annoy 向量相似性搜索，实现智能记忆检索

import os
import json
import numpy as np
from annoy import AnnoyIndex
from typing import List, Dict, Optional, Tuple
from .logger import logger

class SemanticMemory:
    """
    语义记忆系统
    基于向量相似性搜索，实现智能记忆检索
    """
    def __init__(self, dimension: int = 384, metric: str = 'angular'):
        self.dimension = dimension
        self.metric = metric
        self.index = AnnoyIndex(dimension, metric)
        self.memory_items = []  # 存储记忆内容
        self.memory_index = 0
        logger.info("✅ 语义记忆系统初始化完成")

    def add_memory(self, content: str, metadata: Optional[Dict] = None):
        """
        添加记忆
        """
        # 生成向量（这里使用简单的字符频率向量作为示例）
        vector = self._generate_vector(content)
        
        # 添加到索引
        self.index.add_item(self.memory_index, vector)
        
        # 存储记忆内容
        memory_item = {
            'content': content,
            'metadata': metadata or {},
            'vector': vector.tolist()
        }
        self.memory_items.append(memory_item)
        
        self.memory_index += 1
        return self.memory_index - 1

    def build_index(self, n_trees: int = 10):
        """
        构建索引
        """
        if self.memory_index > 0:
            try:
                self.index.build(n_trees)
                logger.info(f"✅ 语义记忆索引构建完成，包含 {self.memory_index} 条记忆")
            except Exception as e:
                # 忽略重复构建索引的错误
                if "You can't build a built index" in str(e):
                    logger.debug("⚠️  索引已经构建，跳过重复构建")
                else:
                    logger.error(f"❌ 构建索引失败：{str(e)}")
        else:
            logger.warning("⚠️  没有记忆需要索引")

    def search(self, query: str, top_k: int = 5) -> List[Tuple[float, str, Dict]]:
        """
        搜索相关记忆
        """
        if self.memory_index == 0:
            return []
        
        # 生成查询向量
        query_vector = self._generate_vector(query)
        
        # 搜索相似向量
        indices, distances = self.index.get_nns_by_vector(
            query_vector, top_k, include_distances=True
        )
        
        # 整理结果
        results = []
        for idx, distance in zip(indices, distances):
            if 0 <= idx < len(self.memory_items):
                item = self.memory_items[idx]
                results.append((distance, item['content'], item['metadata']))
        
        return results

    def _generate_vector(self, text: str) -> np.ndarray:
        """
        生成文本向量
        这里使用简单的字符频率向量作为示例
        实际应用中应该使用更先进的文本嵌入模型
        """
        # 简单的字符频率向量
        # 实际应用中应该使用 BERT、Sentence-BERT 等模型
        vector = np.zeros(self.dimension)
        
        # 计算字符频率
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # 填充向量
        for i, (char, count) in enumerate(char_counts.items()):
            if i < self.dimension:
                vector[i] = count
        
        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector

    def save(self, path: str):
        """
        保存记忆
        """
        # 保存索引
        index_path = f"{path}.ann"
        self.index.save(index_path)
        
        # 保存记忆内容
        data_path = f"{path}.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump({
                'memory_items': self.memory_items,
                'memory_index': self.memory_index,
                'dimension': self.dimension,
                'metric': self.metric
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 语义记忆保存到 {path}")

    def load(self, path: str):
        """
        加载记忆
        """
        # 加载记忆内容
        data_path = f"{path}.json"
        if not os.path.exists(data_path):
            logger.error(f"❌ 记忆文件不存在: {data_path}")
            return False
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.memory_items = data['memory_items']
        self.memory_index = data['memory_index']
        self.dimension = data['dimension']
        self.metric = data['metric']
        
        # 重新构建索引
        self.index = AnnoyIndex(self.dimension, self.metric)
        for i, item in enumerate(self.memory_items):
            vector = np.array(item['vector'])
            self.index.add_item(i, vector)
        
        self.build_index()
        logger.info(f"✅ 语义记忆从 {path} 加载完成")
        return True

    def clear(self):
        """
        清空记忆
        """
        self.index = AnnoyIndex(self.dimension, self.metric)
        self.memory_items = []
        self.memory_index = 0
        logger.info("✅ 语义记忆已清空")

    def get_memory_count(self) -> int:
        """
        获取记忆数量
        """
        return self.memory_index

# 全局语义记忆实例
semantic_memory = SemanticMemory()
