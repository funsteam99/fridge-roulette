import streamlit as st
from openai import OpenAI
import json
import os
import re
import random
import base64
from streamlit_google_auth import Authenticate

# 設定檔案路徑
CONFIG_FILE = "config.json"

# --- 測試食材清單 ---
TEST_SAMPLES = [
    "半盒豆腐, 剩一半的炸雞, 三根蔥, 一顆雞蛋",
    "兩片吐司, 一罐鮪魚罐頭, 半顆洋蔥, 沒喝完的牛奶",
    "一把空心菜, 昨晚剩的白飯, 兩條香腸, 少許沙茶醬",
    "三顆馬鈴薯, 半顆高麗菜, 一小塊豬肉, 剩下一點點的起司"
]

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

saved_config = load_config()

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

# --- Google 身分驗證設定 ---
# 這些資訊會從 st.secrets 讀取
if "google_auth" in st.secrets:
    authenticator = Authenticate(
        secret_credentials_path='google_credentials.json', # 這個檔案會由程式動態生成或從 Secrets 讀取
        cookie_name='fridge_roulette_cookie',
        cookie_key=st.secrets["google_auth"]["cookie_key"],
        client_id=st.secrets["google_auth"]["client_id"],
        client_secret=st.secrets["google_auth"]["client_secret"],
        redirect_uri=st.secrets["google_auth"]["redirect_uri"],
    )
    # 執行檢查
    authenticator.check_authenticity()
else:
    authenticator = None

# --- 初始化 Session State ---
if "api_key" not in st.session_state:
    st.session_state.api_key = st.secrets.get("api_key") or saved_config.get("api_key", "")

if "available_models" not in st.session_state:
    base_models = ["gemini-1.5-flash", "gemini-1.5-pro"]
    if "default_model" in st.secrets:
        s_model = st.secrets["default_model"]
        if s_model not in base_models: base_models.insert(0, s_model)
    st.session_state.available_models = saved_config.get("available_models", base_models)

if "default_model" not in st.session_state:
    st.session_state.default_model = st.secrets.get("default_model") or saved_config.get("model", "gemini-1.5-flash")

if "ingredients_input" not in st.session_state:
    st.session_state["ingredients_input"] = random.choice(TEST_SAMPLES)

# --- 側邊欄：Google 登入 ---
with st.sidebar:
    st.title("👤 會員中心")
    if authenticator:
        if not st.session_state.get('connected'):
            authenticator.login()
        else:
            st.success(f"歡迎回來！\n{st.session_state.get('user_info', {}).get('email')}")
            authenticator.logout()
    else:
        st.warning("⚠️ 尚未配置 Google Login 憑證。")
        st.info("請在 Secrets 中填入 google_auth 資訊以啟用。")

    st.markdown("---")
    st.title("⚙️ 工程設定")
    try:
        current_default = st.session_state.get("default_model", "")
        d_index = st.session_state.available_models.index(current_default)
    except:
        d_index = 0
    model_name = st.selectbox("選擇 AI 大腦", options=st.session_state.available_models, index=d_index)

# --- 核心 AI 邏輯 ---
def identify_ingredients(api_key, base_url, model_name, image_bytes):
    CHEF_VISION_SYSTEM_PROMPT = "你是一位星級創意大廚。請運用專業直覺掃描照片，僅列出看到的食材名稱，以逗號分隔。嚴禁包含思考過程。"
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": CHEF_VISION_SYSTEM_PROMPT},
                {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}]}
            ]
        )
        raw_result = response.choices[0].message.content.strip()
        cleaned = re.sub(r'<thought>.*?</thought>', '', raw_result, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'```[a-zA-Z]*\n?|食材列表|以下是辨識結果|[：:]', '', cleaned)
        return cleaned.replace('\n', ', ').strip(' ,')
    except Exception as e:
        return f"辨識失敗: {str(e)}"

def get_recipes(api_key, base_url, model_name, ingredients, is_premium=False):
    extra_prompt = "請額外為每道菜加入「健康營養分析」與「專業養生建議」。" if is_premium else ""
    SYSTEM_INSTRUCTION = f"你是一位星級創意大廚。根據食材設計三道料理。{extra_prompt} 必須回傳 JSON。"
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": SYSTEM_INSTRUCTION}, {"role": "user", "content": f"食材：{ingredients}"}],
            response_format={"type": "json_object"}
        )
        raw_content = response.choices[0].message.content.strip()
        json_str = re.sub(r'<thought>.*?</thought>', '', raw_content, flags=re.DOTALL | re.IGNORECASE)
        json_find = re.search(r'(\{.*\})', json_str, re.DOTALL)
        if json_find: json_str = json_find.group(1)
        return json.loads(json_str)
    except Exception as e:
        return None

# --- UI 介面 ---
st.title("🍳 冰箱大轉盤")
st.caption("AI 驅動的星級剩食料理助手")

with st.expander("📸 第一步：拍照辨識食材", expanded=False):
    camera_photo = st.camera_input("拍照")
    if camera_photo:
        if st.button("🔍 辨識照片食材", use_container_width=True):
            with st.spinner("辨識中..."):
                base_url = f"https://generativelanguage.googleapis.com/v1beta/openai"
                results = identify_ingredients(st.session_state.api_key, base_url, model_name, camera_photo.getvalue())
                st.session_state["ingredients_input"] = results
                st.rerun()

st.markdown("---")
ingredients = st.text_area("👇 第二步：確認食材清單 (可手動修改)：", height=120, key="ingredients_input")

if st.button("🔥 第三步：開始料理轉盤！", type="primary", use_container_width=True):
    if ingredients.strip():
        with st.spinner("正在為您烹飪..."):
            base_url = f"https://generativelanguage.googleapis.com/v1beta/openai"
            is_mem = st.session_state.get('connected', False)
            result = get_recipes(st.session_state.api_key, base_url, model_name, ingredients, is_premium=is_mem)
            if result:
                st.balloons()
                cols = st.columns(3)
                recipes = result.get("recipes", [])[:3]
                for i, recipe in enumerate(recipes):
                    with cols[i]:
                        st.markdown(f"### 🍽️ {recipe.get('dish_name', '驚喜料理')}")
                        st.write("**🛒 食材**\n" + ", ".join(recipe.get('ingredients_needed', [])))
                        if is_mem and "nutrition" in recipe:
                            st.info(f"🥗 **營養分析**\n\n{recipe['nutrition']}")
                        st.warning(f"💡 **秘訣**\n\n{recipe.get('chef_secret', '用心就是美味！')}")
    else: st.warning("☝️ 請先提供食材！")

st.markdown("---")
st.caption("2026 Fridge Roulette v10.0 - Google OAuth Integrated")
