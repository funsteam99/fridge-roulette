import streamlit as st
from openai import OpenAI
import json
import os
import re
import random
import base64
try:
    from streamlit_google_auth import Authenticate
except ImportError:
    Authenticate = None

# --- 常數設定 ---
CONFIG_FILE = "config.json"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"

# --- 測試食材樣品 ---
TEST_SAMPLES = [
    "半盒豆腐, 剩一半的炸雞, 三根蔥, 一顆雞蛋",
    "兩片吐司, 一罐鮪魚罐頭, 半顆洋蔥, 沒喝完的牛奶",
    "一把空心菜, 昨晚剩的白飯, 兩條香腸, 少許沙茶醬",
    "三顆馬鈴薯, 半顆高麗菜, 一小塊豬肉, 剩下一點點的起司"
]

# --- 頁面配置 ---
st.set_page_config(
    page_title="冰箱大轉盤", 
    page_icon="🍳", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS 美化 (PWA 感) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { bottom: 50px; }
    .stButton>button { border-radius: 12px; height: 3.5em; font-weight: 600; transition: 0.3s; }
    .stButton>button:hover { border-color: #ff4b4b; color: #ff4b4b; }
    .stTextArea textarea { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 初始化 Session State ---
if "api_key" not in st.session_state:
    st.session_state.api_key = st.secrets.get("api_key") or ""

if "available_models" not in st.session_state:
    base_models = ["gemini-1.5-flash", "gemini-1.5-pro"]
    if "default_model" in st.secrets:
        if st.secrets["default_model"] not in base_models:
            base_models.insert(0, st.secrets["default_model"])
    st.session_state.available_models = base_models

if "ingredients_input" not in st.session_state:
    st.session_state["ingredients_input"] = random.choice(TEST_SAMPLES)

# --- Google Auth 初始化 ---
authenticator = None
if "google_auth" in st.secrets and Authenticate:
    try:
        authenticator = Authenticate(
            secret_credentials_path='google_credentials.json',
            cookie_name='fridge_roulette_cookie',
            cookie_key=st.secrets["google_auth"]["cookie_key"],
            client_id=st.secrets["google_auth"]["client_id"],
            client_secret=st.secrets["google_auth"]["client_secret"],
            redirect_uri=st.secrets["google_auth"]["redirect_uri"],
        )
        authenticator.check_authenticity()
    except: pass # 靜默降級

# --- 側邊欄邏輯 ---
with st.sidebar:
    st.title("👤 會員中心")
    is_mem = False
    if authenticator:
        if not st.session_state.get('connected'):
            authenticator.login()
        else:
            is_mem = True
            st.success(f"大廚的貴賓：\n{st.session_state.get('user_info', {}).get('email')}")
            authenticator.logout()
    else:
        st.info("💡 目前以訪客身分體驗。")

    st.markdown("---")
    st.title("⚙️ 工程設定")
    
    def sync_api_key(): st.session_state.api_key = st.session_state.temp_api_key

    st.text_input("API Key", type="password", value=st.session_state.api_key, key="temp_api_key", on_change=sync_api_key)
    
    cur_def = st.secrets.get("default_model", "gemini-1.5-flash")
    try: d_idx = st.session_state.available_models.index(cur_def)
    except: d_idx = 0
    selected_model = st.selectbox("選擇 AI 大腦", options=st.session_state.available_models, index=d_idx)

# --- 核心 AI 邏輯 ---
def clean_ai_response(raw):
    """強效清理 AI 回傳內容，移除思考過程與標籤"""
    res = re.sub(r'<thought>.*?</thought>', '', raw, flags=re.DOTALL | re.IGNORECASE)
    res = re.sub(r'```[a-zA-Z]*\n?|```', '', res)
    return res.strip()

def identify_ingredients(image_bytes):
    """第一階段：大廚視覺辨識"""
    prompt = "你是一位星級創意大廚。請掃描照片並直接列出看到的食材，以逗號分隔。嚴禁廢話與思考過程。"
    try:
        client = OpenAI(api_key=st.session_state.api_key, base_url=DEFAULT_BASE_URL)
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        resp = client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}]}],
        )
        return clean_ai_response(resp.choices[0].message.content).replace('\n', ', ')
    except Exception as e:
        return f"大廚暫時看不清：{str(e)}"

