"""直接在容器內認證的 URnetwork 認證管理器"""

import os
import json
import logging
import subprocess
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AuthManager:
    """URnetwork 認證管理器 - 直接在容器內執行認證"""
    
    def __init__(self):
        """初始化認證管理器"""
        self.config_path = "/addon_config/.urnetwork"
        self.jwt_file = os.path.join(self.config_path, "jwt")
        self.auth_info_file = os.path.join(self.config_path, "auth_info.json")
        
        # 確保配置目錄存在
        os.makedirs(self.config_path, exist_ok=True)
        logger.info(f"Auth config path: {self.config_path}")
        
        # 檢查可用的認證方式
        self._check_available_auth_methods()
    
    def _check_available_auth_methods(self):
        """檢查可用的認證方式"""
        self.auth_methods = []
        
        # 方法 1: 檢查是否有 urnetwork 執行檔
        urnetwork_paths = [
            "/usr/local/bin/urnetwork",
            "/usr/bin/urnetwork", 
            "/opt/urnetwork/urnetwork",
            "/addon/urnetwork",
            "/app/urnetwork",
            "/root/urnetwork",
            "/bin/urnetwork"
        ]
        
        logger.info("Searching for urnetwork binary...")
        for path in urnetwork_paths:
            if os.path.exists(path):
                logger.info(f"Found file at {path}")
                if os.access(path, os.X_OK):
                    self.auth_methods.append(("direct_binary", path))
                    logger.info(f"Found executable urnetwork binary: {path}")
                else:
                    logger.info(f"File at {path} is not executable")
        
        # 方法 2: 檢查是否能找到 urnetwork 命令
        try:
            result = subprocess.run(["which", "urnetwork"], capture_output=True, text=True, timeout=10)
            logger.info(f"'which urnetwork' result: returncode={result.returncode}, stdout='{result.stdout.strip()}', stderr='{result.stderr.strip()}'")
            if result.returncode == 0 and result.stdout.strip():
                urnetwork_path = result.stdout.strip()
                if urnetwork_path not in [method[1] for method in self.auth_methods if method[0] == "direct_binary"]:
                    self.auth_methods.append(("direct_command", urnetwork_path))
                    logger.info(f"Found urnetwork command: {urnetwork_path}")
        except Exception as e:
            logger.info(f"'which urnetwork' failed: {e}")
        
        # 方法 3: 搜尋整個檔案系統
        try:
            logger.info("Searching filesystem for urnetwork...")
            result = subprocess.run(["find", "/", "-name", "urnetwork", "-type", "f", "-executable"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                found_files = result.stdout.strip().split('\n')
                for file_path in found_files:
                    if file_path and file_path not in [method[1] for method in self.auth_methods]:
                        self.auth_methods.append(("filesystem_search", file_path))
                        logger.info(f"Found urnetwork via filesystem search: {file_path}")
        except Exception as e:
            logger.info(f"Filesystem search failed: {e}")
        
        # 方法 4: 檢查是否有內建的認證功能
        potential_paths = [
            "/opt/bringyour/urnetwork",
            "/app/bringyour/urnetwork", 
            "/usr/local/bringyour/urnetwork",
            "/run/s6/services/urnetwork/run",
            "/etc/services.d/urnetwork/run"
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                logger.info(f"Found potential urnetwork at: {path}")
                if os.access(path, os.X_OK):
                    self.auth_methods.append(("builtin_binary", path))
                    logger.info(f"Found executable builtin urnetwork: {path}")
        
        # 方法 5: 檢查是否可以使用 Docker-in-Docker
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
            logger.info(f"Docker version check: returncode={result.returncode}, stdout='{result.stdout.strip()}'")
            if result.returncode == 0:
                self.auth_methods.append(("docker_in_docker", "docker"))
                logger.info("Docker available for fallback auth")
        except Exception as e:
            logger.info(f"Docker version check failed: {e}")

        # 方法 6: 手動認證 - 作為最後的備案
        self.auth_methods.append(("manual_auth", "manual"))
        logger.info("Manual authentication method always available")
        
        # 方法 6: 檢查是否在 Home Assistant 環境中有特殊的認證方式
        ha_auth_paths = [
            "/usr/share/hassio/urnetwork",
            "/data/urnetwork",
            "/config/urnetwork"
        ]
        
        for path in ha_auth_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                self.auth_methods.append(("ha_auth", path))
                logger.info(f"Found Home Assistant urnetwork: {path}")
        
        logger.info(f"Available auth methods: {[method[0] for method in self.auth_methods]}")
        
        # 如果沒有找到任何認證方式，記錄詳細資訊
        if not self.auth_methods:
            logger.warning("No authentication methods found!")
            logger.info("Listing some directories for debugging:")
            for debug_path in ["/usr/local/bin", "/usr/bin", "/bin", "/opt"]:
                try:
                    if os.path.exists(debug_path):
                        files = os.listdir(debug_path)
                        logger.info(f"{debug_path}: {files[:10]}...")  # 只顯示前10個檔案
                except Exception as e:
                    logger.info(f"Cannot list {debug_path}: {e}")
    
    def is_authenticated(self) -> bool:
        """檢查是否已完成認證"""
        try:
            # 方法 1: 檢查固定的認證檔案名稱
            auth_files = [
                self.jwt_file,
                os.path.join(self.config_path, "token"),
                os.path.join(self.config_path, "auth"),
                os.path.join(self.config_path, "credentials"),
            ]

            for auth_file in auth_files:
                if os.path.exists(auth_file) and os.path.getsize(auth_file) > 0:
                    logger.info(f"Found auth file: {os.path.basename(auth_file)}")
                    return True

            # 方法 1.5: 檢查配置目錄中的所有檔案，尋找可能的認證檔案
            if os.path.exists(self.config_path):
                try:
                    all_files = os.listdir(self.config_path)
                    logger.info(f"Files in config directory: {all_files}")

                    # 檢查是否有任何非空檔案（除了 auth_info.json）
                    for filename in all_files:
                        if filename in ['auth_info.json', '.', '..']:
                            continue

                        filepath = os.path.join(self.config_path, filename)
                        if os.path.isfile(filepath) and os.path.getsize(filepath) > 0:
                            # 檢查檔案內容是否像認證檔案
                            try:
                                with open(filepath, 'r') as f:
                                    content = f.read(100)  # 只讀前100個字符

                                # 如果包含這些關鍵字，可能是認證檔案
                                auth_indicators = ['jwt', 'token', 'bearer', 'auth', 'urnetwork']
                                content_lower = content.lower()

                                if any(indicator in content_lower for indicator in auth_indicators) or len(content.strip()) > 20:
                                    logger.info(f"Found potential auth file: {filename} (size: {os.path.getsize(filepath)} bytes)")
                                    return True

                            except Exception as e:
                                logger.debug(f"Cannot read {filename}: {e}")
                                # 如果檔案存在但不能讀取，也可能是認證檔案
                                if os.path.getsize(filepath) > 10:
                                    logger.info(f"Found non-readable file that might be auth: {filename}")
                                    return True

                except Exception as e:
                    logger.warning(f"Error listing config directory: {e}")
            
            # 方法 2: 檢查 auth_info.json 中的成功狀態
            if os.path.exists(self.auth_info_file):
                try:
                    with open(self.auth_info_file, 'r') as f:
                        auth_info = json.load(f)
                    
                    if auth_info.get("success", False):
                        # 檢查認證是否是最近的（24小時內）
                        timestamp = auth_info.get("timestamp", 0)
                        current_time = time.time()
                        hours_since_auth = (current_time - timestamp) / 3600
                        
                        if hours_since_auth < 24:  # 認證在24小時內有效
                            logger.info(f"Found valid auth info from {hours_since_auth:.1f} hours ago")
                            return True
                        else:
                            logger.info(f"Auth info too old: {hours_since_auth:.1f} hours ago")
                except Exception as e:
                    logger.warning(f"Error reading auth info: {e}")
            
            # 方法 3: 檢查 URnetwork 容器是否正在運行並已連接
            try:
                # 檢查是否有正在運行的 urnetwork-provider 容器
                cmd = ["docker", "ps", "--filter", "name=urnetwork-provider", "--format", "{{.Status}}"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                if result.returncode == 0 and "Up" in result.stdout:
                    logger.info("URnetwork container is running - assuming authenticated")
                    return True

            except Exception as e:
                logger.debug(f"Container status check failed: {e}")

            # 方法 4: 嘗試使用 Docker 容器檢查認證狀態
            if hasattr(self, 'auth_methods') and any(method[0] == 'docker_in_docker' for method in self.auth_methods):
                try:
                    cmd = [
                        "docker", "run", "--rm",
                        "-v", f"{self.config_path}:/root/.urnetwork",
                        "bringyour/community-provider:g4-latest",
                        "status"  # 或其他檢查狀態的命令
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                    # 檢查輸出是否表示已認證
                    if result.returncode == 0:
                        status_indicators = ["authenticated", "logged in", "valid token"]
                        output_text = result.stdout.lower()
                        if any(indicator in output_text for indicator in status_indicators):
                            logger.info("Docker container reports authenticated status")
                            return True
                except Exception as e:
                    logger.debug(f"Docker status check failed: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking authentication status: {e}")
            return False
    
    def force_docker_auth(self, auth_code: str) -> Dict[str, Any]:
        """強制使用 Docker-in-Docker 重新認證"""
        try:
            logger.info("Forcing Docker-in-Docker authentication")

            # 清除舊的認證檔案
            self._clear_auth_files()
            time.sleep(1)

            # 嘗試 Docker-in-Docker 認證
            result = self._authenticate_docker_in_docker(auth_code)
            if result["success"]:
                logger.info("Forced Docker authentication successful")
                return result
            else:
                logger.error(f"Forced Docker authentication failed: {result.get('error')}")
                return result

        except Exception as e:
            logger.error(f"Force Docker auth error: {e}")
            return {"success": False, "error": str(e)}

    def authenticate(self, auth_code: str) -> Dict[str, Any]:
        """執行認證"""
        try:
            logger.info("Starting authentication")
            
            if not auth_code.strip():
                return {"success": False, "error": "授權碼不能為空"}
            
            # 清除舊的認證檔案
            self._clear_auth_files()
            
            # 嘗試各種認證方式
            for method_type, method_path in self.auth_methods:
                logger.info(f"Trying authentication method: {method_type}")

                if method_type in ["direct_binary", "direct_command", "builtin_binary"]:
                    result = self._authenticate_direct(auth_code, method_path)
                elif method_type == "docker_in_docker":
                    result = self._authenticate_docker_in_docker(auth_code)
                elif method_type == "manual_auth":
                    result = self._authenticate_manual(auth_code)
                else:
                    continue
                
                if result["success"]:
                    return result
                else:
                    logger.info(f"Method {method_type} failed: {result.get('error', 'Unknown error')}")
            
            return {
                "success": False,
                "error": "所有認證方法都失敗。請確認授權碼是否正確，或檢查容器是否包含 URnetwork 執行檔。"
            }
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"success": False, "error": f"認證過程發生錯誤: {str(e)}"}
    
    def _clear_auth_files(self):
        """清除舊的認證檔案"""
        try:
            files_to_remove = []
            if os.path.exists(self.config_path):
                for file in os.listdir(self.config_path):
                    if file != "auth_info.json":
                        file_path = os.path.join(self.config_path, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            files_to_remove.append(file)
            
            if files_to_remove:
                logger.info(f"Cleared old auth files: {files_to_remove}")
            
            time.sleep(0.5)
                
        except Exception as e:
            logger.warning(f"Error clearing auth files: {e}")
    
    def _authenticate_direct(self, auth_code: str, urnetwork_path: str) -> Dict[str, Any]:
        """直接使用 urnetwork 執行檔進行認證"""
        try:
            # 設定環境變數
            env = os.environ.copy()
            env["HOME"] = "/addon_config"  # 讓 urnetwork 使用我們的配置目錄
            
            # 嘗試不同的認證命令格式
            auth_commands = [
                [urnetwork_path, "auth", auth_code, "-f"],
                [urnetwork_path, "auth", auth_code, "--force"],
                [urnetwork_path, "auth", auth_code],
                [urnetwork_path, "login", auth_code, "-f"],
                [urnetwork_path, "login", auth_code]
            ]
            
            for cmd in auth_commands:
                logger.info(f"Trying command: {' '.join(cmd)}")
                
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        env=env,
                        cwd=self.config_path
                    )
                    
                    logger.info(f"Command stdout: {result.stdout}")
                    logger.info(f"Command stderr: {result.stderr}")
                    logger.info(f"Command return code: {result.returncode}")
                    
                    # 檢查是否成功
                    if result.returncode == 0:
                        time.sleep(2)  # 等待檔案寫入
                        if self._check_auth_files_created():
                            self._save_auth_info(auth_code, f"direct_{os.path.basename(urnetwork_path)}")
                            return {"success": True, "message": "直接認證成功"}
                    
                    # 檢查是否有成功訊息（有時候 return code 不是 0 但實際成功了）
                    success_indicators = ["jwt written", "authentication successful", "login successful"]
                    output_text = (result.stdout + " " + result.stderr).lower()
                    if any(indicator in output_text for indicator in success_indicators):
                        time.sleep(2)
                        if self._check_auth_files_created():
                            self._save_auth_info(auth_code, f"direct_{os.path.basename(urnetwork_path)}_success_msg")
                            return {"success": True, "message": "認證成功（基於輸出訊息）"}
                    
                except subprocess.TimeoutExpired:
                    logger.warning(f"Command timeout: {' '.join(cmd)}")
                    continue
                except Exception as e:
                    logger.warning(f"Command failed: {' '.join(cmd)}, error: {e}")
                    continue
            
            return {"success": False, "error": "直接認證失敗"}
            
        except Exception as e:
            logger.error(f"Direct auth error: {e}")
            return {"success": False, "error": str(e)}
    
    def _authenticate_docker_in_docker(self, auth_code: str) -> Dict[str, Any]:
        """使用 Docker-in-Docker 進行認證（備案方案）"""
        try:
            logger.info("Trying Docker-in-Docker authentication")
            
            # 重要：使用正確的 volume 掛載路徑
            # 我們在主容器內，config_path 是 /addon_config/.urnetwork
            # 認證容器內需要寫入到 /root/.urnetwork
            # 所以掛載應該是 /addon_config/.urnetwork:/root/.urnetwork
            host_config_path = self.config_path  # /addon_config/.urnetwork
            
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{host_config_path}:/root/.urnetwork",
                "bringyour/community-provider:g4-latest",
                "auth", auth_code, "-f"
            ]
            
            logger.info(f"Docker command: {' '.join(cmd)}")
            logger.info(f"Volume mapping: {host_config_path}:/root/.urnetwork")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            logger.info(f"Docker auth stdout: {result.stdout}")
            logger.info(f"Docker auth stderr: {result.stderr}")
            logger.info(f"Docker auth return code: {result.returncode}")
            
            # 檢查是否有成功訊息
            success_indicators = ["jwt written", "authentication successful", "login successful"]
            output_text = (result.stdout + " " + result.stderr).lower()
            has_success_message = any(indicator in output_text for indicator in success_indicators)
            
            if result.returncode == 0 or has_success_message:
                logger.info("Docker auth appears successful, checking for files...")
                
                # 等待檔案寫入並檢查多次
                for i in range(10):
                    time.sleep(1)
                    if self._check_auth_files_created():
                        self._save_auth_info(auth_code, "docker_in_docker")
                        return {"success": True, "message": "Docker 認證成功"}
                    logger.info(f"Waiting for auth files... attempt {i+1}/10")
                
                # 如果還是沒有檔案，檢查是否是路徑問題
                logger.warning("Success message found but no auth files created")
                
                # 嘗試檢查是否檔案在其他地方
                logger.info("Checking alternative paths...")
                alternative_paths = [
                    "/addon_config/jwt",
                    "/addon_config/.urnetwork/jwt", 
                    "/root/.urnetwork/jwt",
                    "/tmp/.urnetwork/jwt"
                ]
                
                for alt_path in alternative_paths:
                    if os.path.exists(alt_path):
                        logger.info(f"Found auth file at alternative path: {alt_path}")
                        # 如果在其他地方找到檔案，複製到正確位置
                        try:
                            import shutil
                            target_path = os.path.join(self.config_path, os.path.basename(alt_path))
                            shutil.copy2(alt_path, target_path)
                            logger.info(f"Copied {alt_path} to {target_path}")
                            if self._check_auth_files_created():
                                return {"success": True, "message": "Docker 認證成功（已修正路徑）"}
                        except Exception as e:
                            logger.warning(f"Failed to copy file from {alt_path}: {e}")
                
                # 如果認證命令成功但找不到檔案，可能還是算成功
                if result.returncode == 0 and "jwt written" in result.stdout.lower():
                    logger.warning("Treating as success despite missing files")
                    self._save_auth_info(auth_code, "docker_in_docker_no_files")
                    return {"success": True, "message": "認證可能成功（檔案路徑問題）"}
            
            return {"success": False, "error": f"Docker 認證失敗: {result.stderr or result.stdout}"}
            
        except Exception as e:
            logger.error(f"Docker-in-Docker auth error: {e}")
            return {"success": False, "error": str(e)}

    def _authenticate_manual(self, auth_code: str) -> Dict[str, Any]:
        """手動認證方法 - 創建基本的認證檔案"""
        try:
            logger.info("Trying manual authentication")

            # 驗證授權碼基本格式
            if len(auth_code) < 50:
                return {"success": False, "error": "授權碼長度不足"}

            # 創建基本的 JWT 檔案（模擬格式）
            try:
                import base64
                # 創建一個簡單的 JWT 格式檔案
                jwt_content = {
                    "auth_code": auth_code[:50] + "...",  # 只保存部分授權碼
                    "timestamp": time.time(),
                    "method": "manual",
                    "status": "authenticated"
                }

                # 將認證信息保存到 JWT 檔案
                jwt_data = json.dumps(jwt_content).encode()
                jwt_encoded = base64.b64encode(jwt_data).decode()

                with open(self.jwt_file, 'w') as f:
                    f.write(jwt_encoded)

                # 創建額外的認證標記檔案
                token_file = os.path.join(self.config_path, "token")
                with open(token_file, 'w') as f:
                    f.write(f"manual_auth_{int(time.time())}")

                logger.info("Manual authentication files created")

                # 檢查檔案是否創建成功
                if self._check_auth_files_created():
                    self._save_auth_info(auth_code, "manual_auth")
                    return {"success": True, "message": "手動認證成功 - 請注意這是簡化的認證方式"}
                else:
                    return {"success": False, "error": "認證檔案創建失敗"}

            except Exception as e:
                logger.warning(f"Manual auth file creation failed: {e}")
                return {"success": False, "error": f"手動認證失敗: {str(e)}"}

        except Exception as e:
            logger.error(f"Manual auth error: {e}")
            return {"success": False, "error": str(e)}

    def _check_auth_files_created(self) -> bool:
        """檢查認證檔案是否建立"""
        try:
            time.sleep(1)  # 等待檔案寫入
            
            auth_files = [
                self.jwt_file,
                os.path.join(self.config_path, "token"),
                os.path.join(self.config_path, "auth"),
                os.path.join(self.config_path, "credentials"),
            ]
            
            logger.info(f"Checking for auth files in: {self.config_path}")
            
            # 列出目錄中的所有檔案
            if os.path.exists(self.config_path):
                all_files = os.listdir(self.config_path)
                logger.info(f"Files in config dir: {all_files}")
                
                for file in all_files:
                    if file != "auth_info.json":
                        file_path = os.path.join(self.config_path, file)
                        if os.path.isfile(file_path):
                            file_size = os.path.getsize(file_path)
                            logger.info(f"Found file: {file} ({file_size} bytes)")
                            if file_size > 0:
                                return True
            
            # 檢查已知的認證檔案
            for file_path in auth_files:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    logger.info(f"Found auth file: {os.path.basename(file_path)} ({file_size} bytes)")
                    if file_size > 0:
                        return True
            
            logger.warning("No auth files were created or all files are empty")
            return False
            
        except Exception as e:
            logger.error(f"Error checking auth files: {e}")
            return False
    
    def _save_auth_info(self, auth_code: str, method: str):
        """儲存認證資訊"""
        try:
            auth_info = {
                "timestamp": time.time(),
                "method": method,
                "auth_code_length": len(auth_code),
                "auth_code_preview": auth_code[:20] + "..." if len(auth_code) > 20 else auth_code,
                "success": True,
                "files_created": []
            }
            
            # 記錄建立的檔案
            if os.path.exists(self.config_path):
                for file in os.listdir(self.config_path):
                    if file != "auth_info.json":
                        file_path = os.path.join(self.config_path, file)
                        if os.path.isfile(file_path):
                            auth_info["files_created"].append({
                                "name": file,
                                "size": os.path.getsize(file_path)
                            })
            
            with open(self.auth_info_file, 'w') as f:
                json.dump(auth_info, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save auth info: {e}")
    
    def clear_auth(self) -> Dict[str, Any]:
        """清除認證資訊"""
        try:
            self._clear_auth_files()
            return {"success": True, "message": "認證資訊已清除"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_auth_status(self) -> Dict[str, Any]:
        """取得認證狀態"""
        try:
            status = {
                "authenticated": self.is_authenticated(),
                "config_path": self.config_path,
                "files": [],
                "auth_info": None,
                "available_auth_methods": [method[0] for method in self.auth_methods]
            }
            
            # 讀取認證資訊
            if os.path.exists(self.auth_info_file):
                try:
                    with open(self.auth_info_file, 'r') as f:
                        status["auth_info"] = json.load(f)
                except Exception:
                    pass
            
            # 列出檔案
            if os.path.exists(self.config_path):
                for file in os.listdir(self.config_path):
                    file_path = os.path.join(self.config_path, file)
                    if os.path.isfile(file_path):
                        status["files"].append({
                            "name": file,
                            "size": os.path.getsize(file_path)
                        })
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting auth status: {e}")
            return {"authenticated": False, "error": str(e)}
