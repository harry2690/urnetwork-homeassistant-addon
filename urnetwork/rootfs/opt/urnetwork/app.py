#!/usr/bin/env python3
"""URnetwork Add-on Web UI with Ingress support."""

import os
import sys
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for

# 檢查是否在 Ingress 模式下運行
ingress_path = os.getenv('INGRESS_PATH', '')
ingress_url = os.getenv('INGRESS_URL', '')

# 設定日誌讓 Home Assistant 看得到
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

def log_message(msg):
    """統一日誌輸出"""
    print(f"[URnetwork] {msg}", flush=True)
    print(f"[URnetwork] {msg}", file=sys.stderr, flush=True)

# 記錄 Ingress 資訊
if ingress_path:
    log_message(f"Running with Ingress - Path: {ingress_path}, URL: {ingress_url}")
else:
    log_message("Running in direct mode (no Ingress)")

# 添加 utils 模組到路徑
sys.path.append('/opt/urnetwork')

try:
    from utils.docker_manager import DockerManager
    from utils.auth_manager import AuthManager
    from utils.stats_collector import StatsCollector

    # 管理器實例
    docker_mgr = DockerManager()
    auth_mgr = AuthManager()
    stats_collector = StatsCollector()

    log_message("所有管理器載入成功")
except ImportError as e:
    log_message(f"載入管理器失敗: {e}")
    # 建立假的管理器避免錯誤
    class DummyManager:
        def is_authenticated(self):
            return False
        def get_status(self):
            return {"status": "停止", "message": "模擬狀態"}
        def get_latest_stats(self):
            return {"total_earnings": "0.00", "uptime": "未知", "traffic_served": "0 MB"}
        def authenticate(self, code):
            return {"success": True, "message": "模擬認證成功"}
        def start_provider(self):
            return {"success": True, "message": "模擬啟動"}
        def stop_provider(self):
            return {"success": True, "message": "模擬停止"}
        def restart_provider(self):
            return {"success": True, "message": "模擬重啟"}
        def update_provider(self):
            return {"success": True, "message": "模擬更新"}
        def get_logs(self, lines=100):
            return "URnetwork 模擬日誌輸出\n程式正在運行中...\n等待實際 Docker 容器啟動"
        def get_last_update(self):
            return "2024-01-01 12:00:00"
    
    docker_mgr = DummyManager()
    auth_mgr = DummyManager()
    stats_collector = DummyManager()

# Flask 應用程式
app = Flask(__name__)
app.secret_key = os.urandom(24)

# 如果有 Ingress 路徑，設定相關配置
if ingress_path:
    app.config['APPLICATION_ROOT'] = ingress_path

def make_url(endpoint, **values):
    """生成 URL，支援 Ingress 路徑"""
    if ingress_path and not ingress_url:
        # 使用相對路徑
        return url_for(endpoint, **values)
    elif ingress_url:
        # 使用完整的 Ingress URL
        relative_url = url_for(endpoint, **values)
        return ingress_url.rstrip('/') + relative_url
    else:
        return url_for(endpoint, **values)

# 主要路由
@app.route('/')
def index():
    """主頁面 - 檢查是否已設定"""
    log_message("Accessing main page")
    
    # 檢查是否已完成認證
    if auth_mgr.is_authenticated():
        return redirect(make_url('dashboard'))
    else:
        return redirect(make_url('setup'))

