import streamlit as st
from openai import OpenAI
import json
import os
import re
import random
import base64

# 設定檔案路徑
CONFIG_FILE = "config.json"

# --- 測試食材清單 ---
TEST_SAMPLES = [
    "半盒豆腐, 剩一半的炸雞, 三根蔥, 一顆雞蛋",
    "兩片吐司, 一罐鮪魚罐頭, 半顆洋蔥,沒喝完的牛奶",
    "一把空心菜, 昨晚剩的白飯, 兩條香腸, 少許沙茶醬",
    "三顆馬鈴薯, 半顆高麗菜, 一小塊豬肉, 剩下一點點的起司"
]

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

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
    .member-box { padding: 15px; border-radius: 10px; background-color: #f0f2f6; border: 1px solid #d1d5db; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

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

# 會員狀態初始化
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""

# --- 側邊欄：會員與設定 ---
with st.sidebar:
    st.title("👤 會員中心")
    if not st.session_state["is_logged_in"]:
        with st.form("login_form"):
            email = st.text_input("電子信箱", placeholder="example@gmail.com")
            submitted = st.form_submit_button("登入 / 註冊", use_container_width=True)
            if submitted and email:
                st.session_state["is_logged_in"] = True
                st.session_state["user_email"] = email
                st.rerun()
        st.info("💡 登入後可解鎖「食譜收藏」與「營養分析」功能。")
    else:
        st.success(f"歡迎回來！\n{st.session_state['user_email']}")
        if st.button("登出", use_container_width=True):
            st.session_state["is_logged_in"] = False
            st.session_state["user_email"] = ""
            st.rerun()

    st.markdown("---")
    st.title("⚙️ 工程設定")
    api_key = st.text_input("API Key", type="password", value=st.session_state.api_key)
    
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
    extra_prompt = ""
    if is_premium:
        extra_prompt = "請額外為每道菜加入「健康營養分析（熱量、蛋白質等）」與「專業養生建議」。"

    SYSTEM_INSTRUCTION = f"""你是一位星級創意大廚。根據食材設計三道料理。{extra_prompt}
    必須回傳 JSON：{{"chef_thinking": "...", "recipes": [{{"dish_name": "...", "style": "...", "ingredients_needed": [], "steps": [], "chef_secret": "...", "nutrition": "..."}}]}}
    如果輸入無關或有害，請回傳 {{"error": "..."}}"""
    
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

# --- 介面操作回呼 ---
def add_tag(tag):
    current = st.session_state.get("ingredients_input", "")
    if current in TEST_SAMPLES or not current.strip(): st.session_state["ingredients_input"] = tag
    else: st.session_state["ingredients_input"] = f"{current}, {tag}"

def set_random_ingredients(): st.session_state["ingredients_input"] = random.choice(TEST_SAMPLES)
def clear_ingredients(): st.session_state["ingredients_input"] = ""

# --- UI 介面 ---
st.title("🍳 冰箱大轉盤")
st.caption("AI 驅動的星級剩食料理助手")

with st.expander("📸 第一步：拍照辨識食材", expanded=False):
    camera_photo = st.camera_input("拍照")
    if camera_photo:
        if st.button("🔍 辨識照片食材", use_container_width=True):
            with st.spinner("👨‍🍳 大廚正在看照片辨識中..."):
                base_url = f"https://generativelanguage.googleapis.com/v1beta/openai"
                results = identify_ingredients(st.session_state.api_key, base_url, model_name, camera_photo.getvalue())
                st.session_state["ingredients_input"] = results
                st.rerun()

st.markdown("---")
st.write("**快速加入常用食材：**")
common_tags = ["雞蛋", "豆腐", "蔥花", "高麗菜", "豬肉片", "泡麵", "洋蔥", "鮪魚罐頭"]
tag_cols = st.columns(2)
for i, tag in enumerate(common_tags):
    tag_cols[i % 2].button(f"+ {tag}", key=f"tag_{tag}", on_click=add_tag, args=(tag,), use_container_width=True)

st.markdown(" ")
ingredients = st.text_area("👇 第二步：確認食材清單 (可手動修改)：", height=120, key="ingredients_input")

col_actions1, col_actions2 = st.columns(2)
with col_actions1: st.button("🎲 隨機清單", on_click=set_random_ingredients, use_container_width=True)
with col_actions2: st.button("🧹 清空", on_click=clear_ingredients, use_container_width=True)

if st.button("🔥 第三步：開始料理轉盤！", type="primary", use_container_width=True):
    if ingredients.strip():
        with st.spinner("👨‍🍳 大廚正在廚房忙碌中..."):
            base_url = f"https://generativelanguage.googleapis.com/v1beta/openai"
            # 判斷是否為會員以提供加值功能
            is_mem = st.session_state["is_logged_in"]
            result = get_recipes(st.session_state.api_key, base_url, model_name, ingredients, is_premium=is_mem)
            
            if result and "error" not in result:
                st.balloons()
                with st.expander("🧠 大廚的內心獨白", expanded=True):
                    st.markdown(result.get("chef_thinking", ""))
                
                cols = st.columns(3)
                recipes = result.get("recipes", [])[:3]
                for i, recipe in enumerate(recipes):
                    with cols[i]:
                        st.markdown(f"### 🍽️ {recipe.get('dish_name', '驚喜料理')}")
                        st.caption(f"風格：{recipe.get('style', '創意')}")
                        st.write("**🛒 食材**\n" + ", ".join(recipe.get('ingredients_needed', [])))
                        st.write("**📝 步驟**\n" + "\n".join([f"{idx+1}. {s}" for idx, s in enumerate(recipe.get('steps', []))]))
                        
                        if is_mem and "nutrition" in recipe:
                            st.info(f"🥗 **會員專屬：營養分析**\n\n{recipe['nutrition']}")
                        
                        if st.button(f"💾 收藏食譜", key=f"save_{i}", use_container_width=True):
                            if is_mem: st.toast(f"✅ 已收藏：{recipe.get('dish_name')}", icon="📂")
                            else: st.warning("⚠️ 請先登入會員以收藏食譜！")
                        
                        st.warning(f"💡 **秘訣**\n\n{recipe.get('chef_secret', '用心就是美味！')}")
            elif result and "error" in result:
                st.error(f"👨‍🍳 大廚提醒：{result['error']}")
    else: st.warning("☝️ 請先提供食材！")

st.markdown("---")
st.caption("2026 Fridge Roulette v9.0 - Member Management Beta")
