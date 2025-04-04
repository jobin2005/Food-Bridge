from dotenv import load_dotenv
import oracledb
import os

load_dotenv()
env = {key: os.getenv(key) for key in ['USER','PASS','DSN','CONFIG','WLTLOC','WLTPASS']}

# Use Thin Mode (no Oracle Instant Client required)
oracledb.defaults.fetch_lobs = False  # Improve performance

script_dir = os.path.dirname(os.path.abspath(__file__))
wallet_relative_path = 'Wallet_FOODBRIDGE'
env["FILEPATH"] = os.path.join(script_dir, wallet_relative_path).replace('\\','/')

class NonQueryError(Exception):

    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.message} (Error Code: {self.error_code})"
    
class NonInsertionError(Exception):

    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.message} (Error Code: {self.error_code})"
#Update Exception
class NonUpdateError(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.args[0]} (Error Code: {self.error_code})"

class NonUpdateError(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.args[0]} (Error Code: {self.error_code})"

def query(sql, params=None):
    if isinstance(sql, str) and sql.strip().upper().startswith("SELECT"):
        with oracledb.connect(user=env["USER"], password=env["PASS"], dsn=env["DSN"], config_dir=env["FILEPATH"], wallet_location=env["FILEPATH"], wallet_password=env["WLTPASS"]) as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)

                return cursor.fetchall()
    else:
        raise NonQueryError("The given SQL command is not a SELECT query", 400)

    
def insert(sql, params=None):
    if isinstance(sql, str) and sql.strip().upper().startswith("INSERT"):
        with oracledb.connect(user=env["USER"], password=env["PASS"], dsn=env["DSN"], config_dir=env["FILEPATH"], wallet_location=env["FILEPATH"], wallet_password=env["WLTPASS"]) as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                conn.commit()
    else:
        raise NonInsertionError("The given sql command is not a INSERT command", 400)
    
def update(sql, params=None):
    if isinstance(sql, str) and sql.strip().upper().startswith("UPDATE"):
        with oracledb.connect(user=env["USER"], password=env["PASS"], dsn=env["DSN"], config_dir=env["FILEPATH"], wallet_location=env["FILEPATH"], wallet_password=env["WLTPASS"]) as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                conn.commit()  # ✅ Ensure changes are saved
    else:
        raise NonUpdateError("The given SQL command is not an UPDATE command", 400)