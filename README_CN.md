# URnetwork Provider Add-on

**Languages:** [English](README.md) | [中文](README_CN.md) | [日本語](README_JP.md)

URnetwork 社群提供者插件讓你的 Home Assistant 成為 URnetwork 網路的一部分，共享網路資源並賺取收益。

## 功能特色

- 🌐 成為 URnetwork 社群提供者
- 💰 透過共享網路資源賺取收益
- 📊 即時監控連線狀態和統計資料
- 🔒 安全的認證機制
- 🎛️ 簡單易用的 Web 管理介面

## 安裝步驟

1. 將此儲存庫加入到你的 Home Assistant Add-on 商店
2. 安裝 "URnetwork Provider" 插件
3. 啟動保護模式
4. 啟動插件
5. 透過 Web 介面進行初始設定

## 配置選項

### 基本設定

- **ssl**: 是否啟用 SSL (預設: false)
- **certfile**: SSL 憑證檔案名稱
- **keyfile**: SSL 私鑰檔案名稱
- **web_port**: Web 介面埠號 (預設: 8099)
- **log_level**: 日誌記錄等級

## 認證流程

1. 訪問插件的 Web 介面
2. 輸入從 URnetwork 取得的授權碼
3. 系統會自動驗證並建立連線
4. 認證成功後即可開始提供服務

## 故障排除

### 認證失敗
- 確認授權碼正確
- 檢查網路連線
- 查看日誌檔案了解詳細錯誤

## 支援

如有問題或建議，請至 GitHub Issues 回報。

### 推薦連結與支援
- ur.io 推薦連結：https://ur.io/app?bonus=J8C8CV
- 想請我喝杯咖啡嗎？ USDC BASE 鏈錢包地址：0x040F0037C6a4C28DC504d718Ca9329eFBF6fD8d1

## 授權條款

MIT License