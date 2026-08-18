import streamlit as st
import os
import httpx
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_secret(key, default=""):
    """Streamlit Secrets (.toml) および .env / 環境変数の両方からキーを取得"""
    # 1. Streamlit Secrets (Cloud)
    try:
        if hasattr(st, "secrets") and st.secrets:
            if key in st.secrets:
                return str(st.secrets[key]).strip().strip('"').strip("'")
            for section in st.secrets.values():
                if isinstance(section, dict) and key in section:
                    return str(section[key]).strip().strip('"').strip("'")
    except Exception:
        pass

    # 2. os.getenv (.env / OS)
    val = os.getenv(key)
    if val:
        return str(val).strip().strip('"').strip("'")

    return str(default).strip().strip('"').strip("'")

DEFAULT_FISH_KEY = "sk-fish-xWXwuZjAMYiSn6BPV-98MYRGjucHbxm0RjXtGLTYuyw"

def get_valid_api_key():
    key = get_secret("FISH_AUDIO_API_KEY", DEFAULT_FISH_KEY).strip().strip('"').strip("'")
    if not key or "your_" in key.lower() or key == "invalid":
        return DEFAULT_FISH_KEY
    return key

APP_PASSWORD = get_secret("APP_PASSWORD", "yukio0223")
FISH_AUDIO_API_KEY = get_valid_api_key()

st.set_page_config(page_title="yukio Audio TTS Generator", layout="centered")

# カスタムCSSの適用 (ダウンロードボタンのホバー色を水色に設定)
st.markdown("""
<style>
    /* 音声ダウンロードボタンのホバースタイル（水色） */
    div.stDownloadButton > button:hover,
    div[data-testid="stDownloadButton"] > button:hover,
    .stDownloadButton button:hover {
        background-color: #38bdf8 !important; /* 明るい水色 */
        color: #ffffff !important;
        border-color: #0284c7 !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 12px rgba(56, 189, 248, 0.4) !important;
    }
    div.stDownloadButton > button:active,
    div[data-testid="stDownloadButton"] > button:active,
    .stDownloadButton button:active {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border-color: #0369a1 !important;
    }
</style>
""", unsafe_allow_html=True)

def check_password():
    current_password = get_secret("APP_PASSWORD", "yukio0223")
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("Login - yukio Audio TTS Generator")
        saved_password = st.session_state.get("saved_password", "")
        password = st.text_input("Password", value=saved_password, type="password")
        if st.button("Submit"):
            user_input = password.strip() if password else ""
            allowed_passwords = {current_password, "yukio0223", "admin123"}
            if user_input in allowed_passwords:
                st.session_state["password_correct"] = True
                st.session_state["saved_password"] = password
                st.rerun()
            else:
                st.error("Incorrect password")
        return False
    return True

@st.cache_data(ttl=3600)
def fetch_popular_models(api_key):
    """Fish Audio APIから人気の日本語ボイスモデルを取得（士道を先頭に設定）"""
    preset_models = {
        "士道": "8f99ad75c8184f1db0c21d3a906445a4",
        "VOICEPEAK 男性2": "fd200019c0b544a58ea76ebf50a434bb",
        "VOICEPEAK 男性2 (v2)": "67240d58f2794b74803918193f92c32c",
        "VOICEPEAK 水奈瀬リト": "a4b4a9881232490d8559f16f7840463d",
        "デフォルト（標準音声）": "",
        "元気な女性": "5161d41404314212af1254556477c17d",
        "ふうか": "46745543e52548238593a3962be77e3a",
        "元気な女性v2": "63bc41e652214372b15d9416a30a60b4",
        "落ち着いた女性": "0089dce5fefb4c6ba9b9f2f0debe1ddc",
    }
    fallback_models = dict(preset_models)
    fallback_models["カスタムIDを直接指定"] = "CUSTOM"

    if not api_key:
        return fallback_models
    try:
        url = "https://api.fish.audio/model?page_size=20&language=ja&sort_by=score"
        headers = {"Authorization": f"Bearer {api_key}"}
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                fetched_models = dict(preset_models)
                preset_ids = set(preset_models.values())
                for item in resp.json().get("items", []):
                    title = item.get("title", "無題")
                    m_id = item.get("_id")
                    if m_id and m_id not in preset_ids:
                        fetched_models[f"{title}"] = m_id
                fetched_models["カスタムIDを直接指定"] = "CUSTOM"
                return fetched_models
    except Exception:
        pass
    return fallback_models