@app.route('/setup')
def setup():
    """設定頁面"""
    log_message("Accessing setup page")
    try:
        return render_template('setup.html')
    except Exception as e:
        log_message(f"Template error: {e}")
        # 如果模板載入失敗，返回基本 HTML
        return f'''
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <title>URnetwork Provider 設定</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .container {{ background: #f5f5f5; padding: 30px; border-radius: 10px; }}
                textarea {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }}
                button {{ background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; }}
                button:hover {{ background: #0056b3; }}
                .status {{ margin-top: 20px; padding: 15px; border-radius: 5px; }}
                .success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                .info {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>URnetwork Provider 初始設定</h1>
                <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h3>設定步驟：</h3>
                    <ol>
                        <li>前往 <a href="https://ur.io" target="_blank">ur.io</a> 登入你的帳號</li>
                        <li>點擊「Copy an Auth Code」按鈕</li>
                        <li>將授權碼貼到下方欄位</li>
                        <li>點擊「開始設定」完成認證</li>
                    </ol>
                </div>
                
                <form id="authForm">
                    <label for="authCode"><strong>授權碼 (Auth Code):</strong></label><br>
                    <textarea id="authCode" rows="4" placeholder="請在此貼上從 ur.io 複製的授權碼..." required></textarea><br>
                    <button type="submit">開始設定</button>
                </form>
                <div id="status"></div>
            </div>
            
            <script>
            document.getElementById('authForm').onsubmit = async function(e) {{
                e.preventDefault();
                const code = document.getElementById('authCode').value.trim();
                const status = document.getElementById('status');
                
                if (!code) {{
                    status.innerHTML = '<div class="status error">請輸入授權碼</div>';
                    return;
                }}
                
                status.innerHTML = '<div class="status info">正在設定中，請稍候...</div>';
                
                try {{
                    const response = await fetch('{make_url("authenticate")}', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{auth_code: code}})
                    }});
                    const result = await response.json();
                    
                    if (result.success) {{
                        status.innerHTML = '<div class="status success">設定成功！正在跳轉到控制台...</div>';
                        setTimeout(() => window.location.href = '{make_url("dashboard")}', 2000);
                    }} else {{
                        status.innerHTML = '<div class="status error">設定失敗: ' + result.error + '</div>';
                    }}
                }} catch (error) {{
                    status.innerHTML = '<div class="status error">設定過程發生錯誤: ' + error + '</div>';
                }}
            }};
            </script>
        </body>
        </html>
        '''

@app.route('/dashboard')
def dashboard():
    """控制台頁面"""
    log_message("Accessing dashboard")
    
    # 檢查認證狀態
    if not auth_mgr.is_authenticated():
        return redirect(make_url('setup'))
    
    # 獲取狀態資訊
    status = docker_mgr.get_status()
    stats = stats_collector.get_latest_stats()
    
    try:
        return render_template('dashboard.html', status=status, stats=stats)
    except Exception as e:
        log_message(f"Dashboard template error: {e}")
        # 簡單的控制台 HTML
        return f'''
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <title>URnetwork Provider 控制台</title>
            <meta http-equiv="refresh" content="30">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
                .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; }}
                .controls {{ margin: 20px 0; }}
                .btn {{ background: #007bff; color: white; padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }}
                .btn:hover {{ background: #0056b3; }}
                .btn-danger {{ background: #dc3545; }}
                .btn-danger:hover {{ background: #c82333; }}
                .btn-warning {{ background: #ffc107; color: #212529; }}
                .btn-warning:hover {{ background: #e0a800; }}
                .logs {{ background: #f8f9fa; padding: 20px; border-radius: 10px; height: 300px; overflow-y: auto; font-family: monospace; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>URnetwork Provider 控制台</h1>
                <p>即時監控和管理你的 URnetwork 提供者服務</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>服務狀態</h3>
                    <p><strong>{status.get("status", "未知")}</strong></p>
                </div>
                <div class="stat-card">
                    <h3>總收益</h3>
                    <p><strong>${stats.get("total_earnings", "0.00")} USDC</strong></p>
                </div>
                <div class="stat-card">
                    <h3>運行時間</h3>
                    <p><strong>{stats.get("uptime", "未知")}</strong></p>
                </div>
                <div class="stat-card">
                    <h3>流量貢獻</h3>
                    <p><strong>{stats.get("traffic_served", "0 MB")}</strong></p>
                </div>
            </div>
            
            <div class="controls">
                <h2>服務控制</h2>
                <button class="btn" onclick="controlProvider('start')">啟動 Provider</button>
                <button class="btn btn-danger" onclick="controlProvider('stop')">停止 Provider</button>
                <button class="btn btn-warning" onclick="controlProvider('restart')">重啟 Provider</button>
                <button class="btn" onclick="controlProvider('update')">更新 Provider</button>
            </div>
            
            <div>
                <h2>系統日誌 <button class="btn" onclick="loadLogs()" style="font-size: 12px; padding: 5px 10px;">重新整理</button></h2>
                <div id="logs" class="logs">載入中...</div>
            </div>
            
            <script>
            async function controlProvider(action) {{
                try {{
                    const response = await fetch('{make_url("provider_control", action="") }' + action, {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}}
                    }});
                    const result = await response.json();
                    
                    if (result.success) {{
                        alert('操作成功: ' + result.message);
                    }} else {{
                        alert('操作失敗: ' + result.error);
                    }}
                    setTimeout(() => location.reload(), 1000);
                }} catch (error) {{
                    alert('操作失敗: ' + error);
                }}
            }}
            
            async function loadLogs() {{
                try {{
                    const response = await fetch('{make_url("get_logs")}');
                    const result = await response.json();
                    document.getElementById('logs').textContent = result.logs;
                }} catch (error) {{
                    document.getElementById('logs').textContent = '無法載入日誌: ' + error;
                }}
            }}
            
            // 自動更新狀態
            setInterval(function() {{
                fetch('{make_url("get_status")}')
                .then(response => response.json())
                .then(data => {{
                    // 這裡可以更新狀態顯示
                    console.log('Status updated:', data);
                }})
                .catch(error => console.error('Status update error:', error));
            }}, 30000);
            
            // 頁面載入時獲取日誌
            loadLogs();
            setInterval(loadLogs, 10000);
            </script>
        </body>
        </html>
        '''

