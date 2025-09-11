#!/usr/bin/env python3
"""URnetwork Add-on Web UI."""

import os
import sys
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for

# 添加 utils 模組到路徑
sys.path.append('/opt/urnetwork')

from utils.docker_manager import DockerManager
from utils.auth_manager import AuthManager
from utils.stats_collector import StatsCollector

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask 應用程式
app = Flask(__name__)
app.secret_key = os.urandom(24)

# 管理器實例
docker_mgr = DockerManager()
auth_mgr = AuthManager()
stats_collector = StatsCollector()

@app.route('/')
def index():
    """主頁面 - 檢查是否已設定"""
    logger.info("Accessing main page")
    
    # 檢查是否已完成認證
    if auth_mgr.is_authenticated():
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('setup'))

@app.route('/setup')
def setup():
    """設定頁面"""
    logger.info("Accessing setup page")
    return render_template('setup.html')

@app.route('/dashboard')
def dashboard():
    """控制台頁面"""
    logger.info("Accessing dashboard")
    
    # 檢查認證狀態
    if not auth_mgr.is_authenticated():
        return redirect(url_for('setup'))
    
    # 獲取狀態資訊
    status = docker_mgr.get_status()
    stats = stats_collector.get_latest_stats()
    
    return render_template('dashboard.html', 
                         status=status, 
                         stats=stats)

@app.route('/api/auth', methods=['POST'])
def authenticate():
    """處理認證請求"""
    try:
        data = request.get_json()
        auth_code = data.get('auth_code', '').strip()
        
        if not auth_code:
            return jsonify({'success': False, 'error': '請提供認證碼'}), 400
        
        logger.info("Processing authentication request")
        
        # 執行認證
        result = auth_mgr.authenticate(auth_code)
        
        if result['success']:
            logger.info("Authentication successful")
            return jsonify({'success': True, 'message': '認證成功！'})
        else:
            logger.error(f"Authentication failed: {result['error']}")
            return jsonify({'success': False, 'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return jsonify({'success': False, 'error': '認證過程發生錯誤'}), 500

@app.route('/api/provider/<action>', methods=['POST'])
def provider_control(action):
    """Provider 控制 API"""
    try:
        logger.info(f"Provider control action: {action}")
        
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
        logger.error(f"Provider control error: {e}")
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
        logger.error(f"Status retrieval error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """獲取日誌"""
    try:
        logs = docker_mgr.get_logs(lines=100)
        return jsonify({'logs': logs})
        
    except Exception as e:
        logger.error(f"Log retrieval error: {e}")
        return jsonify({'logs': f'無法載入日誌: {str(e)}'})

if __name__ == '__main__':
    logger.info("Starting URnetwork Add-on Web UI on port 8099")
    app.run(host='0.0.0.0', port=8099, debug=False)
