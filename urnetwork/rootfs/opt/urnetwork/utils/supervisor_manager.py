"""Home Assistant Supervisor API 管理器"""

import os
import json
import logging
import requests
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SupervisorManager:
    """使用 Home Assistant Supervisor API 管理容器"""

    def __init__(self):
        """初始化 Supervisor API 客戶端"""
        self.supervisor_url = "http://supervisor/docker"
        self.hassio_token = os.environ.get('SUPERVISOR_TOKEN')
        self.container_name = "urnetwork-provider"
        self.image_name = "bringyour/community-provider:g4-latest"
        self.config_path = "/addon_config/.urnetwork"

        if not self.hassio_token:
            logger.warning("SUPERVISOR_TOKEN not found, container management may not work")
            self.hassio_token = None

        self.headers = {
            "Authorization": f"Bearer {self.hassio_token}",
            "Content-Type": "application/json"
        } if self.hassio_token else {}

        logger.info(f"SupervisorManager initialized with token: {'✓' if self.hassio_token else '✗'}")

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """發送 Supervisor API 請求"""
        try:
            if not self.hassio_token:
                logger.error("No SUPERVISOR_TOKEN available")
                return None

            url = f"{self.supervisor_url}/{endpoint}"
            logger.info(f"Making {method} request to: {url}")

            response = requests.request(
                method,
                url,
                headers=self.headers,
                json=data,
                timeout=30
            )

            logger.info(f"Response status: {response.status_code}")

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"API request error: {e}")
            return None

    def get_container_info(self) -> Optional[Dict]:
        """獲取容器資訊"""
        try:
            # 先列出所有容器
            containers = self._make_request("GET", "containers/json")
            if not containers:
                return None

            # 尋找我們的容器
            for container in containers:
                if self.container_name in container.get("Names", []):
                    return container

            logger.info(f"Container {self.container_name} not found")
            return None

        except Exception as e:
            logger.error(f"Error getting container info: {e}")
            return None

    def start_provider(self) -> Dict[str, Any]:
        """啟動 Provider 容器"""
        try:
            if not self.hassio_token:
                return {"success": False, "error": "無 Supervisor API 存取權限"}

            # 檢查容器是否已存在
            container_info = self.get_container_info()

            if container_info:
                # 容器存在，檢查狀態
                if container_info.get("State") == "running":
                    return {"success": True, "message": "Provider 已在運行中"}
                else:
                    # 啟動現有容器
                    result = self._make_request("POST", f"containers/{container_info['Id']}/start")
                    if result is not None:
                        return {"success": True, "message": "Provider 已啟動"}
                    else:
                        return {"success": False, "error": "無法啟動現有容器"}
            else:
                # 創建新容器
                return self._create_container()

        except Exception as e:
            logger.error(f"Failed to start provider: {e}")
            return {"success": False, "error": str(e)}

    def _create_container(self) -> Dict[str, Any]:
        """創建新的 Provider 容器"""
        try:
            # 確保配置目錄存在
            subprocess.run(f"mkdir -p {self.config_path}", shell=True, check=True)

            # 容器設定
            container_config = {
                "Image": self.image_name,
                "Cmd": ["provide"],
                "Env": ["TZ=Asia/Taipei"],
                "HostConfig": {
                    "Binds": [f"{self.config_path}:/root/.urnetwork:rw"],
                    "RestartPolicy": {"Name": "unless-stopped"}
                },
                "name": self.container_name
            }

            logger.info(f"Creating container with config: {json.dumps(container_config, indent=2)}")

            # 創建容器
            result = self._make_request("POST", "containers/create", container_config)
            if not result:
                return {"success": False, "error": "無法創建容器"}

            container_id = result.get("Id")
            if not container_id:
                return {"success": False, "error": "未獲得容器 ID"}

            # 啟動容器
            start_result = self._make_request("POST", f"containers/{container_id}/start")
            if start_result is not None:
                logger.info(f"Container created and started: {container_id}")
                return {"success": True, "message": f"Provider 容器已創建並啟動: {container_id[:12]}"}
            else:
                return {"success": False, "error": "容器創建成功但啟動失敗"}

        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            return {"success": False, "error": str(e)}

    def stop_provider(self) -> Dict[str, Any]:
        """停止 Provider 容器"""
        try:
            if not self.hassio_token:
                return {"success": False, "error": "無 Supervisor API 存取權限"}

            container_info = self.get_container_info()
            if not container_info:
                return {"success": True, "message": "容器未運行"}

            if container_info.get("State") != "running":
                return {"success": True, "message": "容器已停止"}

            result = self._make_request("POST", f"containers/{container_info['Id']}/stop")
            if result is not None:
                return {"success": True, "message": "Provider 已停止"}
            else:
                return {"success": False, "error": "無法停止容器"}

        except Exception as e:
            logger.error(f"Failed to stop provider: {e}")
            return {"success": False, "error": str(e)}

    def restart_provider(self) -> Dict[str, Any]:
        """重啟 Provider 容器"""
        try:
            if not self.hassio_token:
                return {"success": False, "error": "無 Supervisor API 存取權限"}

            container_info = self.get_container_info()
            if not container_info:
                return self.start_provider()

            result = self._make_request("POST", f"containers/{container_info['Id']}/restart")
            if result is not None:
                return {"success": True, "message": "Provider 已重啟"}
            else:
                return {"success": False, "error": "無法重啟容器"}

        except Exception as e:
            logger.error(f"Failed to restart provider: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """獲取 Provider 狀態"""
        try:
            if not self.hassio_token:
                return {
                    "status": "no_api_access",
                    "message": "無 Supervisor API 存取權限",
                    "error": "缺少 SUPERVISOR_TOKEN"
                }

            container_info = self.get_container_info()
            if not container_info:
                return {
                    "status": "not_found",
                    "message": "容器不存在"
                }

            state = container_info.get("State", "unknown")
            return {
                "status": state,
                "name": container_info.get("Names", [None])[0],
                "id": container_info.get("Id", "unknown")[:12],
                "image": container_info.get("Image", "unknown"),
                "created": container_info.get("Created", "unknown")
            }

        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"status": "error", "error": str(e)}

    def get_logs(self) -> str:
        """獲取容器日誌"""
        try:
            if not self.hassio_token:
                return "無 Supervisor API 存取權限"

            container_info = self.get_container_info()
            if not container_info:
                return "容器不存在"

            # 使用 Supervisor API 獲取日誌
            logs_url = f"containers/{container_info['Id']}/logs?stdout=1&stderr=1&tail=100"
            result = self._make_request("GET", logs_url)

            if result:
                return result.get("logs", "無日誌")
            else:
                return "無法獲取日誌"

        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return f"獲取日誌失敗: {str(e)}"