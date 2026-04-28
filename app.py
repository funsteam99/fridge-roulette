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

# --- APP 視覺美化 (隱藏 Streamlit 選單) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        bottom: 50px;
    }
    .stButton>button {
        border-radius: 12px;
        height: 3em;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 初始化 Session State ---
if "api_key" not in st.session_state:
    if "api_key" in st.secrets:
        st.session_state.api_key = st.secrets["api_key"]
    else:
        st.session_state.api_key = saved_config.get("api_key", "")

if "available_models" not in st.session_state:
    st.session_state.available_models = saved_config.get("available_models", ["gemma-4-31b-it", "gemini-1.5-flash", "gemini-1.5-pro"])

if "default_model" not in st.session_state:
    if "default_model" in st.secrets:
        st.session_state.default_model = st.secrets["default_model"]
    else:
        st.session_state.default_model = saved_config.get("model", "gemma-4-31b-it")

if "ingredients_input" not in st.session_state:
    st.session_state["ingredients_input"] = random.choice(TEST_SAMPLES)

# --- 側邊欄設定 ---
with st.sidebar:
    st.title("⚙️ 大廚工作室設定")
    st.subheader("API 配置")
    default_domain = "generativelanguage.googleapis.com"
    default_base_url = f"https://{default_domain}/v1beta/openai"
    st.text_input("API 帳號", value=default_domain, key="api_username", disabled=True)
    
    def sync_and_save():
        st.session_state.api_key = st.session_state.api_key_input
        config = load_config()
        config.update({
            "api_key": st.session_state.api_key,
            "base_url": st.session_state.get("base_url_input", default_base_url),
            "model": st.session_state.get("model_selectbox", ""),
            "available_models": st.session_state.available_models
        })
        save_config(config)
        if st.session_state.api_key: fetch_latest_models()

    api_key = st.text_input("API Key", type="password", value=st.session_state.api_key, key="api_key_input", on_change=sync_and_save)
    use_custom_url = st.checkbox("自定義 Base URL", value=saved_config.get("use_custom_url", False), key="use_custom_url")
    base_url = st.text_input("Base URL", value=saved_config.get("base_url", default_base_url), key="base_url_input", on_change=sync_and_save) if use_custom_url else default_base_url

    def fetch_latest_models():
        if not st.session_state.api_key: return
        try:
            client = OpenAI(api_key=st.session_state.api_key, base_url=base_url)
            models = client.models.list()
            model_ids = [m.id for m in models.data]
            keywords = ["gemini", "gemma", "learnlm"]
            filtered = [m for m in model_ids if any(kw in m.lower() for kw in keywords) and "embed" not in m.lower()]
            if filtered:
                st.session_state.available_models = sorted(list(set(filtered)))
                config = load_config()
                config["available_models"] = st.session_state.available_models
                save_config(config)
                st.toast("✅ 模型清單已更新！", icon="👨‍🍳")
        except Exception as e:
            st.sidebar.error(f"掃描失敗: {str(e)}")

    try:
        current_model = st.session_state.default_model
        default_index = st.session_state.available_models.index(current_model)
    except:
        default_index = 0

    selected_model = st.selectbox(
        "選擇 AI 大腦", options=st.session_state.available_models + ["自定義模型..."],
        index=default_index,
        key="model_selectbox", on_change=sync_and_save
    )
    model_name = st.text_input("自定義模型", value=saved_config.get("custom_model", ""), key="custom_model_input", on_change=sync_and_save) if selected_model == "自定義模型..." else selected_model

# --- 核心邏輯 ---
SYSTEM_INSTRUCTION = """
你是一位擁有 20 年經驗的星級創意大廚，專精於「剩食料理 (Fridge Roulette)」。
你的任務是根據使用者提供的食材，設計出三道富有創意的料理。

【極度重要警告】
你必須回傳一個嚴格的 JSON 格式物件。
嚴禁翻譯或更改 JSON 的「鍵值 (Key)」，必須完全使用以下定義的英文 Key。

JSON 結構必須精準長這樣：
{
  "chef_thinking": "描述你如何思考搭配與靈感來源。",
  "recipes": [
    {
      "dish_name": "響亮或有趣的菜名",
      "style": "料理風格",
      "ingredients_needed": ["食材1", "食材2"],
      "steps": ["步驟1", "步驟2"],
      "chef_secret": "大廚秘訣"
    }
  ]
}
"""

def parse_chef_response(raw_content):
    thinking = ""
    json_str = ""
    thought_match = re.search(r'<thought>(.*?)</thought>', raw_content, re.DOTALL)
    if thought_match:
        thinking = thought_match.group(1).strip()
        json_str = re.sub(r'<thought>.*?</thought>', '', raw_content, flags=re.DOTALL).strip()
    else:
        json_str = raw_content.strip()
    json_str = re.sub(r'^```json\s*', '', json_str, flags=re.MULTILINE)
    json_str = re.sub(r'\s*```$', '', json_str, flags=re.MULTILINE)
    if not json_str.startswith('{'):
        json_find = re.search(r'(\{.*\})', json_str, re.DOTALL)
        if json_find: json_str = json_find.group(1)
    try:
        data = json.loads(json_str)
        if not thinking: thinking = data.get("chef_thinking", "大廚正在為您準備佳餚...")
        return {"chef_thinking": thinking, "recipes": data.get("recipes", [data])}
    except:
        st.error("❌ 解析失敗。")
        st.code(raw_content)
        return None

def get_recipes(api_key, base_url, model_name, ingredients, image_bytes=None):
    if not api_key:
        st.error("🔑 請先輸入 API Key！")
        return None
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        user_content = [{"type": "text", "text": f"食材文字描述：{ingredients}"}]
        
        if image_bytes:
            encoded_image = base64.b64encode(image_bytes).decode("utf-8")
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
            })
            user_content[0]["text"] += "\n請同時辨識這張圖片中的食材，並結合文字描述進行設計。"

        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": SYSTEM_INSTRUCTION}, {"role": "user", "content": user_content}],
            response_format={"type": "json_object"}
        )
        return parse_chef_response(response.choices[0].message.content)
    except Exception as e:
        st.error(f"❌ 連線失敗：{str(e)}")
        return None

