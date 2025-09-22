# URnetwork Provider アドオン

**言語:** [English](README.md) | [中文](README_CN.md) | [日本語](README_JP.md)

URnetwork Provider アドオンを使用すると、Home Assistant が URnetwork の一部となり、ネットワークリソースを共有して報酬を得ることができます。

## 特徴

* 🌐 URnetwork コミュニティプロバイダーになる
* 💰 ネットワークリソースを共有して報酬を得る
* 📊 接続状況と統計のリアルタイム監視
* 🔒 安全な認証機構
* 🎛️ 使いやすい Web 管理インターフェース

## インストール手順

1. このリポジトリを Home Assistant Add-on ストアに追加
2. **URnetwork Provider** アドオンをインストール
3. 保護モードを有効化
4. アドオンを起動
5. Web インターフェースから初期設定を完了

## 設定オプション

### 基本設定

* **ssl**: SSL を有効にするかどうか (デフォルト: false)
* **certfile**: SSL 証明書ファイル名
* **keyfile**: SSL 秘密鍵ファイル名
* **web\_port**: Web インターフェースのポート番号 (デフォルト: 8099)
* **log\_level**: ログレベル

## 認証プロセス

1. アドオンの Web インターフェースにアクセス
2. URnetwork から取得した認証コードを入力
3. システムが自動的に検証し、接続を確立
4. 認証が成功すると、サービスの提供が可能に

## トラブルシューティング

### 認証失敗

* 認証コードが正しいか確認
* ネットワーク接続を確認
* 詳細なエラーについてはログファイルを確認

## サポート

ご質問やご提案がある場合は、GitHub Issues にてご報告ください。

### 推薦リンク & サポート

* UR.io 推薦リンク: [https://ur.io/app?bonus=J8C8CV](https://ur.io/app?bonus=J8C8CV)
* コーヒーをご馳走していただけますか？USDC BASE ウォレットアドレス: `0x040F0037C6a4C28DC504d718Ca9329eFBF6fD8d1`

## ライセンス

MIT License