# API 路由
@app.route('/api/auth', methods=['POST'])
def authenticate():
    """處理認證請求"""
    try:
        data = request.get_json()
        auth_code = data.get('auth_code', '').strip()
        
        if not auth_code:
            return jsonify({'success': False, 'error': '請提供認證碼'}), 400
        
        log_message("Processing authentication request")
        
        # 執行認證
        result = auth_mgr.authenticate(auth_code)
        
        if result['success']:
            log_message("Authentication successful")
            return jsonify({'success': True, 'message': '認證成功！'})
        else:
            log_message(f"Authentication failed: {result.get('error', 'Unknown error')}")
            return jsonify({'success': False, 'error': result['error']}), 400
            
    except Exception as e:
        log_message(f"Authentication error: {e}")
        return jsonify({'success': False, 'error': '認證過程發生錯誤'}), 500

@app.route('/api/force-docker-auth', methods=['POST'])
def force_docker_auth():
    """強制使用 Docker 重新認證"""
    try:
        data = request.get_json()
        auth_code = data.get('auth_code', '').strip()

        if not auth_code:
            return jsonify({'success': False, 'error': '請提供認證碼'}), 400

        log_message("Processing forced Docker authentication")

        # 執行強制 Docker 認證
        result = auth_mgr.force_docker_auth(auth_code)

        if result['success']:
            log_message("Forced Docker authentication successful")
            return jsonify({'success': True, 'message': '強制 Docker 認證成功！'})
        else:
            log_message(f"Forced Docker authentication failed: {result.get('error', 'Unknown error')}")
            return jsonify({'success': False, 'error': result['error']}), 400

    except Exception as e:
        log_message(f"Forced Docker authentication error: {e}")
        return jsonify({'success': False, 'error': '強制認證過程發生錯誤'}), 500

@app.route('/api/provider/<action>', methods=['POST'])
def provider_control(action):
    """Provider 控制 API"""
    try:
        log_message(f"Provider control action: {action}")
        
        if action == 'start':
            result = docker_mgr.start_provider()
        elif action == 'stop':
            result = docker_mgr.stop_provider()
        elif action == 'restart':
            result = docker_mgr.restart_provider()
        elif action == 'update':
            result = docker_mgr.update_provider()
        else:
            return jsonify({'success': False, 'error': '無效的操作'}), 400
        
        return jsonify(result)
        
    except Exception as e:
        log_message(f"Provider control error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """獲取 Provider 狀態"""
    try:
        status = docker_mgr.get_status()
        stats = stats_collector.get_latest_stats()
        
        return jsonify({
            'status': status,
            'stats': stats,
            'timestamp': stats_collector.get_last_update()
        })
        
    except Exception as e:
        log_message(f"Status retrieval error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """獲取日誌"""
    try:
        logs = docker_mgr.get_logs()
        return jsonify({'logs': logs})
        
    except Exception as e:
        log_message(f"Log retrieval error: {e}")
        return jsonify({'logs': f'無法載入日誌: {str(e)}'})

# 健康檢查端點
@app.route('/health')
def health_check():
    """健康檢查"""
    return jsonify({
        'status': 'healthy',
        'ingress_mode': bool(ingress_path),
        'ingress_path': ingress_path,
        'ingress_url': ingress_url
    })

if __name__ == '__main__':
    # 從環境變數讀取設定
    port = int(os.getenv('URNETWORK_WEB_PORT', '8099'))
    log_level = os.getenv('URNETWORK_LOG_LEVEL', 'info')
    
    log_message(f"Starting URnetwork Add-on Web UI on port {port}")
    log_message(f"Log level: {log_level}")
    
    # 設定 Flask 日誌等級
    if log_level.lower() in ['trace', 'debug']:
        app.logger.setLevel(logging.DEBUG)
        debug_mode = True
    else:
        app.logger.setLevel(logging.INFO)
        debug_mode = False
    
    # 啟動 Flask 應用程式
    app.run(host='0.0.0.0', port=port, debug=debug_mode)