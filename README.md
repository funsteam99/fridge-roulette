# 🍳 冰箱大轉盤 (Fridge Roulette) - v8.0 星級大廚視覺辨識版

![AI-Powered](https://img.shields.io/badge/AI-Gemma%20%2F%20Gemini-orange)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-blue)
![PWA](https://img.shields.io/badge/Mobile-PWA%20Ready-green)
![Stability](https://img.shields.io/badge/Status-Robust%20Parsing-brightgreen)

> **「大廚不僅有手藝，更有看一眼食材就能成菜的靈感。」** —— 專為剩食打造的 AI 廚房助手

本專案是一個深度整合 Google 多模態模型與 Streamlit 的智慧料理應用。透過 **v8.0 兩階段辨識流程**，使用者可以先拍攝冰箱照片，由 AI 大廚初步清點食材後，進行人工微調，最後產出三道五星級創意食譜。

## ✨ v8.0 重大更新與功能亮點

- **👨‍🍳 兩階段辨識流程 (Two-Stage Workflow)**：
  - **Step 1 視覺清點**：利用多模態模型（如 Gemma 4 或 Gemini 1.5）掃描照片。
  - **Step 2 人工微調**：自動將辨識結果填入清單，支援使用者編輯與標籤補充。
  - **Step 3 創意料理**：根據最終確認的清單生成結構化食譜。
- **🧠 大廚人格化影像辨識**：影像辨識提示詞經過精心設計（Prompt Engineering），使 AI 以專業大廚口吻掃描食材。
- **🛡️ 系統健壯性 (Robustness)**：
  - **強效 JSON 解析**：內建 Regex 過濾機制，可從模型混亂的回傳中精準提取食譜數據。
  - **標籤掃除技術**：自動偵測並過濾 `<thought>` 思考標籤與 Markdown 代碼塊，確保介面純淨。
  - **頻率限制保護**：針對 API 429 錯誤提供優雅的降級提示與模型切換建議。
- **📱 極簡 PWA 體驗**：
  - 隱藏所有 Streamlit 官方浮水印與選單。
  - 支援「加入主畫面」，提供全螢幕的原生 APP 操控感。

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
- **AI 引擎**: Google Gemma 4 / Gemini 1.5 Pro & Flash
- **資料處理**: 兩階段 Regex 過濾 + 容錯 JSON 解析引擎
- **狀態管理**: Streamlit Callback 異步狀態同步模式

---
**讓每一份剩食，在 AI 大廚的眼中重獲新生！** 🍷🍽️
