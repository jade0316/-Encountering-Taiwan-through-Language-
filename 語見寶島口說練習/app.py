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
st.set_page_config(page_title="《語見寶島：臺灣生活華語與實務》口說練習", layout="centered")

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
    azure_region = ""
    
    if api_mode == "真實模式 (Azure API)":
        azure_key = st.text_input("Azure Subscription Key", value=default_key, type="password")
        azure_region = st.text_input("Azure Region", value=default_region)

# --- 資料庫 ---
vocab_database = {
    "第一課 便利商店": {
        "便利商店": "biàn lì shāng diàn", "美食": "měi shí", "茶葉蛋": "chá yè dàn",
        "關東煮": "guān dōng zhǔ", "熱狗": "rè gǒu", "飲料": "yǐn liào",
        "櫃臺": "guì tái", "原味": "yuán wèi", "選擇": "xuǎn zé",
        "口味": "kǒu wèi", "悠遊卡": "yōu yóu kǎ", "各式各樣": "gè shì gè yàng",
        "使用": "shǐ yòng", "機器": "jī qì", "發票": "fā piào", "儲值": "chú zhí"
    },
    "第二課 交通與捷運": {
        "搭（車／捷運）": "dā (chē / jié yùn)", "改（搭）": "gǎi (dā)", "準時": "zhǔn shí",
        "環保": "huán bǎo", "熟悉": "shú xī", "按照": "àn zhào",
        "指示牌": "zhǐ shì pái", "建築": "jiàn zhú", "方向感": "fāng xiàng gǎn",
        "適應": "shì yìng", "嘗試": "cháng shì", "捷運": "jié yùn",
        "班次": "bān cì", "路線": "lù xiàn", "經常": "jīng cháng",
        "輛": "liàng", "悠遊卡": "yōu yóu kǎ", "車廂": "chē xiāng"
    },
    "第三課 熱炒店": {
        "點餐": "diǎn cān", "招牌菜": "zhāo pái cài", "氣氛": "qì fēn",
        "熱炒店": "rè chǎo diàn", "份量": "fèn liàng", "清淡": "qīng dàn",
        "配飯": "pèi fàn", "豐富": "fēng fù", "推銷": "tuī xiāo",
        "酒促小姐": "jiǔ cù xiǎo jiě", "剩下": "shèng xià", "打包": "dǎ bāo",
        "浪費": "làng fèi", "結帳": "jié zhàng", "推辭": "tuī cí",
        "請客": "qǐng kè", "搶先": "qiǎng xiān"
    },
    "第四課 住宿": {
        "房客": "fáng kè", "工作人員": "gōng zuò rén yuán", "服務人員": "fú wù rén yuán",
        "棉被": "mián bèi", "毛巾": "máo jīn", "水壓": "shuǐ yā",
        "設備": "shè bèi", "改善": "gǎi shàn", "打掃": "dǎ sǎo",
        "整理": "zhěng lǐ", "換房": "huàn fáng", "滿意": "mǎn yì",
        "立刻": "lì kè", "換洗": "huàn xǐ", "反映": "fǎn yìng", "處理": "chǔ lǐ"
    },
    "第五課 中元節": {
        "中元節": "Zhōng yuán jié", "普渡": "pǔ dù", "好兄弟": "hǎo xiōng dì",
        "供品": "gòng pǐn", "紙錢": "zhǐ qián", "敬拜": "jìng bài",
        "祈福": "qí fú", "生意": "shēng yì", "插香": "chā xiāng",
        "零食": "líng shí", "泡麵": "pào miàn", "祝福": "zhù fú",
        "文化": "wén huà", "供桌": "gòng zhuō", "重視": "zhòng shì",
        "舉辦": "jǔ bàn", "習俗": "xí sú"
    },
    "第六課 伴手禮": {
        "伴手禮": "bàn shǒu lǐ", "團圓": "tuán yuán", "吉祥": "jí xiáng",
        "特色": "tè sè", "禮貌": "lǐ mào", "心意": "xīn yì",
        "象徵": "xiàng zhēng", "喜好": "xǐ hào", "內餡": "nèi xiàn",
        "美味": "měi wèi", "茶葉": "chá yè", "花生": "huā shēng",
        "軟": "ruǎn", "親戚": "qīn qī", "講究": "jiǎng jiù",
        "考慮": "kǎo lǜ", "打算": "dǎ suàn"
    },
    "自訂練習": {}
}

