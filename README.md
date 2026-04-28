# 🍳 冰箱大轉盤 (Fridge Roulette) - 星級大廚剩食料理

![Fridge Roulette](https://img.shields.io/badge/AI-Gemini%20%2F%20Gemma-orange)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-blue)
![Deployment](https://img.shields.io/badge/Deployed-Streamlit%20Cloud-green)
![PWA](https://img.shields.io/badge/Mobile-PWA%20Ready-blue)

> **「冰箱裡沒有垃圾，只有還沒被發現的奇蹟。」** —— 20 年資歷創意大廚

這是一個由 AI 驅動的創意料理助手，專門解決「冰箱剩一堆食材卻不知道煮什麼」的世紀難題。透過 Google Gemini 或 Gemma 模型的強大運算力，我們為每一份剩食注入靈魂。

## ✨ 特色功能

- **👨‍🍳 20 年星級大廚人格**：專業、幽默且充滿熱情，設計三道風格迥異的創意料理。
- **📱 原生 APP 體驗 (PWA)**：優化行動端介面，隱藏瀏覽器選單與浮水印，支援「加入主畫面」以全螢幕原生感運行。
- **🧠 大廚內心獨白**：完整呈現 AI 的思考過程 (Thinking Process)，增加生成內容的透明度與趣味性。
- **📸 智慧潛力介面**：預留相機拍照功能介面，展現未來結合視覺辨識的擴充性。
- **⚡ 觸控優化設計**：加入「常用食材快速標籤」與「滿版按鈕」，大幅提升單手操作流暢度。
- **☁️ 雲端自動載入**：支援 Streamlit Secrets，實現「開啟即用」的零設定 Demo 體驗。

## 🚀 快速展示 (Deployment)

本專案已針對 **Streamlit Community Cloud** 深度優化。

### 雲端配置 (Secrets Setting)
請在 Streamlit Cloud 後台設定以下 Secrets：
```toml
api_key = "YOUR_GOOGLE_API_KEY"
default_model = "gemini-1.5-flash"
```

### 📲 手機安裝教學 (推薦)
為獲得最佳體驗，請將此應用程式「安裝」至手機桌面：
- **iOS (Safari)**：點擊「分享」按鈕 > 選擇「加入主畫面」。
- **Android (Chrome)**：點擊「更多 (三個點)」 > 選擇「安裝應用程式」或「加入主畫面」。

## 🛠️ 本地開發

### 1. 複製專案與安裝
```bash
git clone https://github.com/funsteam99/fridge-roulette.git
cd fridge-roulette
pip install -r requirements.txt
```

### 2. 啟動服務
```bash
streamlit run app.py
```

## 📝 技術架構與安全性

- **Frontend**: Streamlit (with Custom CSS Injection)
- **AI Engine**: Google Gemini / Gemma (via OpenAI SDK)
- **State Management**: 使用 Streamlit Callback 模式進行健壯的狀態管理，防止並發操作錯誤。
- **Security**: 具備 Secrets 優先讀取機制，確保 API Key 不會洩漏於源碼或設定檔中。

---
**讓每份剩食都有重生的機會！** 🍷🍽️