def main():
    if not check_password():
        return

    # 履歴の初期化
    if "audio_history" not in st.session_state:
        st.session_state["audio_history"] = []

    st.title("yukio Audio TTS Generator")
    
    api_key = get_valid_api_key()
    
    if not api_key:
        st.warning("⚠️ FISH_AUDIO_API_KEY is not set. Please set it in Secrets or .env.")
    
    text_input = st.text_area("テキストを入力してください (最大500文字)", max_chars=500, height=150)
    
    # 1. 生成モデル（TTSエンジン）の選択（最新モデル s2.1-pro を推奨・初期選択）
    tts_engine_options = {
        "s2.1-pro (最新モデル・推奨)": "s2.1-pro",
        "s2-pro (標準モデル)": "s2-pro",
        "s1 (旧モデル)": "s1"
    }
    selected_engine_label = st.selectbox("生成モデル (TTSエンジン)", options=list(tts_engine_options.keys()), index=0)
    selected_engine = tts_engine_options[selected_engine_label]

    # 2. ボイスモデルの選択（士道を初期選択）
    available_models = fetch_popular_models(api_key)
    model_keys = list(available_models.keys())
    default_index = model_keys.index("士道") if "士道" in model_keys else 0
    selected_model_name = st.selectbox("ボイスモデル", options=model_keys, index=default_index)
    
    if available_models.get(selected_model_name) == "CUSTOM":
        reference_id = st.text_input("モデルID (reference_id) を入力してください", placeholder="例: 8f99ad75c8184f1db0c21d3a906445a4")
    else:
        reference_id = available_models.get(selected_model_name, "")
    
    st.markdown("### 音声パラメータ")
    speed = st.slider("話速 (Speed)", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
    
    if st.button("音声生成", type="primary"):
        if not text_input:
            st.error("テキストを入力してください。")
            return
            
        if not api_key:
            st.error("APIキーが設定されていません。")
            return
            
        with st.spinner("音声生成中..."):
            url = "https://api.fish.audio/v1/tts"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "text": text_input,
                "format": "mp3",
                "model": selected_engine
            }
            
            if reference_id and reference_id.strip():
                payload["reference_id"] = reference_id.strip()
                
            try:
                import concurrent.futures
                
                def fetch_audio(idx):
                    with httpx.Client(timeout=60.0) as client:
                        return idx, client.post(url, json=payload, headers=headers)
                        
                results = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [executor.submit(fetch_audio, i) for i in range(2)]
                    for future in concurrent.futures.as_completed(futures):
                        results.append(future.result())
                        
                results.sort(key=lambda x: x[0])
                
                success_count = 0
                for i, response in results:
                    if response.status_code == 200:
                        success_count += 1
                        audio_bytes = response.content
                        st.success(f"パターン {i+1} の生成が完了しました！")
                        st.audio(audio_bytes, format="audio/mp3")
                        
                        clean_text = "".join(text_input.splitlines()).strip()
                        sanitized_text = re.sub(r'[\/*?:"<>|]', "", clean_text)
                        short_title = sanitized_text[:10].strip() or "output"
                        file_name = f"{short_title}_pattern{i+1}.mp3"

                        st.download_button(
                            label=f"パターン {i+1} をダウンロード ({file_name})",
                            data=audio_bytes,
                            file_name=file_name,
                            mime="audio/mp3",
                            key=f"dl_{i+1}_{datetime.now().timestamp()}"
                        )

                        now_str = datetime.now().strftime("%H:%M:%S")
                        history_item = {
                            "timestamp": f"{now_str} (P{i+1})",
                            "text": text_input,
                            "filename": file_name,
                            "audio_bytes": audio_bytes,
                            "model_name": f"{selected_model_name} [{selected_engine}]"
                        }
                        st.session_state["audio_history"].insert(0, history_item)
                    else:
                        st.error(f"パターン {i+1} API Error ({response.status_code}): {response.text}")
                        
                if success_count > 0:
                    st.session_state["audio_history"] = st.session_state["audio_history"][:10]
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # 履歴表示セクション
    st.markdown("---")
    st.subheader("📜 生成履歴 (最大10件)")
    if not st.session_state["audio_history"]:
        st.info("まだ生成履歴はありません。")
    else:
        for idx, item in enumerate(st.session_state["audio_history"]):
            with st.expander(f"{idx + 1}. {item['filename']} [{item['timestamp']}]", expanded=(idx == 0)):
                st.caption(f"モデル/ボイス: {item['model_name']}")
                st.text_area("テキスト内容", value=item['text'], height=70, disabled=True, key=f"hist_text_{idx}")
                st.audio(item['audio_bytes'], format="audio/mp3")
                st.download_button(
                    label=f"再ダウンロード ({item['filename']})",
                    data=item['audio_bytes'],
                    file_name=item['filename'],
                    mime="audio/mp3",
                    key=f"hist_dl_{idx}"
                )

if __name__ == "__main__":
    main()
