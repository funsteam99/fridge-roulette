import streamlit as st
from openai import OpenAI
import json
import os
import re
import random

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
    page_title="冰箱大轉盤 - 星級大廚剩食料理", 
    page_icon="🍳", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 初始化 Session State
if "api_key" not in st.session_state:
    st.session_state.api_key = saved_config.get("api_key", "")
if "available_models" not in st.session_state:
    st.session_state.available_models = saved_config.get("available_models", ["gemini-1.5-flash", "gemini-1.5-pro", "gemma-2-9b-it"])
# 隨機挑選測試食材
if "random_ingredients" not in st.session_state:
    st.session_state.random_ingredients = random.choice(TEST_SAMPLES)

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

    selected_model = st.selectbox(
        "選擇 AI 大腦", options=st.session_state.available_models + ["自定義模型..."],
        index=st.session_state.available_models.index(saved_config.get("model")) if saved_config.get("model") in st.session_state.available_models else 0,
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

def get_recipes(api_key, base_url, model_name, ingredients):
    if not api_key:
        st.error("🔑 請先輸入 API Key！")
        return None
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": SYSTEM_INSTRUCTION}, {"role": "user", "content": f"食材：{ingredients}"}],
            response_format={"type": "json_object"}
        )
        return parse_chef_response(response.choices[0].message.content)
    except Exception as e:
        st.error(f"❌ 連線失敗：{str(e)}")
        return None

# --- UI 介面 ---
st.title("🍳 冰箱大轉盤 (Fridge Roulette)")
st.subheader("大廚已備好測試食材，直接點擊「開始料理」試試看吧！")

ingredients = st.text_area(
    "👇 輸入剩食食材：", 
    value=st.session_state.random_ingredients,
    height=150, 
    key="ingredients_input"
)

col_actions1, col_actions2 = st.columns([1, 4])
with col_actions1:
    if st.button("🎲 換一組試試"):
        st.session_state.random_ingredients = random.choice(TEST_SAMPLES)
        st.rerun()

if st.button("🔥 開始料理轉盤！", use_container_width=True):
    if ingredients.strip():
        with st.spinner(f"👨‍🍳 大廚正在廚房忙碌中..."):
            result = get_recipes(st.session_state.api_key, base_url, model_name, ingredients)
            if result:
                st.balloons()
                with st.expander("🧠 大廚的內心獨白 (思考過程)", expanded=False):
                    st.markdown(result["chef_thinking"])
                
                st.markdown("---")
                cols = st.columns(3)
                for i, recipe in enumerate(result["recipes"][:3]):
                    with cols[i]:
                        # 加入容錯讀取機制 (Fallback)，防範模型不聽話
                        dish_name = recipe.get('dish_name', recipe.get('菜名', '驚喜料理'))
                        style = recipe.get('style', recipe.get('風格', recipe.get('料理風格', '創意')))
                        
                        ing_list = recipe.get('ingredients_needed', recipe.get('食材', recipe.get('所需食材', [])))
                        if isinstance(ing_list, str): ing_list = [ing_list] # 防呆
                        
                        steps_list = recipe.get('steps', recipe.get('步驟', recipe.get('烹飪步驟', [])))
                        if isinstance(steps_list, str): steps_list = [steps_list] # 防呆
                        
                        secret = recipe.get('chef_secret', recipe.get('大廚秘訣', recipe.get('秘訣', '用心就是美味！')))

                        st.markdown(f"### 🍽️ {dish_name}")
                        st.caption(f"風格：{style}")
                        
                        st.write("**🛒 食材**")
                        st.write(", ".join(ing_list) if ing_list else "食材解析遺失，請查看獨白或直接發揮創意。")
                        
                        st.write("**📝 步驟**")
                        for idx, s in enumerate(steps_list): st.write(f"{idx+1}. {s}")
                        
                        st.warning(f"💡 **大廚秘訣**\n\n{secret}")
    else: st.warning("☝️ 請輸入食材！")

st.markdown("---")
st.caption("2026 Fridge Roulette Engine v6.3 - Strict Keys & Fallback parser")
