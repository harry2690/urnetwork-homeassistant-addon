"""Docker 容器管理器"""

import docker
import json
import logging
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DockerManager:
    """管理 URnetwork Docker 容器"""
    
    def __init__(self):
        """初始化 Docker 客戶端"""
        # 先設定基本屬性
        self.container_name = "urnetwork-provider"
        self.image_name = "bringyour/community-provider:g4-latest"
        self.config_path = "/addon_config/.urnetwork"

        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Docker client initialization failed: {e}")
            self.client = None
    
    def get_container(self) -> Optional[docker.models.containers.Container]:
        """獲取 URnetwork 容器"""
        try:
            if self.client is None:
                return None
            return self.client.containers.get(self.container_name)
        except docker.errors.NotFound:
            logger.debug("URnetwork container not found")
            return None
        except Exception as e:
            logger.error(f"Error getting container: {e}")
            return None
    
    def start_provider(self) -> Dict[str, Any]:
        """啟動 Provider"""
        try:
            if self.client is None:
                return {"success": False, "error": "Docker 連接失敗，無法啟動 Provider"}

            container = self.get_container()
            
            if container is None:
                # 建立新容器
                logger.info("Creating new URnetwork container")
                return self._create_container()
            
            if container.status != "running":
                logger.info("Starting existing container")
                container.start()
                return {"success": True, "message": "Provider 已啟動"}
            else:
                return {"success": True, "message": "Provider 已在運行中"}
                
        except Exception as e:
            logger.error(f"Failed to start provider: {e}")
            return {"success": False, "error": str(e)}
    
    def stop_provider(self) -> Dict[str, Any]:
        """停止 Provider"""
        try:
            if self.client is None:
                return {"success": False, "error": "Docker 連接失敗，無法停止 Provider"}

            container = self.get_container()
            
            if container and container.status == "running":
                logger.info("Stopping URnetwork container")
                container.stop()
                return {"success": True, "message": "Provider 已停止"}
            else:
                return {"success": True, "message": "Provider 未在運行"}
                
        except Exception as e:
            logger.error(f"Failed to stop provider: {e}")
            return {"success": False, "error": str(e)}
    
    def restart_provider(self) -> Dict[str, Any]:
        """重啟 Provider"""
        try:
            if self.client is None:
                return {"success": False, "error": "Docker 連接失敗，無法重啟 Provider"}

            container = self.get_container()
            
            if container:
                logger.info("Restarting URnetwork container")
                container.restart()
                return {"success": True, "message": "Provider 已重啟"}
            else:
                return self.start_provider()
                
        except Exception as e:
            logger.error(f"Failed to restart provider: {e}")
            return {"success": False, "error": str(e)}
    
    def update_provider(self) -> Dict[str, Any]:
        """更新 Provider 映像檔"""
        try:
            if self.client is None:
                return {"success": False, "error": "Docker 連接失敗，無法更新 Provider"}

            logger.info("Updating URnetwork provider image")
            
            # 停止現有容器
            container = self.get_container()
            if container:
                container.stop()
                container.remove()
            
            # 拉取最新映像檔
            self.client.images.pull(self.image_name)
            
            # 重新建立容器
            return self._create_container()
                
        except Exception as e:
            logger.error(f"Failed to update provider: {e}")
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """獲取 Provider 狀態"""
        try:
            if self.client is None:
                return {
                    "status": "docker_unavailable",
                    "message": "Docker 連接失敗",
                    "error": "無法連接到 Docker daemon"
                }

            container = self.get_container()
            
            if container is None:
                return {
                    "status": "not_found",
                    "message": "容器不存在"
                }
            
            # 獲取容器詳細資訊
            container.reload()  # 重新載入容器狀態
            
            return {
                "status": container.status,
                "name": container.name,
                "created": container.attrs.get("Created", "unknown"),
                "started": container.attrs["State"].get("StartedAt", "unknown"),
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "ports": container.ports,
                "health": container.attrs["State"].get("Health", {}).get("Status", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_logs(self, lines: int = 100) -> str:
        """獲取容器日誌"""
        try:
            container = self.get_container()
            
            if container:
                logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
                return logs
            else:
                return "容器不存在或未啟動"
                
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return f"獲取日誌失敗: {str(e)}"
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取容器統計資訊"""
        try:
            container = self.get_container()
            
            if container and container.status == "running":
                stats = container.stats(stream=False)
                return stats
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def _create_container(self) -> Dict[str, Any]:
        """建立新的 URnetwork 容器"""
        try:
            if self.client is None:
                return {"success": False, "error": "Docker 連接失敗，無法創建容器"}

            # 確保配置目錄存在
            subprocess.run(f"mkdir -p {self.config_path}", shell=True, check=True)
            
            # 容器設定
            container_config = {
                "image": self.image_name,
                "name": self.container_name,
                "command": "provide",
                "volumes": {
                    self.config_path: {
                        "bind": "/root/.urnetwork",
                        "mode": "rw"
                    }
                },
                "environment": {
                    "TZ": "Asia/Taipei"
                },
                "restart_policy": {"Name": "unless-stopped"},
                "detach": True,
                "remove": False
            }
            
            logger.info(f"Creating container with config: {container_config}")
            
            # 建立並啟動容器
            container = self.client.containers.run(**container_config)
            
            logger.info(f"Container created successfully: {container.short_id}")
            
            return {
                "success": True, 
                "message": f"容器已建立並啟動: {container.short_id}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            return {"success": False, "error": str(e)}
