# 🍳 冰箱大轉盤 (Fridge Roulette) - 星級大廚剩食料理

![Fridge Roulette](https://img.shields.io/badge/AI-Gemini%20%2F%20Gemma-orange)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-blue)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Deployment](https://img.shields.io/badge/Deployed-Streamlit%20Cloud-green)

> **「冰箱裡沒有垃圾，只有還沒被發現的奇蹟。」** —— 20 年資歷創意大廚

這是一個由 AI 驅動的創意料理助手，專門解決「冰箱剩一堆食材卻不知道煮什麼」的世紀難題。透過 Google Gemini 或 Gemma 模型的強大運算力，我們為每一份剩食注入靈魂。

## ✨ 特色功能

- **👨‍🍳 20 年星級大廚人格**：專業、幽默且充滿熱情，設計三道風格迥異的創意料理。
- **🧠 大廚內心獨白**：完整呈現 AI 的思考過程 (Thinking Process)，增加生成內容的透明度與趣味性。
- **☁️ 雲端優化部署**：支援 Streamlit Secrets，部署後自動載入 API Key 與預設模型，實現「開啟即用」的零設定體驗。
- **🤖 自動模型掃描**：支援自動掃描帳號下可用的最新 Gemini 與 Gemma 模型。
- **💾 混合儲存機制**：優先讀取雲端 Secrets，本地環境則自動使用 `config.json` 記憶配置。
- **🛡️ 強大解析引擎**：內建針對 LLM 回傳格式的容錯解析與 Strict Keys 機制。

## 🚀 快速展示 (Deployment)

本專案已優化為可直接部署於 **Streamlit Community Cloud**。

### 雲端配置 (Secrets Setting)
若要實現自動載入，請在 Streamlit Cloud 後台設定以下 Secrets：
```toml
api_key = "YOUR_GOOGLE_API_KEY"
default_model = "gemini-1.5-flash"
```

## 🛠️ 本地開發

### 1. 複製專案
```bash
git clone https://github.com/funsteam99/fridge-roulette.git
cd fridge-roulette
```

### 2. 安裝套件
```bash
pip install -r requirements.txt
```

### 3. 啟動服務
```bash
streamlit run app.py
```

## 📝 技術架構

- **Frontend**: Streamlit
- **AI Engine**: Google Gemini / Gemma (via OpenAI SDK)
- **Data Format**: Strict JSON with Fallback Parsing Logic

---
**讓每份剩食都有重生的機會！** 🍷🍽️
