import streamlit as st
import numpy as np
import sounddevice as sd
import tempfile
import wave
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate 
from gtts import gTTS
import os
from datetime import datetime
import matplotlib.pyplot as plt
import altair as alt
from wordcloud import WordCloud
import re
from collections import Counter
from dotenv import load_dotenv
from openai import OpenAI
from pages.database import get_user_role, save_log

## 변수
# 환경변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("🚨 로그인이 필요합니다!")
    st.stop()

# 세션 상태 초기화 (필수)
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "id" not in st.session_state:
    st.session_state["id"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "login"
if "slider_value" not in st.session_state:
    st.session_state["slider_value"] = 60  # 기본 녹음 길이 (초)

# 현재 로그인한 사용자 정보 (KeyError 방지)
id = st.session_state.get("id", None)
user_role = get_user_role(id) if id else None

if user_role == "admin":
    name = "관리자"
else: 
    name = "입시매니저"


## 함수
# STT 처리 함수
def transcribe_audio(audio_file):
    """음성 파일을 Whisper API로 변환하는 함수"""
    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )
    return result  # 텍스트 변환 결과 반환

# GPT 요약 함수
def generate_summary(text):
    """GPT-4o-mini를 사용하여 텍스트 요약 생성"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"다음 대화를 간결하게 요약하세요:\n\n{text}, 만약 대화상대가 두명 이상이면 대화상대의 이름을 대화내용에서 유추하여 적어주세요."}],
        temperature=0.7
    )
    return response.choices[0].message.content  # 요약된 텍스트 반환

# TTS 변환 함수
def text_to_speech(text):
    """텍스트를 음성으로 변환하는 함수"""
    tts = gTTS(text, lang="ko")
    return tts

# 워드클라우드 생성 함수
def generate_wordcloud(text):
    """워드클라우드 생성"""
    words = re.findall(r'\b\w+\b', text)
    word_freq = Counter(words)
    wordcloud = WordCloud(
        width=900, height=400, background_color="white", font_path="C:/Windows/Font/malgun.ttf"
    ).generate_from_frequencies(word_freq)
    return wordcloud

# GPT 대화 응답 생성 함수
def get_gpt_response(user_text):
    """GPT-4o-mini를 사용하여 대화 응답 생성"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"사용자의 질문: {user_text}\nGPT의 답변:"}],
        temperature=0.7
    )
    return response.choices[0].message.content

# 사용가능 오디오 입력장치 확인 함수
def get_input_device():
    try:
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]  # 입력 채널이 있는 장치만 필터링
        
        if not input_devices:
            return None  # 사용 가능한 입력 장치가 없을 경우

        return input_devices[0]['index']  # 기본적으로 첫 번째 입력 장치 반환
    except Exception as e:
        print(f"⚠️ 오디오 장치 확인 중 오류 발생: {e}")
        return None

# 녹음 함수 (디바이스가 없을 경우 예외 처리)
def record_audio(duration, sample_rate):
    input_device = get_input_device()

    if input_device is None:
        st.warning("⚠️ 사용 가능한 오디오 입력 장치가 없습니다! 마이크를 연결해주세요.")
        return None  # 녹음 실행하지 않음

    try:
        # 마이크 녹음 실행
        recorded_audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=2,
            dtype=np.int16,
            device=input_device  # 올바른 장치 사용
        )
        sd.wait()
        return recorded_audio
    except sd.PortAudioError as e:
        st.error(f"⚠️ 오디오 장치 오류 발생: {e}")
        return None

