import hashlib
from datetime import datetime
import os


def check_password(password: str) -> bool:
    #HPに予め決められたパスワードのハッシュ化した値が代入されています
    hashed_password = os.environ["HP"]

    #ログイン画面で入力されたパスワードをハッシュ化します
    hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()

    #予め決められたパスワードをハッシュ化したhashed_passwordと入力されたパスワードをハッシュ化したhashedを比較
    return hashed == hashed_password


# 時間、ハッシュ化されたパスワード、バイアスからセッションキーの生成
# 形式　"{時間},{キー}"
def create_session_key(time: datetime) -> str:
    hashed_password = os.environ["HP"]
    bias = os.environ["BIAS"]

    unix_time_str = str(int(time.timestamp()))

    m = hashlib.sha256()
    m.update(unix_time_str.encode("utf-8"))
    m.update(hashed_password.encode("utf-8"))
    m.update(bias.encode("utf-8"))
    key = m.hexdigest()

    return f"{unix_time_str},{key}"


# セッションキーの確認
def check_session_key(session_key: str) -> bool:
    timeout = int(os.environ["TIMEOUT"])
    hashed_password = os.environ["HP"]
    bias = os.environ["BIAS"]

    data = session_key.split(",")

    if len(data) < 2:
        return False

    session_time, session_key = data
    session_time = int(session_time)

    now = int(datetime.now().timestamp())

    if now - session_time > timeout:
        return False

    m = hashlib.sha256()
    m.update(str(session_time).encode("utf-8"))
    m.update(hashed_password.encode("utf-8"))
    m.update(bias.encode("utf-8"))
    key = m.hexdigest()

    return session_key == key
