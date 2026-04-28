# 🍳 冰箱大轉盤 (Fridge Roulette) - v8.1 智慧安全辨識版

![AI-Powered](https://img.shields.io/badge/AI-Gemma%20%2F%20Gemini-orange)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-blue)
![PWA](https://img.shields.io/badge/Mobile-PWA%20Ready-green)
![Security](https://img.shields.io/badge/Security-Intent%20Filtered-red)

> **「大廚只專注於美味，其餘雜訊一概不理。」** —— 具備自動意圖防護的 AI 廚房助手

本專案是一個深度整合 Google 多模態模型與 Streamlit 的智慧料理應用。透過 **v8.1 安全辨識流程**，系統不僅能從照片與文字中發掘料理靈感，更能有效過濾無關或惡意輸入，確保服務的穩定與安全。

## ✨ v8.1 重大更新與功能亮點

- **🛡️ 料理意圖過濾 (Culinary Intent Filtering)**：
  - **自動偵測**：系統會自動判斷輸入內容是否與「食材」或「烹飪」相關。
  - **濫用防護**：有效攔截政治、暴力、仇恨言論或惡意程式碼等不當輸入。
  - **防範越獄 (Anti-Jailbreak)**：內建保護機制，拒絕執行嘗試改變大廚人格或繞過安全規範的指令。
- **👨‍🍳 兩階段視覺工作流 (Two-Stage Workflow)**：
  - **Step 1 視覺清點**：利用多模態模型掃描照片，自動提取食材列表。
  - **Step 2 人工微調**：結果回填至文字框，支援手動增刪與標籤補充。
  - **Step 3 創意料理**：根據最終確認清單生成三道結構化食譜。
- **🧠 大廚人格一致性**：無論是影像辨識還是食譜生成，皆維持一致的星級大廚專業語氣。
- **📱 極簡 PWA 體驗**：支援「加入主畫面」，提供全螢幕運行的原生 APP 感。
- **⚡ 系統健壯性**：具備強效 JSON 解析與 `<thought>` 標籤過濾技術，確保介面呈現完美結果。

## 🚀 雲端部署 (Deployment)

本專案已針對 **Streamlit Community Cloud** 完美優化。

### 雲端 Secret 設定
請於後台設定以下變數以實現自動載入：
```toml
api_key = "YOUR_GOOGLE_API_KEY"
default_model = "gemini-1.5-flash"
```

### 手機安裝方式
- **iOS (Safari)**：分享 > 「加入主畫面」。
- **Android (Chrome)**：選單 > 「安裝應用程式」。

## 🛠️ 技術架構

- **前端介面**: Streamlit (自定義 CSS 注入)
- **AI 引擎**: Google Gemma 4 / Gemini 1.5 系列
- **安全機制**: 內建系統級意圖分析與內容審核邏輯
- **資料處理**: 容錯 JSON 解析引擎 + Regex 內容清洗

---
**讓每一份剩食，在安全且智慧的環境中重獲新生！** 🍷🍽️
