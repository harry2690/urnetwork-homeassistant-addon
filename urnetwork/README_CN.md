# URnetwork Provider Add-on

將您的 Home Assistant 變成 URnetwork 的網路提供者，為去中心化網路做出貢獻並賺取 USDC 獎勵。

## 安裝步驟

### 1. 添加 Add-on Repository

在 Home Assistant 中：

1. 進入 **設定** → **Add-ons** → **Add-on Store**
2. 點選右上角的三個點選單
3. 選擇 **Repositories**
4. 添加此 repository URL：`https://github.com/harry2690/urnetwork-homeassistant-addon`
5. 點擊 **Add**

### 2. 安裝 Add-on

1. 重新整理 Add-on Store
2. 找到 **URnetwork Provider**
3. 點擊 **Install**
4. 等待安裝完成

### 3. 重要：關閉保護模式

⚠️ **此步驟非常重要** - URnetwork Add-on 需要存取 Docker 來管理容器

1. 在 Add-on 頁面中，點擊 **Configuration** 標籤
2. **關閉 "Protection mode"** 選項
3. 點擊 **Save**

### 4. 啟動 Add-on

1. 返回 **Info** 標籤
2. 點擊 **Start**
3. 可選：啟用 **Start on boot** 自動啟動
4. 可選：啟用 **Watchdog** 自動重啟

## 配置選項

在 Add-on 的 **Configuration** 頁面中可以調整以下設定：

```yaml
ssl: false                 # 是否啟用 SSL
certfile: fullchain.pem    # SSL 憑證檔案
keyfile: privkey.pem       # SSL 私鑰檔案
web_port: 8099            # Web UI 埠號
log_level: info           # 日誌等級 (trace/debug/info/notice/warning/error/fatal)
```

### 預設配置

大多數情況下，預設設定即可正常使用。除非有特殊需求，否則不需要修改配置。

## 認證流程

### 1. 取得認證碼

1. 前往 [ur.io](https://ur.io)
2. 註冊或登入您的帳戶
3. 取得您的認證碼 (Authentication Code)

### 2. 初次認證

1. 啟動 Add-on 後，點擊 **Open Web UI**
2. 您會看到設定頁面
3. 輸入從 ur.io 取得的認證碼
4. 點擊 **認證**
5. 等待認證完成

### 3. 重新認證（如果需要）

如果遇到認證問題：

1. 在 Dashboard 中點擊 **重新認證** 按鈕
2. 輸入您的原始認證碼
3. 系統會使用 Docker 進行真實認證
4. 完成後重啟 Provider 容器

### 4. 驗證連接

認證完成後：
- 檢查 Dashboard 中的容器狀態
- 前往 [ur.io](https://ur.io) 確認您的客戶端顯示為 "Connected"
- 查看系統日誌確認沒有認證錯誤

## Web UI 功能

Access the Web UI at `http://[HOME_ASSISTANT_IP]:8099`

- **Dashboard**：監控 Provider 狀態和獎勵
- **容器控制**：啟動、停止、重啟、更新 URnetwork Provider
- **系統日誌**：查看運行日誌和錯誤訊息
- **重新認證**：在遇到認證問題時重新進行認證

## 常見問題

### 容器無法啟動

1. 確認已關閉保護模式
2. 檢查 Docker 服務是否正常運行
3. 查看 Add-on 日誌了解錯誤訊息

### 認證失敗

1. 確認認證碼正確
2. 使用 "重新認證" 功能
3. 確認網路連接正常

### 無法存取 Web UI

1. 檢查埠號設定（預設 8099）
2. 確認防火牆設定
3. 嘗試重新啟動 Add-on

## 支援與回饋

### 回報問題

如果遇到問題，請：

1. 檢查 Add-on 日誌
2. 到 [GitHub Issues](https://github.com/harry2690/urnetwork-homeassistant-addon/issues) 回報
3. 提供詳細的錯誤訊息和日誌

### 贊助

歡迎使用我的推薦碼加入ur.io: [https://ur.io/app?bonus=J8C8CV](https://ur.io/app?bonus=J8C8CV)

或是請我喝杯咖啡: [BASE鍊] 0x040F0037C6a4C28DC504d718Ca9329eFBF6fD8d1

### 社群支援

- URnetwork 官方文件：[ur.io](https://ur.io)
- Home Assistant 社群討論

## 授權條款

本專案採用 MIT 授權條款。

### 第三方授權

- URnetwork Provider：請參考 URnetwork 官方授權條款
- Home Assistant Add-on 架構：Apache 2.0 License

---

**免責聲明**：使用本 Add-on 前請確保您了解 URnetwork 的服務條款和隱私政策。網路提供者服務可能會消耗您的網路頻寬和電力。