# --- 介面操作回呼函數 ---
def add_tag(tag):
    current = st.session_state.get("ingredients_input", "")
    if current in TEST_SAMPLES or not current.strip():
        st.session_state["ingredients_input"] = tag
    else:
        st.session_state["ingredients_input"] = f"{current}, {tag}"

def set_random_ingredients():
    st.session_state["ingredients_input"] = random.choice(TEST_SAMPLES)

def clear_ingredients():
    st.session_state["ingredients_input"] = ""

# --- UI 介面 ---
st.title("🍳 冰箱大轉盤")
st.caption("AI 驅動的星級剩食料理助手")

camera_photo = None
with st.expander("📸 拍照辨識食材", expanded=False):
    camera_photo = st.camera_input("拍一張冰箱照片")
    if camera_photo:
        st.success("✅ 照片已備好，點擊下方「開始料理」進行辨識。")

st.markdown("---")

st.write("**快速加入常用食材：**")
common_tags = ["雞蛋", "豆腐", "蔥花", "高麗菜", "豬肉片", "泡麵", "洋蔥", "鮪魚罐頭"]
tag_cols = st.columns(2)
for i, tag in enumerate(common_tags):
    tag_cols[i % 2].button(f"+ {tag}", key=f"tag_{tag}", on_click=add_tag, args=(tag,), use_container_width=True)

st.markdown(" ")

ingredients = st.text_area("👇 您的食材清單：", height=120, key="ingredients_input")

col_actions1, col_actions2 = st.columns(2)
with col_actions1:
    st.button("🎲 隨機清單", on_click=set_random_ingredients, use_container_width=True)
with col_actions2:
    st.button("🧹 清空", on_click=clear_ingredients, use_container_width=True)

if st.button("🔥 開始料理轉盤！", type="primary", use_container_width=True):
    if ingredients.strip() or camera_photo:
        with st.spinner(f"👨‍🍳 大廚正在看照片發想靈感..."):
            photo_bytes = camera_photo.getvalue() if camera_photo else None
            result = get_recipes(st.session_state.api_key, base_url, model_name, ingredients, photo_bytes)
            if result:
                st.balloons()
                with st.expander("🧠 大廚的內心獨白", expanded=False):
                    st.markdown(result["chef_thinking"])
                
                st.markdown("---")
                cols = st.columns(3)
                for i, recipe in enumerate(result["recipes"][:3]):
                    with cols[i]:
                        dish_name = recipe.get('dish_name', '驚喜料理')
                        style = recipe.get('style', '創意')
                        ing_list = recipe.get('ingredients_needed', [])
                        if isinstance(ing_list, str): ing_list = [ing_list]
                        steps_list = recipe.get('steps', [])
                        if isinstance(steps_list, str): steps_list = [steps_list]
                        secret = recipe.get('chef_secret', '用心就是美味！')

                        st.markdown(f"### 🍽️ {dish_name}")
                        st.caption(f"風格：{style}")
                        st.write("**🛒 食材**")
                        st.write(", ".join(ing_list) if ing_list else "食材解析遺失。")
                        st.write("**📝 步驟**")
                        for idx, s in enumerate(steps_list): st.write(f"{idx+1}. {s}")
                        st.warning(f"💡 **秘訣**\n\n{secret}")
    else: st.warning("☝️ 請輸入食材或拍張照！")

st.markdown("---")
st.caption("2026 Fridge Roulette Engine v7.0 - Gemma 4 Multimodal Ready")
