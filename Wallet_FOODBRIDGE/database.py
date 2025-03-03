import oracledb

from details import usr, passwd, dsn, config, wltloc, wltpass

# Use Thin Mode (no Oracle Instant Client required)
oracledb.defaults.fetch_lobs = False  # Improve performance

sql = "INSERT INTO allusers VALUES (103, 'volunteer')"
search = "SELECT * FROM allusers"

with oracledb.connect(user=usr, password=passwd, dsn=dsn, config_dir=config, wallet_location=wltloc, wallet_password=wltpass) as conn:
    with conn.cursor() as cursor:
        cursor.execute(sql)
        conn.commit()

        for r in cursor.execute(search):
            print(r)