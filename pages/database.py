import sqlite3
import bcrypt

DB_NAME = "database.db"

# 데이터베이스 초기화 함수
def init_db():
    """데이터베이스 및 테이블 초기화"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # `users` 테이블 생성 (role 기본값: user)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        idx INTEGER PRIMARY KEY AUTOINCREMENT,  
        id TEXT UNIQUE NOT NULL,  
        password TEXT NOT NULL,  
        role TEXT NOT NULL DEFAULT 'user'  
    )
    """)

    # `logs` 테이블 생성 (timestamp 기본값: 현재 시간)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        input_type TEXT,
        original_text TEXT,
        summary_text TEXT,
        wordcloud_image TEXT,
        gpt_response TEXT,
        audio_summary_path TEXT,
        audio_response_path TEXT
    )
    """)

    conn.commit()
    conn.close()

# 회원가입 함수 (비밀번호 암호화 후 저장)
def register_user(id, password):
    """새로운 사용자 등록"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()  # `decode()` 추가
    try:
        cursor.execute("INSERT INTO users (id, password) VALUES (?, ?)", (id, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # ID 중복 시 False 반환
    finally:
        conn.close()

# 로그인 검증 함수 (비밀번호 비교)
def login_user(id, password):
    """사용자 로그인 검증"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT password FROM users WHERE id = ?", (id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result and bcrypt.checkpw(password.encode(), result[0].encode()):  # `encode()` 추가
        return True
    return False

# 사용자 권한 검증 함수
def get_user_role(id):
    """사용자의 역할(role) 조회"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT role FROM users WHERE id = ?", (id,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else None

# 로그 저장 함수 추가
def save_log(id, input_type, original_text, summary_text, wordcloud_image, gpt_response, audio_summary_path, audio_response_path):
    """사용자의 실행 로그 저장"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO logs (id, input_type, original_text, summary_text, wordcloud_image, gpt_response, audio_summary_path, audio_response_path) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (id, input_type, original_text, summary_text, wordcloud_image, gpt_response, audio_summary_path, audio_response_path))
    
    conn.commit()
    conn.close()


# 데이터베이스 초기화 실행 (테이블 생성)
if __name__ == "__main__":
    init_db()
    print("데이터베이스 초기화 완료!")