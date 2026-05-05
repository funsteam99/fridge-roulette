# 🍳 冰箱大轉盤 (Fridge Roulette) - v10.2 Strict & Robust Edition

![AI-Powered](https://img.shields.io/badge/AI-Gemini-orange)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-blue)
![Security](https://img.shields.io/badge/Security-Intent%20Filtered-red)

> **「大廚只專注於美味，其餘雜訊一概不理。」** —— 具備料理意圖過濾的 AI 廚房助手

本專案是一個整合 Google Gemini OpenAI-compatible API 與 Streamlit 的智慧料理應用。使用者可以拍照辨識食材、手動微調清單，或使用快速標籤加入常見食材，再由 AI 產生三道結構化料理建議。

## ✨ 功能亮點

- **🛡️ 料理意圖過濾 (Culinary Intent Filtering)**
  - 自動檢查輸入是否與食材或烹飪相關。
  - 攔截明顯的政治、暴力、仇恨、惡意程式與其他非料理用途輸入。
  - 偵測常見 prompt injection / jailbreak 字句，避免使用者嘗試改寫系統規則。
- **👨‍🍳 兩階段視覺工作流 (Two-Stage Workflow)**
  - Step 1：使用相機拍照，透過多模態模型清點食材。
  - Step 2：將辨識結果回填至文字框，支援手動增刪與快速標籤補充。
  - Step 3：根據最終食材清單生成三道料理。
- **🧠 大廚人格一致性**
  - 影像辨識與食譜生成都維持星級大廚語氣。
- **👤 會員模式**
  - 若設定 Google OAuth 並成功登入，食譜會額外顯示營養分析與養生建議。
  - 未設定 OAuth 時自動以訪客模式運行，不影響核心食譜功能。
- **⚙️ Secrets-first 設定**
  - API key 與模型名稱必須由 Streamlit secrets 指定。
  - 專案不再內建預設模型；缺少 secrets 時會在 UI 顯示錯誤說明。

## 🚀 部署與設定

本專案可部署在 Streamlit Community Cloud，也可在本機執行。

### 必要 Secrets

請在 Streamlit Cloud Secrets 或本機 `.streamlit/secrets.toml` 設定：

```toml
api_key = "YOUR_GOOGLE_API_KEY"
model = "gemini-2.5-flash"
```

若缺少 secrets 檔案，或缺少 `api_key` / `model` 任一欄位，應用程式會停止 AI 功能並顯示設定錯誤。

### 選用 Google OAuth

若需要會員模式，額外加入：

```toml
[google_auth]
cookie_key = "YOUR_COOKIE_KEY"
client_id = "YOUR_GOOGLE_CLIENT_ID"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
redirect_uri = "YOUR_REDIRECT_URI"
```

OAuth 需要搭配 `google_credentials.json`。未設定時會自動降級為訪客模式。

## 🛠️ 技術架構

- **前端介面**：Streamlit + 自定義 CSS
- **AI 引擎**：Google Gemini OpenAI-compatible endpoint
- **安全機制**：本機料理意圖檢查、濫用關鍵字阻擋、prompt injection 字句偵測、系統提示約束
- **資料處理**：JSON object response、Regex 清除 code fences 與 `<thought>` 標籤
- **設定來源**：Streamlit secrets

## ▶️ 本機執行

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

**讓每一份剩食，在安全且智慧的環境中重獲新生。**
