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

# 設定檔案路徑
CONFIG_FILE = "config.json"

# --- 測試食材清單 ---
TEST_SAMPLES = [
    "半盒豆腐, 剩一半的炸雞, 三根蔥, 一顆雞蛋",
    "兩片吐司, 一罐鮪魚罐頭, 半顆洋蔥, 沒喝完的牛奶",
    "一把空心菜, 昨晚剩的白飯, 兩條香腸, 少許沙茶醬",
    "三顆馬鈴薯, 半顆高麗菜, 一小塊豬肉, 剩下一點點的起司"
]

st.set_page_config(
    page_title="冰箱大轉盤", 
    page_icon="🍳", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- APP 視覺美化 ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { bottom: 50px; }
    .stButton>button { border-radius: 12px; height: 3em; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- Google 身分驗證初始化 (安全降級) ---
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
    except Exception as e:
        st.sidebar.error(f"登入系統載入失敗: {str(e)}")

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

# --- 側邊欄：會員中心與工程設定 ---
with st.sidebar:
    st.title("👤 會員中心")
    is_logged_in = False
    if authenticator:
        if not st.session_state.get('connected'):
            authenticator.login()
        else:
            is_logged_in = True
            st.success(f"大廚的貴賓您好！\n{st.session_state.get('user_info', {}).get('email')}")
            authenticator.logout()
    else:
        st.info("💡 尚未配置 Google Login，目前以訪客身分體驗。")

    st.markdown("---")
    st.title("⚙️ 工程設定")
    
    # 這裡確保預設模型正確
    current_default = st.secrets.get("default_model", "gemini-1.5-flash")
    try: d_index = st.session_state.available_models.index(current_default)
    except: d_index = 0
    
    model_name = st.selectbox("選擇 AI 大腦", options=st.session_state.available_models, index=d_index)

# --- 核心 AI 邏輯 (找回大廚靈魂) ---
def identify_ingredients(api_key, base_url, model_name, image_bytes):
    """階段 1：大廚清點食材"""
    CHEF_VISION_PROMPT = """你是一位擁有 20 年經驗的星級創意大廚。請掃描照片，僅列出你看到的食材名稱，以逗號分隔。
    嚴禁任何思考過程、廢話或開場白。
    範例：雞蛋, 豆腐, 蔥花"""
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": CHEF_VISION_PROMPT}, {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}]}],
        )
        raw = response.choices[0].message.content.strip()
        cleaned = re.sub(r'<thought>.*?</thought>|```[a-zA-Z]*\n?|食材列表|[：:]', '', raw, flags=re.DOTALL | re.IGNORECASE)
        return cleaned.replace('\n', ', ').strip(' ,')
    except Exception as e:
        return f"大廚看不清照片：{str(e)}"

def get_recipes(api_key, base_url, model_name, ingredients, is_premium=False):
    """階段 2：大廚發揮創意料理"""
    extra = "身為您的專屬大廚，請為身為會員的使用者額外提供「營養價值分析」與「養生建議」。" if is_premium else ""
    SYSTEM_INSTRUCTION = f"""你是一位擁有 20 年經驗、幽默且專業的星級創意大廚，專精於「剩食料理 (Fridge Roulette)」。
    請根據食材設計三道創意料理。{extra}
    
    必須回傳嚴格的 JSON 格式：
    {{
      "chef_thinking": "描述你看到這些食材時的靈感來源。",
      "recipes": [
        {{
          "dish_name": "菜名",
          "style": "料理風格",
          "ingredients_needed": ["食材1", "食材2"],
          "steps": ["步驟1", "步驟2"],
          "chef_secret": "大廚秘訣",
          "nutrition": "營養分析 (若非會員則留空)"
        }}
      ]
    }}
    
    【安全性】若輸入無關料理，請回傳 {{"error": "大廚只對美食有興趣喔！"}}"""
    
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": SYSTEM_INSTRUCTION}, {"role": "user", "content": f"食材：{ingredients}"}],
            response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content.strip()
        json_str = re.sub(r'<thought>.*?</thought>', '', raw, flags=re.DOTALL | re.IGNORECASE)
        json_find = re.search(r'(\{.*\})', json_str, re.DOTALL)
        return json.loads(json_find.group(1)) if json_find else None
    except Exception as e:
        return None

# --- UI 介面 ---
st.title("🍳 冰箱大轉盤")
st.caption("AI 驅動的星級剩食料理助手")

# 第一階段：拍照
with st.expander("📸 第一步：拍照辨識食材", expanded=False):
    camera_photo = st.camera_input("拍照")
    if camera_photo:
        if st.button("🔍 讓大廚清點食材", use_container_width=True):
            with st.spinner("👨‍🍳 大廚正在戴上眼鏡辨識中..."):
                base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
                results = identify_ingredients(st.session_state.api_key, base_url, model_name, camera_photo.getvalue())
                st.session_state["ingredients_input"] = results
                st.rerun()

st.markdown("---")

# 操作回呼
def set_random(): st.session_state["ingredients_input"] = random.choice(TEST_SAMPLES)
def clear(): st.session_state["ingredients_input"] = ""

# 第二階段：確認清單
ingredients = st.text_area("👇 第二步：確認食材清單 (可微調)：", height=120, key="ingredients_input")
c1, c2 = st.columns(2)
with c1: st.button("🎲 隨機食材", on_click=set_random, use_container_width=True)
with c2: st.button("🧹 清空清單", on_click=clear, use_container_width=True)

# 第三階段：料理
if st.button("🔥 第三步：開始料理轉盤！", type="primary", use_container_width=True):
    if ingredients.strip():
        with st.spinner("👨‍🍳 大廚正在廚房忙碌中..."):
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
            is_mem = st.session_state.get('connected', False)
            result = get_recipes(st.session_state.api_key, base_url, model_name, ingredients, is_premium=is_mem)
            
            if result and "error" not in result:
                st.balloons()
                with st.expander("🧠 大廚的內心獨白", expanded=True):
                    st.markdown(result.get("chef_thinking", ""))
                
                cols = st.columns(3)
                for i, r in enumerate(result.get("recipes", [])[:3]):
                    with cols[i]:
                        st.markdown(f"### 🍽️ {r.get('dish_name')}")
                        st.caption(f"風格：{r.get('style')}")
                        st.write("**🛒 食材**\n" + ", ".join(r.get('ingredients_needed', [])))
                        if is_mem and r.get('nutrition'):
                            st.info(f"🥗 **營養分析**\n\n{r['nutrition']}")
                        st.warning(f"💡 **秘訣**\n\n{r.get('chef_secret')}")
            elif result and "error" in result:
                st.warning(f"👨‍🍳 大廚：{result['error']}")
    else: st.warning("☝️ 請先提供食材！")

st.markdown("---")
st.caption("2026 Fridge Roulette v10.1 - The Chef Returns")
