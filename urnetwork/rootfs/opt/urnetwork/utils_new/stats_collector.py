"""統計資料收集器"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StatsCollector:
    """收集和解析 URnetwork 統計資料"""
    
    def __init__(self):
        """初始化統計收集器"""
        self.last_update = None
        self.cached_stats = {}
    
    def get_latest_stats(self) -> Dict[str, Any]:
        """獲取最新統計資料"""
        try:
            # 這裡可以從 Docker 容器日誌中解析統計資料
            # 目前返回基本資料
            
            from .docker_manager import DockerManager
            docker_mgr = DockerManager()
            
            # 獲取容器日誌
            logs = docker_mgr.get_logs(lines=50)
            
            # 解析日誌中的統計資料
            stats = self._parse_logs_for_stats(logs)
            
            # 獲取容器統計資料
            container_stats = docker_mgr.get_stats()
            if container_stats:
                stats.update(self._parse_container_stats(container_stats))
            
            self.cached_stats = stats
            self.last_update = datetime.now().isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error collecting stats: {e}")
            return self.cached_stats or {}
    
    def _parse_logs_for_stats(self, logs: str) -> Dict[str, Any]:
        """從日誌中解析統計資料"""
        stats = {
            "total_earnings": "0.00",
            "traffic_served": "0 MB",
            "uptime": "未知",
            "connection_status": "未知",
            "client_id": "未知",
            "instance_id": "未知"
        }
        
        try:
            # 解析 client_id
            client_id_match = re.search(r'client_id:\s*([a-f0-9\-]+)', logs)
            if client_id_match:
                stats["client_id"] = client_id_match.group(1)
            
            # 解析 instance_id
            instance_id_match = re.search(r'instance_id:\s*([a-f0-9\-]+)', logs)
            if instance_id_match:
                stats["instance_id"] = instance_id_match.group(1)
            
            # 解析連線狀態
            if "Provider" in logs and "started" in logs:
                stats["connection_status"] = "已連線"
            elif "failed" in logs.lower():
                stats["connection_status"] = "連線失敗"
            
            # 解析成功的網路片段
            success_matches = re.findall(r'success=(\d+)', logs)
            if success_matches:
                total_success = sum(int(match) for match in success_matches)
                stats["successful_connections"] = str(total_success)
            
            # 解析錯誤
            error_matches = re.findall(r'error=(\d+)', logs)
            if error_matches:
                total_errors = sum(int(match) for match in error_matches)
                stats["connection_errors"] = str(total_errors)
            
        except Exception as e:
            logger.error(f"Error parsing logs: {e}")
        
        return stats
    
    def _parse_container_stats(self, container_stats: Dict[str, Any]) -> Dict[str, Any]:
        """解析容器統計資料"""
        parsed_stats = {}
        
        try:
            # 記憶體使用
            if 'memory' in container_stats:
                memory_usage = container_stats['memory'].get('usage', 0)
                memory_limit = container_stats['memory'].get('limit', 0)
                
                if memory_limit > 0:
                    memory_percent = (memory_usage / memory_limit) * 100
                    parsed_stats["memory_usage"] = f"{memory_percent:.1f}%"
                    parsed_stats["memory_usage_mb"] = f"{memory_usage / 1024 / 1024:.1f} MB"
            
            # CPU 使用
            if 'cpu_stats' in container_stats and 'precpu_stats' in container_stats:
                cpu_stats = container_stats['cpu_stats']
                precpu_stats = container_stats['precpu_stats']
                
                cpu_usage = self._calculate_cpu_percent(cpu_stats, precpu_stats)
                if cpu_usage is not None:
                    parsed_stats["cpu_usage"] = f"{cpu_usage:.1f}%"
            
            # 網路統計
            if 'networks' in container_stats:
                networks = container_stats['networks']
                total_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
                total_tx = sum(net.get('tx_bytes', 0) for net in networks.values())
                
                parsed_stats["network_rx"] = f"{total_rx / 1024 / 1024:.1f} MB"
                parsed_stats["network_tx"] = f"{total_tx / 1024 / 1024:.1f} MB"
        
        except Exception as e:
            logger.error(f"Error parsing container stats: {e}")
        
        return parsed_stats
    
    def _calculate_cpu_percent(self, cpu_stats: Dict, precpu_stats: Dict) -> Optional[float]:
        """計算 CPU 使用百分比"""
        try:
            cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
            system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
            
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(cpu_stats['cpu_usage']['percpu_usage']) * 100
                return max(0, min(100, cpu_percent))
        
        except (KeyError, ZeroDivisionError, TypeError) as e:
            logger.debug(f"Error calculating CPU percent: {e}")
        
        return None
    
    def get_last_update(self) -> Optional[str]:
        """獲取最後更新時間"""
        return self.last_update
    
    def clear_cache(self):
        """清除快取"""
        self.cached_stats = {}
        self.last_update = None