# --- 主頁面邏輯 ---
st.title("《語見寶島：臺灣生活華語與實務》口說練習")
st.divider()

lesson_options = list(vocab_database.keys())
topic = st.selectbox("📚 請選擇課程單元：", lesson_options)

target_text = ""
pinyin = ""

if topic == "自訂練習":
    target_text = st.text_input("⌨️ 請輸入你想練習的句子：", "你好，很高興認識你。")
    pinyin = "Custom Practice"
else:
    current_lesson_words = vocab_database[topic]
    selected_word = st.selectbox("📝 請選擇詞彙：", list(current_lesson_words.keys()))
    target_text = selected_word
    pinyin = current_lesson_words[selected_word]

# 顯示卡片
st.markdown(f"""
<div style="background-color:#fffbe6;padding:30px;border-radius:15px;text-align:center;margin-bottom:20px;border: 3px solid #ffe082;margin-top:20px;">
    <h1 style="color:#e65100;font-size:60px;margin:0;font-weight:800;">{target_text}</h1>
    <p style="color:#8d6e63;font-size:28px;margin-top:15px;">{pinyin}</p>
</div>
""", unsafe_allow_html=True)

# --- 錄音區 ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.write("👇 點擊下方麥克風開始/停止錄音")
    
    if audio_recorder:
        audio_bytes = audio_recorder(
            text="",
            recording_color="#e8b62c",
            neutral_color="#6aa36f",
            icon_name="microphone",
            icon_size="3x",
        )

        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            with st.spinner("正在分析您的發音..."):
                temp_filename = "temp_web_recording.wav"
                with open(temp_filename, "wb") as f:
                    f.write(audio_bytes)

                if api_mode == "真實模式 (Azure API)":
                    if not azure_key or not azure_region:
                        st.error("⚠️ 尚未設定 Azure API Key")
                    else:
                        result, error = assess_pronunciation_from_file(target_text, azure_key, azure_region, temp_filename)
                        if error:
                            st.error(error)
                        else:
                            st.session_state['result'] = result
                            st.session_state['mode'] = 'real'
                else:
                    mock_data = get_mock_score()
                    st.session_state['result'] = mock_data
                    st.session_state['mode'] = 'mock'
    else:
        st.warning("錄音元件載入失敗，請重新整理頁面。")

# --- 結果顯示 ---
if 'result' in st.session_state:
    res = st.session_state['result']
    mode = st.session_state.get('mode')
    
    st.divider()
    
    if mode == 'real':
        accuracy = res.accuracy_score
        fluency = res.fluency_score
        completeness = res.completeness_score
        total = res.pronunciation_score
    else:
        accuracy = res['accuracy_score']
        fluency = res['fluency_score']
        completeness = res['completeness_score']
        total = res['pronunciation_score']

    score_color = "#4caf50" if total >= 80 else "#ff9800" if total >= 60 else "#f44336"

    st.markdown(f"""
    <div style="text-align:center;">
        <p style="margin-bottom:5px;font-size:20px;color:#666;">綜合評分</p>
        <h1 style="color:{score_color};font-size:80px;margin:0;font-weight:bold;">{total:.0f}</h1>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='text-align:center'><h3>準確度</h3><h2 style='color:#555'>{accuracy:.0f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='text-align:center'><h3>流暢度</h3><h2 style='color:#555'>{fluency:.0f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='text-align:center'><h3>完整度</h3><h2 style='color:#555'>{completeness:.0f}</h2></div>", unsafe_allow_html=True)