# 파일 지정 경로 생성 함수
def generate_file_path(id, file_name, extension):
    """사용자 ID와 현재 타임스탬프 기반으로 고유한 파일명을 생성하는 함수"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_path = os.path.join("logs", id)
    
    # 폴더가 없으면 생성
    os.makedirs(folder_path, exist_ok=True)

    file_name = f"{id}_{file_name}_{timestamp}.{extension}"
    return os.path.join(folder_path, file_name)


## 메인
# Streamlit UI 설정
st.set_page_config(page_title="🎙️ 음성 기반 AI 요약 서비스", layout="wide")

st.image("https://img.uway.com/2021_re/img/logo.png", width=140)
st.title("AI 음성 요약 서비스")
st.info("🔊 **음성 파일**을 업로드하거나 **실시간 녹음**하여 **텍스트 변환 및 요약**을 받을 수 있습니다.")

# 사이드바 설정
if st.session_state["logged_in"]:
    st.sidebar.title(f"**{id}님 환영합니다!**")
    st.sidebar.subheader("권한: " + name)

    if user_role == "admin":
        page = st.sidebar.radio("이동할 페이지를 선택하세요", ["메인 페이지", "백오피스"])
        if page == "사용자 메인":
            st.switch_page("pages/backoffice.py")
        else:
            st.switch_page("pages/main.py")

    # 로그아웃 버튼 추가
    st.sidebar.markdown("---")  
    if st.sidebar.button("🔒 로그아웃"):
        st.session_state["logged_in"] = False
        st.session_state["id"] = None
        st.session_state["page"] = "login"
        st.rerun()

# 입력 방식 선택 (탭 활용)
tab1, tab2 = st.tabs(["📂 파일 업로드", "🎙️ 실시간 녹음"])
### **TAB 1: 파일 업로드**
with tab1:
    st.subheader("📂 파일 업로드")
    uploaded_file = st.file_uploader("📂 음성 파일을 업로드하세요", type=["mp3", "wav", "mp4"])

    if uploaded_file is not None:
        with st.spinner("🛠️ 음성을 텍스트로 변환 중입니다..."):
            # 파일 저장 후 Whisper API 호출
            audio_file_path = generate_file_path(id, "uploaded_audio", uploaded_file.name.split('.')[-1])

            with open(audio_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 올바른 파일 경로를 사용하여 STT 변환
            with open(audio_file_path, "rb") as audio_file:
                full_text = transcribe_audio(audio_file)

        # STT 결과 표시 (아코디언 형태)
        with st.expander("📌 전체 대화 내용"):
            st.write(full_text)

        # GPT-4o-mini 요약 생성
        with st.spinner("🤖 변환된 음성에 대한 요약문을 생성 중입니다..."):
            summary_text = generate_summary(full_text)

        # 컬럼 레이아웃으로 요약 & 워드클라우드 배치
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📜 대화 요약 결과")
            st.write(summary_text)
            st.download_button("📥 요약 파일 다운로드", data=summary_text, file_name=f"{id}_summary.txt")

        with col2:
            # 워드클라우드 생성
            with st.spinner("☁️ 키워드를 생성 중입니다..."):
                wordcloud = generate_wordcloud(full_text)
                wordcloud_path = generate_file_path(id, "wordcloud", "png")
                wordcloud.to_file(wordcloud_path)

                fig, ax = plt.subplots(figsize=(6, 3))
                ax.imshow(wordcloud, interpolation="bilinear")
                ax.axis("off")
                st.subheader("☁️ 핵심 키워드")
                st.pyplot(fig)

                # 워드클라우드 이미지 다운로드 기능 추가
                with open(wordcloud_path, "rb") as wc_file:
                    st.download_button("📥 키워드 다운로드", wc_file, file_name=f"{id}_wordcloud.png")

        # TTS 변환 및 다운로드
        with st.spinner("🔊 텍스트를 음성으로 변환 중입니다..."):
            tts = text_to_speech(summary_text)
            audio_summary_path = generate_file_path(id, "summary_audio", "mp3")
            tts.save(audio_summary_path)

        with open(audio_summary_path, "rb") as audio_file:
            st.download_button("📥 요약 음성 다운로드", data=audio_file, file_name=f"{id}_summary_audio.mp3")

        # 로그 저장 (파일명 & 데이터 수정)
        save_log(
            id=id,
            input_type="파일 업로드",
            original_text=full_text,
            summary_text=summary_text,
            wordcloud_image=wordcloud_path,
            gpt_response=summary_text,
            audio_summary_path=audio_summary_path,
            audio_response_path="N/A"
        )

### **TAB 2: 실시간 녹음**
with tab2:
    st.subheader("🎤 실시간 녹음")

    # 슬라이더 상태 유지 (페이지 리로드 없이 값만 업데이트)
    duration = st.slider("녹음 길이 (초)", 30, 1200, st.session_state["slider_value"])

    st.session_state.update({"slider_value": duration})
    sample_rate = 44100  

    if st.button("🎙️ 녹음 시작"):
        with st.spinner(f"🎤 {duration}초 동안 녹음 중..."):
            recorded_file_path = generate_file_path(id, "recorded_audio", "wav")
            recorded_audio = record_audio(duration, sample_rate)

        if recorded_audio is not None:
            with wave.open(recorded_file_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(recorded_audio.tobytes())

            st.success(f"🎤 {duration}초 동안 녹음이 완료되었습니다!")

        with st.spinner("🛠️ 음성을 텍스트로 변환 중입니다..."):
            with open(recorded_file_path, "rb") as audio_file:
                user_text = transcribe_audio(audio_file)

        st.text_area("📌 전체 음성 내용", user_text, height=500)

        # GPT 요약문 생성
        with st.spinner("🤖 변환된 음성에 대한 요약문을 생성 중입니다..."):
            summary_text = generate_summary(user_text)

        # GPT 응답 생성
        with st.spinner("🤖 GPT 응답 생성 중입니다..."):
            response = get_gpt_response(user_text)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📜 대화 요약 결과")
            st.write(summary_text)
            st.download_button("📥 요약 파일 다운로드", data=summary_text, file_name=f"{id}_summary.txt")

        with col2:
            # 워드클라우드 생성
            with st.spinner("☁️ 키워드를 생성 중입니다..."):
                wordcloud = generate_wordcloud(user_text)
                wordcloud_path = generate_file_path(id, "wordcloud", "png")
                wordcloud.to_file(wordcloud_path)

                fig, ax = plt.subplots(figsize=(6, 3))
                ax.imshow(wordcloud, interpolation="bilinear")
                ax.axis("off")
                st.subheader("☁️ 핵심 키워드")
                st.pyplot(fig)

        # TTS 변환 및 다운로드
        with st.spinner("🔊 텍스트를 음성으로 변환 중입니다..."):
            tts = text_to_speech(summary_text)
            audio_summary_path = generate_file_path(id, "summary_audio", "mp3")
            tts.save(audio_summary_path)

        with open(audio_summary_path, "rb") as audio_file:
            st.download_button("📥 요약 음성 다운로드", data=audio_file, file_name=f"{id}_summary_audio.mp3")

        # 로그 저장 (파일명 & 데이터 수정)
        save_log(
            id=id,
            input_type="실시간 녹음",
            original_text=user_text,
            summary_text=summary_text,
            wordcloud_image=wordcloud_path,
            gpt_response=response,
            audio_summary_path=audio_summary_path,
            audio_response_path="N/A"
        )