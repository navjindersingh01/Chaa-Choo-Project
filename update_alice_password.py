from werkzeug.security import generate_password_hash
import mysql.connector
import config

print('Connecting to DB...')
cnx = mysql.connector.connect(host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASSWORD, database=config.DB_NAME)
cur = cnx.cursor()
new_hash = generate_password_hash('11111111')
cur.execute('UPDATE users SET password_hash=%s WHERE username=%s', (new_hash, 'alice'))
cnx.commit()
print('Updated alice password')
cur.close()
cnx.close()
