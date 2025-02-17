import streamlit as st
import sqlite3
from pages.database import get_user_role, DB_NAME

# ✅ 로그인 상태 확인 및 관리자 권한 체크
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("🚨 로그인이 필요합니다!")
    st.stop()

id = st.session_state.get("id")
user_role = get_user_role(id)

if user_role != "admin":
    st.error("❌ 접근 권한이 없습니다. 관리자 계정만 접근 가능합니다.")
    st.stop()

# ✅ Streamlit 페이지 설정
st.set_page_config(page_title="📊 백오피스 관리", layout="wide")

st.title("📊 백오피스 관리")
st.info("🔍 사용자 로그 조회 및 권한 변경 기능을 제공합니다.")

# ✅ 데이터베이스 연결 함수
def connect_db():
    return sqlite3.connect(DB_NAME)

# ✅ 사용자 목록 가져오기
def get_users():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

# ✅ 선택한 사용자의 로그 조회 함수
def get_user_logs(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs WHERE id = ? ORDER BY timestamp DESC", (user_id,))
    logs = cursor.fetchall()
    conn.close()
    return logs

# ✅ 사용자 권한 변경 함수
def update_user_role(user_id, role):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    conn.close()

# ✅ 사용자 선택 UI
users = get_users()
user_dict = {user[0]: user[1] for user in users}  # ID: role 매핑
user_list = list(user_dict.keys())

# ✅ 기존 선택된 사용자 유지
if "selected_user" not in st.session_state:
    st.session_state["selected_user"] = user_list[0]  # 첫 번째 사용자 기본 선택

selected_user = st.selectbox("🔍 사용자 선택", user_list, index=user_list.index(st.session_state["selected_user"]))

# ✅ 세션 상태에 선택한 사용자 저장 (중복 선택 시 초기화 방지)
if selected_user != st.session_state["selected_user"]:
    st.session_state["selected_user"] = selected_user

if selected_user:
    st.subheader(f"📂 `{selected_user}` 님의 실행 로그")

    logs = get_user_logs(selected_user)
    if logs:
        st.write("📜 최근 실행 내역")
        log_table = []
        for log in logs:
            log_table.append({
                "시간": log[1],
                "입력 유형": log[2],
                "원문 텍스트": log[3],
                "요약문": log[4],
                "GPT 응답": log[6],
                "음성 요약": log[7],
                "음성 응답": log[8],
            })
        import pandas as pd
        df = pd.DataFrame(log_table)
        st.dataframe(df)
    else:
        st.warning("📭 해당 사용자의 실행 로그가 없습니다.")

    # ✅ 현재 사용자 역할 표시 및 변경 기능
    st.subheader("⚙️ 사용자 권한 관리")
    current_role = user_dict[selected_user]
    new_role = st.radio("변경할 역할을 선택하세요", ["user", "admin"], index=0 if current_role == "user" else 1)

    if st.button("✅ 권한 변경"):
        if current_role != new_role:
            update_user_role(selected_user, new_role)
            st.success(f"✅ `{selected_user}`님의 역할이 `{new_role}`(으)로 변경되었습니다.")
            st.session_state["user_roles_updated"] = True  # UI 업데이트 플래그 추가
        else:
            st.warning("🚨 변경된 사항이 없습니다.")

# ✅ 관리자용 홈 이동 버튼
st.sidebar.title("📌 메뉴")
st.sidebar.info(f"🔑 **{id}님 (관리자)**")

if st.sidebar.button("🏠 메인 페이지 이동"):
    st.switch_page("main.py")

if st.sidebar.button("🔒 로그아웃"):
    st.session_state["logged_in"] = False
    st.session_state["id"] = None
    st.switch_page("login.py")
