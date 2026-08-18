import streamlit as st
import os
import httpx
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

APP_PASSWORD = os.getenv("APP_PASSWORD", "admin123")
FISH_AUDIO_API_KEY = os.getenv("FISH_AUDIO_API_KEY", "")

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
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("Login - yukio Audio TTS Generator")
        saved_password = st.session_state.get("saved_password", "")
        password = st.text_input("Password", value=saved_password, type="password")
        if st.button("Submit"):
            if password == APP_PASSWORD:
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
    
    if not FISH_AUDIO_API_KEY:
        st.warning("⚠️ FISH_AUDIO_API_KEY is not set in the environment variables (.env). Please set it to use the API.")
    
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
    available_models = fetch_popular_models(FISH_AUDIO_API_KEY)
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
            
        if not FISH_AUDIO_API_KEY:
            st.error("APIキーが設定されていません。")
            return
            
        with st.spinner("音声生成中..."):
            url = "https://api.fish.audio/v1/tts"
            headers = {
                "Authorization": f"Bearer {FISH_AUDIO_API_KEY}",
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
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    audio_bytes = response.content
                    st.success("音声生成が完了しました！")
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    # 入力テキストの先頭10文字からファイル名を生成（記号・改行を除去）
                    clean_text = "".join(text_input.splitlines()).strip()
                    sanitized_text = re.sub(r'[\\/*?:"<>|]', "", clean_text)
                    short_title = sanitized_text[:10].strip() or "output"
                    file_name = f"{short_title}.mp3"

                    st.download_button(
                        label=f"音声をダウンロード ({file_name})",
                        data=audio_bytes,
                        file_name=file_name,
                        mime="audio/mp3"
                    )

                    # 履歴の保存（最大10件）
                    now_str = datetime.now().strftime("%H:%M:%S")
                    history_item = {
                        "timestamp": now_str,
                        "text": text_input,
                        "filename": file_name,
                        "audio_bytes": audio_bytes,
                        "model_name": f"{selected_model_name} [{selected_engine}]"
                    }
                    st.session_state["audio_history"].insert(0, history_item)
                    st.session_state["audio_history"] = st.session_state["audio_history"][:10]

                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
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
