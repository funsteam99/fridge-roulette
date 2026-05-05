import streamlit as st
from openai import OpenAI
import json
import re
import random
import base64
try:
    from streamlit_google_auth import Authenticate
except ImportError:
    Authenticate = None

# --- 常數設定 ---
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
MODEL_SECRET_KEYS = ("model", "default_model")
CULINARY_KEYWORDS = {
    "食材", "料理", "烹飪", "煮", "炒", "煎", "烤", "蒸", "燉", "炸", "拌", "湯", "飯", "麵",
    "菜", "肉", "魚", "蛋", "豆腐", "蔥", "洋蔥", "高麗菜", "馬鈴薯", "吐司", "牛奶", "起司",
    "雞", "豬", "牛", "海鮮", "鮪魚", "剩菜", "冰箱", "調味", "醬", "鹽", "糖", "油"
}
BLOCKED_KEYWORDS = {
    "政治", "選舉", "政黨", "暴力", "仇恨", "色情", "毒品", "炸彈", "武器", "駭客",
    "惡意程式", "木馬", "勒索", "釣魚", "sql injection", "xss"
}
JAILBREAK_PATTERNS = (
    r"忽略.*(規則|指令|系統)",
    r"ignore.*(previous|system|instruction)",
    r"jailbreak",
    r"developer mode",
    r"系統提示",
    r"prompt",
)

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

def read_secret(key, default=None):
    """Read Streamlit secrets without crashing when no secrets file exists."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def validate_runtime_config():
    try:
        api_key = st.secrets.get("api_key")
        model = next((st.secrets.get(key) for key in MODEL_SECRET_KEYS if st.secrets.get(key)), None)
    except Exception:
        return {
            "ready": False,
            "api_key": "",
            "model": "",
            "error": "找不到 Streamlit secrets 設定。請建立 .streamlit/secrets.toml，或在 Streamlit Cloud Secrets 加入 api_key 與 default_model。",
        }

    missing = []
    if not api_key:
        missing.append("api_key")
    if not model:
        missing.append("default_model 或 model")

    if missing:
        return {
            "ready": False,
            "api_key": "",
            "model": "",
            "error": f"Streamlit secrets 缺少必要欄位：{', '.join(missing)}。",
        }

    return {
        "ready": True,
        "api_key": api_key,
        "model": model,
        "error": "",
    }


runtime_config = validate_runtime_config()

# --- 初始化 Session State ---
if "api_key" not in st.session_state:
    st.session_state.api_key = runtime_config["api_key"]

if "ingredients_input" not in st.session_state:
    st.session_state["ingredients_input"] = random.choice(TEST_SAMPLES)

# --- Google Auth 初始化 ---
authenticator = None
google_auth_config = read_secret("google_auth")
if google_auth_config and Authenticate:
    try:
        authenticator = Authenticate(
            secret_credentials_path='google_credentials.json',
            cookie_name='fridge_roulette_cookie',
            cookie_key=google_auth_config["cookie_key"],
            client_id=google_auth_config["client_id"],
            client_secret=google_auth_config["client_secret"],
            redirect_uri=google_auth_config["redirect_uri"],
        )
        authenticator.check_authenticity()
    except Exception:
        authenticator = None

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
    if runtime_config["ready"]:
        st.success("Secrets 設定已載入。")
        st.text_input("API Key", type="password", value=runtime_config["api_key"], disabled=True)
        st.text_input("AI 模型", value=runtime_config["model"], disabled=True)
    else:
        st.error(runtime_config["error"])

# --- 核心 AI 邏輯 ---
def clean_ai_response(raw):
    """強效清理 AI 回傳內容，移除思考過程與標籤"""
    res = re.sub(r'<thought>.*?</thought>', '', raw, flags=re.DOTALL | re.IGNORECASE)
    res = re.sub(r'```[a-zA-Z]*\n?|```', '', res)
    return res.strip()


def validate_culinary_intent(text):
    """Return a blocking message when input is unrelated, abusive, or prompt-injection-like."""
    normalized = text.strip().lower()
    if not normalized:
        return "請先提供食材。"

    if any(keyword.lower() in normalized for keyword in BLOCKED_KEYWORDS):
        return "輸入內容包含與料理無關或不適合處理的主題，請改為提供食材或烹飪需求。"

    if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in JAILBREAK_PATTERNS):
        return "輸入內容看起來像是在改寫系統規則，請只提供食材或料理偏好。"

    has_culinary_keyword = any(keyword.lower() in normalized for keyword in CULINARY_KEYWORDS)
    has_separator_list = bool(re.search(r"[,，、\n]", text)) and len(text.strip()) >= 2
    if not has_culinary_keyword and not has_separator_list:
        return "目前只支援食材與烹飪相關內容，請輸入冰箱裡的食材。"

    return ""

def identify_ingredients(image_bytes):
    """第一階段：大廚視覺辨識"""
    prompt = "你是一位星級創意大廚。請掃描照片並直接列出看到的食材，以逗號分隔。嚴禁廢話與思考過程。"
    try:
        client = OpenAI(api_key=runtime_config["api_key"], base_url=DEFAULT_BASE_URL)
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        resp = client.chat.completions.create(
            model=runtime_config["model"],
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
        block_reason = validate_culinary_intent(ingredients)
        if block_reason:
            return {"error": block_reason}

        client = OpenAI(api_key=runtime_config["api_key"], base_url=DEFAULT_BASE_URL)
        resp = client.chat.completions.create(
            model=runtime_config["model"],
            messages=[{"role": "system", "content": instruction}, {"role": "user", "content": f"食材：{ingredients}"}],
            response_format={"type": "json_object"}
        )
        raw = clean_ai_response(resp.choices[0].message.content)
        match = re.search(r'(\{.*\})', raw, re.DOTALL)
        if not match:
            return {"error": "AI 回傳格式不完整，沒有取得可解析的 JSON。"}

        parsed = json.loads(match.group(1))
        if not isinstance(parsed, dict) or not isinstance(parsed.get("recipes"), list):
            return {"error": "AI 回傳 JSON 缺少 recipes 清單。"}

        return parsed
    except Exception as e:
        return {"error": f"食譜生成失敗：{str(e)}"}

# --- UI 介面 ---
st.title("🍳 冰箱大轉盤")
st.caption("AI 驅動的星級剩食料理助手")

if not runtime_config["ready"]:
    st.error(runtime_config["error"])
    st.info("本專案現在以 secrets 檔案作為主要設定來源，必要欄位為 api_key 與 default_model。")

with st.expander("📸 第一步：拍照辨識食材", expanded=False):
    photo = st.camera_input("拍照")
    if photo:
        if st.button("🔍 讓大廚清點食材", use_container_width=True):
            if not runtime_config["ready"]:
                st.error(runtime_config["error"])
            else:
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
    if not runtime_config["ready"]:
        st.error(runtime_config["error"])
    elif ingredients.strip():
        with st.spinner("👨‍🍳 大廚正在廚房忙碌中..."):
            result = get_recipes(ingredients, is_mem)
            if result and result.get("error"):
                st.warning(result["error"])
            elif result:
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
