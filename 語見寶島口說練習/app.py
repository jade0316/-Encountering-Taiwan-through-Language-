import streamlit as st
import os
import time
import random

# 嘗試匯入 Azure SDK
try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None

# 匯入錄音元件
try:
    from audio_recorder_streamlit import audio_recorder
except ImportError:
    st.error("系統偵測不到錄音元件，請確認 requirements.txt 是否正確設定。")
    audio_recorder = None

# --- 頁面設定 ---
st.set_page_config(page_title="華語文口說評測教練", page_icon="🇹🇼", layout="centered")

# CSS 優化
st.markdown(
    """
    <style>
    .stSelectbox label p { font-size: 24px !important; font-weight: bold !important; color: #1f77b4 !important; }
    .stTextInput label p { font-size: 24px !important; font-weight: bold !important; }
    .stSelectbox div[data-baseweb="select"] > div { font-size: 20px !important; }
    .stButton button { font-size: 22px !important; padding: 10px 24px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 核心功能：Azure 發音評測 ---
def assess_pronunciation_from_file(reference_text, subscription_key, region, filename):
    if not speechsdk:
        return None, "Azure SDK 未安裝，請檢查 requirements.txt"

    try:
        speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
        speech_config.speech_recognition_language = "zh-TW" 
        clean_reference_text = reference_text.replace("（", "").replace("）", "").replace("／", "").replace("/", "")

        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=clean_reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True
        )

        audio_config = speechsdk.audio.AudioConfig(filename=filename)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        pronunciation_config.apply_to(recognizer)

        result = recognizer.recognize_once_async().get()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pronunciation_result = speechsdk.PronunciationAssessmentResult(result)
            return pronunciation_result, None
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return None, "無法辨識語音，可能是聲音太小或背景雜音。"
        elif result.reason == speechsdk.ResultReason.Canceled:
            return None, "辨識取消或是連線錯誤"
            
    except Exception as e:
        return None, f"發生錯誤: {str(e)}"

    return None, "未知錯誤"

# --- 模擬數據 ---
def get_mock_score():
    time.sleep(0.8)
    return {
        "accuracy_score": random.randint(70, 98),
        "fluency_score": random.randint(60, 95),
        "completeness_score": random.randint(80, 100),
        "pronunciation_score": random.randint(70, 96)
    }

# --- 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 設定")
    default_key = st.secrets.get("AZURE_KEY", "")
    default_region = st.secrets.get("AZURE_REGION", "")

    api_mode = st.radio("選擇模式", ["演示模式 (模擬分數)", "真實模式 (Azure API)"])
    
    azure_key = ""
    azure
