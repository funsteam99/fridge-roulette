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
    "兩片吐司, 一罐鮪魚罐頭, 半顆洋蔥, 沒喝完的牛奶",
    "一把空心菜, 昨晚剩的白飯, 兩條香腸, 少許沙茶醬",
    "三顆馬鈴薯, 半顆高麗菜, 一小塊豬肉, 剩下一點點的起司",
    "兩球乾泡麵, 一碗昨晚的剩湯, 幾片火腿, 枯萎的香菜",
    "一盒快過期的優格, 半粒蘋果, 堅果碎, 一點蜂蜜"
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

# --- 側邊欄設定 ---
with st.sidebar:
    st.title("⚙️ 設定")
    api_key = st.text_input("API Key", type="password", value=st.session_state.api_key)
    
    # 動態計算預設 index
    try:
        current_default = st.session_state.get("default_model", "")
        d_index = st.session_state.available_models.index(current_default)
    except (ValueError, KeyError):
        d_index = 0
        
    model_name = st.selectbox(
        "選擇 AI 大腦", 
        options=st.session_state.available_models, 
        index=d_index
    )

# --- 核心 AI 邏輯 ---
def identify_ingredients(api_key, base_url, model_name, image_bytes):
    """階段 1：辨識照片中的食材 (以大廚的人格設定進行辨識)"""
    CHEF_VISION_SYSTEM_PROMPT = """你是一位星級創意大廚。請運用專業直覺掃描照片，僅列出看到的食材名稱。
    
    【規則】
    1. 僅回傳食材名稱，並以逗號分隔。
    2. 嚴禁包含任何思考過程、描述、形容詞或結論（例如不要寫「我看見了...」、「這看起來...」）。
    3. 如果沒看到食材，請回傳「未偵測到食材」。
    
    範例輸出：雞蛋, 豆腐, 蔥, 牛奶"""
    
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": CHEF_VISION_SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                ]}
            ]
        )
        raw_result = response.choices[0].message.content.strip()
        
        # 強制過濾常見的 AI 廢話開場 (防護機制)
        cleaned = re.sub(r'^(我看見了|這張照片中有|食材清單有|食材有|以下是辨識結果|辨識結果|食材)：', '', raw_result)
        cleaned = cleaned.replace('\n', ', ').strip() # 防止 AI 用換行而不是逗號
        return cleaned
    except Exception as e:
        if "429" in str(e):
            return "⚠️ API 額度已達上限。大廚建議您在側邊欄切換至 'gemini-1.5-flash'，那是目前最穩定的助手。"
        return f"大廚辨識失敗: {str(e)}"

def get_recipes(api_key, base_url, model_name, ingredients):
    """階段 2：根據文字產出食譜"""
    SYSTEM_INSTRUCTION = """你是一位星級創意大廚。請根據食材設計三道料理。
    必須回傳 JSON：{"chef_thinking": "...", "recipes": [{"dish_name": "...", "style": "...", "ingredients_needed": [], "steps": [], "chef_secret": "..."}]}"""
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": f"食材：{ingredients}"}
            ],
            response_format={"type": "json_object"}
        )
        # 簡單解析邏輯 (沿用之前的 parse_chef_response 精髓)
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        st.error(f"❌ 料理失敗：{str(e)}")
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
            result = get_recipes(st.session_state.api_key, base_url, model_name, ingredients)
            if result:
                st.balloons()
                with st.expander("🧠 大廚的內心獨白", expanded=True):
                    st.markdown(result.get("chef_thinking", "準備中..."))
                
                cols = st.columns(3)
                recipes = result.get("recipes", [])[:3]
                for i, recipe in enumerate(recipes):
                    with cols[i]:
                        st.markdown(f"### 🍽️ {recipe.get('dish_name', '驚喜料理')}")
                        st.caption(f"風格：{recipe.get('style', '創意')}")
                        st.write("**🛒 食材**")
                        st.write(", ".join(recipe.get('ingredients_needed', [])))
                        st.write("**📝 步驟**")
                        for idx, s in enumerate(recipe.get('steps', [])): st.write(f"{idx+1}. {s}")
                        st.warning(f"💡 **秘訣**\n\n{recipe.get('chef_secret', '用心就是美味！')}")
    else: st.warning("☝️ 請先提供食材！")

st.markdown("---")
st.caption("2026 Fridge Roulette Engine v8.0 - Two-Stage Vision Process")
