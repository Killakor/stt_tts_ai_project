import streamlit as st
from database import register_user, login_user, get_user_role

# ✅ 페이지 설정
st.set_page_config(page_title="🔑 회원가입 및 로그인", layout="centered")

st.title("🔐 로그인 및 회원가입")

# ✅ `st.tabs()`을 사용하여 로그인 및 회원가입 UI 분리
tabs = st.tabs(["🔑 로그인", "📝 회원가입"])

# ✅ 로그인 탭
with tabs[0]:  
    st.subheader("🔑 로그인")
    id = st.text_input("아이디", key="login_id")
    password = st.text_input("비밀번호", type="password", key="login_pw")

    if st.button("로그인"):
        if login_user(id, password):  # ✅ 로그인 검증
            st.success(f"✅ 로그인 성공! {id}님 환영합니다.")
            st.session_state["logged_in"] = True
            st.session_state["id"] = id

            # ✅ 사용자 역할 확인 후 이동
            user_role = get_user_role(id)
            if user_role == "admin":
                st.switch_page("./pages/backoffice.py")  
            else:
                st.switch_page("pages/main.py")  
        else:
            st.error("❌ 아이디 또는 비밀번호가 틀립니다.")

# ✅ 회원가입 탭
with tabs[1]:  
    st.subheader("📝 회원가입")
    id = st.text_input("아이디", key="id")
    password = st.text_input("비밀번호", type="password", key="pw")

    if st.button("회원가입"):
        if register_user(id, password):  # ✅ 회원가입 검증
            st.success("✅ 회원가입 성공! 로그인 해주세요.")
        else:
            st.error("❌ 이미 존재하는 아이디입니다.")