def get_recipes(ingredients, is_premium):
    """第二階段：大廚食譜生成"""
    extra = "身為您的專屬大廚，請為身為會員的使用者額外提供「詳細的營養價值分析」與「養生建議」。" if is_premium else ""
    instruction = f"""你是一位星級大廚。根據食材設計三道料理。回應須詳細、有層次。{extra}
    必須回傳 JSON 格式且鍵值不可更改：
    {{
      "chef_thinking": "看到食材的靈感發想",
      "recipes": [
        {{
          "dish_name": "菜名",
          "style": "風格",
          "ingredients_needed": ["食材列表"],
          "steps": ["步驟1", "步驟2"],
          "chef_secret": "美味秘訣",
          "nutrition": "營養分析 (非會員留空)"
        }}
      ]
    }}"""
    try:
        client = OpenAI(api_key=st.session_state.api_key, base_url=DEFAULT_BASE_URL)
        resp = client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "system", "content": instruction}, {"role": "user", "content": f"食材：{ingredients}"}],
            response_format={"type": "json_object"}
        )
        raw = clean_ai_response(resp.choices[0].message.content)
        match = re.search(r'(\{.*\})', raw, re.DOTALL)
        return json.loads(match.group(1)) if match else None
    except: return None

# --- UI 介面 ---
st.title("🍳 冰箱大轉盤")
st.caption("AI 驅動的星級剩食料理助手")

with st.expander("📸 第一步：拍照辨識食材", expanded=False):
    photo = st.camera_input("拍照")
    if photo:
        if st.button("🔍 讓大廚清點食材", use_container_width=True):
            with st.spinner("👨‍🍳 大廚清點中..."):
                st.session_state["ingredients_input"] = identify_ingredients(photo.getvalue())
                st.rerun()

st.markdown("---")

# 常用食材快速標籤 (2x4 佈局)
st.write("**快速加入常用食材：**")
tags = ["雞蛋", "豆腐", "蔥花", "高麗菜", "豬肉片", "泡麵", "洋蔥", "鮪魚罐頭"]
t_cols = st.columns(2)
def add_tag(t): 
    cur = st.session_state.get("ingredients_input", "")
    if cur in TEST_SAMPLES or not cur.strip(): st.session_state["ingredients_input"] = t
    else: st.session_state["ingredients_input"] = f"{cur}, {t}"

for i, t in enumerate(tags):
    t_cols[i % 2].button(f"+ {t}", key=f"t_{t}", on_click=add_tag, args=(t,), use_container_width=True)

st.markdown(" ")

# 文字確認區
ingredients = st.text_area("👇 第二步：確認食材清單 (可微調)：", height=120, key="ingredients_input")
c1, c2 = st.columns(2)
def set_rnd(): st.session_state["ingredients_input"] = random.choice(TEST_SAMPLES)
def clr(): st.session_state["ingredients_input"] = ""
c1.button("🎲 隨機食材", on_click=set_rnd, use_container_width=True)
c2.button("🧹 清空清單", on_click=clr, use_container_width=True)

# 料理生成區
if st.button("🔥 第三步：開始料理轉盤！", type="primary", use_container_width=True):
    if not st.session_state.api_key:
        st.warning("🔑 請先至左側邊欄設定 API Key！")
    elif ingredients.strip():
        with st.spinner("👨‍🍳 大廚正在廚房忙碌中..."):
            result = get_recipes(ingredients, is_mem)
            if result:
                st.balloons()
                with st.expander("🧠 大廚的內心獨白", expanded=True):
                    st.markdown(result.get("chef_thinking", ""))
                
                cols = st.columns(3)
                for i, r in enumerate(result.get("recipes", [])[:3]):
                    with cols[i]:
                        st.markdown(f"### 🍽️ {r.get('dish_name')}")
                        st.caption(f"風格：{r.get('style')}")
                        st.write("**🛒 食材**\n" + ", ".join(r.get('ingredients_needed', [])))
                        st.write("**📝 步驟**")
                        for idx, s in enumerate(r.get('steps', [])): st.write(f"{idx+1}. {s}")
                        if is_mem and r.get('nutrition'): st.info(f"🥗 **營養分析**\n\n{r['nutrition']}")
                        st.warning(f"💡 **秘訣**\n\n{r.get('chef_secret')}")
    else: st.warning("☝️ 請先提供食材！")

st.markdown("---")
st.caption("2026 Fridge Roulette v10.2 - Strict & Robust Edition")
