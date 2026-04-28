# 🍳 冰箱大轉盤 (Fridge Roulette) - 星級大廚剩食料理

![Fridge Roulette](https://img.shields.io/badge/AI-Gemini%20%2F%20Gemma-orange)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-blue)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)

> **「冰箱裡沒有垃圾，只有還沒被發現的奇蹟。」** —— 20 年資歷創意大廚

這是一個由 AI 驅動的創意料理助手，專門解決「冰箱剩一堆食材卻不知道煮什麼」的世紀難題。透過 Google Gemini 或 Gemma 模型的強大運算力，我們為每一份剩食注入靈魂。

## ✨ 特色功能

- **👨‍🍳 20 年星級大廚人格**：專業、幽默且充滿熱情，為您設計三道風格迥異的創意料理（台式、日式、西式或創意融合）。
- **🧠 大廚內心獨白**：完整呈現 AI 的「思考過程 (Thinking Process)」，讓您知道大廚是如何搭配食材與發想靈感的。
- **🤖 模型自動掃描**：支援 Google OpenAI 相容介面，貼入 Key 後自動掃描您帳號下可用的最新 **Gemini** 與 **Gemma** 模型。
- **💾 自動記憶配置**：您的 API Key、Base URL 與模型偏好會自動儲存在本地 `config.json`，下次啟動無需重新設定。
- **🎲 隨機測試食材**：內建多組測試食材，一鍵啟動抽籤，沒靈感時也能輕鬆玩。
- **🛡️ 穩定解析機制**：具備強大的 JSON 解析與容錯讀取邏輯，不怕 AI 亂翻譯 Key。

## 🚀 快速開始

### 1. 複製專案
```bash
git clone https://github.com/funsteam99/fridge-roulette.git
cd fridge-roulette
```

### 2. 安裝套件
```bash
pip install -r requirements.txt
```

### 3. 取得 Gemini API Key
前往 [Google AI Studio](https://aistudio.google.com/) 申請免費的 API Key。

### 4. 啟動服務
```bash
streamlit run app.py
```

## 🛠️ 技術細節

- **API 模式**：使用 `openai` SDK 存取 Google 的 OpenAI-compatible 模式端點。
- **預設網址**：`https://generativelanguage.googleapis.com/v1beta/openai`
- **解析器**：自定義 `parse_chef_response` 函數，支援處理 `<thought>` 標籤。

## ⚙️ 配置說明

展開左側側邊欄 `❯` 可進行以下設定：
- **API Key**：您的 Google AI 憑證。
- **API 帳號**：預設為 `generativelanguage.googleapis.com` 以利瀏覽器索引。
- **選擇大腦**：可選 `gemini-1.5-flash`, `gemini-1.5-pro` 或最新的 `gemma-2` 系列。

## 📝 免責聲明

雖然大廚擁有 20 年資歷，但料理建議僅供參考。請在烹飪前確保食材尚未過期並符合食品安全標準。如果 AI 建議您煮「草莓炒雞排」，請自行斟酌風險。

---
**讓每份剩食都有重生的機會！** 🍷🍽️
