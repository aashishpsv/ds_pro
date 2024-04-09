import hashlib
import sqlite3
import twilio.rest as tr

# Global constants
ADMIN_ID = 0
ADMIN_HASH = '4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2'

def executeQuery(query):
	connector = sqlite3.connect('database.db')
	cursor = connector.cursor()
	try:
		cursor.execute(query)
		connector.commit()
		result = cursor.fetchall()
		data = [True, result, cursor.description]
		cursor.close()
		connector.close()
		return data
	except sqlite3.Error as sqe:
		return [False, sqe]

def createDatabase():
	status = executeQuery('''
		CREATE TABLE IF NOT EXISTS CUSTOMERS(
			account_num INTEGER PRIMARY KEY AUTOINCREMENT,
			first_name VARCHAR(20) NOT NULL,
			last_name VARCHAR(20) NOT NULL,
			aadhar_num VARCHAR(16) UNIQUE NOT NULL,
			phone_num VARCHAR(12) UNIQUE NOT NULL,
			sms CHAR(1) NOT NULL,
			balance FLOAT NOT NULL
		)
	''')
	if not status[0]: return status

	status = executeQuery('''
		CREATE TABLE IF NOT EXISTS TRANSACTIONS(
			transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
			from_account INTEGER NOT NULL,
			to_account INTEGER NOT NULL,
			amount FLOAT NOT NULL,
			type VARCHAR(10),
			date varchar(20),
			FOREIGN KEY (from_account, to_account) REFERENCES CUSTOMERS(account_num, account_num)
		)
	''')
	if not status[0]: return status

	status  = executeQuery('''
		CREATE TABLE IF NOT EXISTS AUTH(
			account_num INTEGER,
			password varchar(100) NOT NULL,
			FOREIGN KEY (account_num) REFERENCES CUSTOMERS(account_num) ON DELETE CASCADE
		)
	''')
	return status

def sha256Hash(string: str) -> str:
	return hashlib.sha256(string.encode()).hexdigest()

def isUserAdmin(accountNumber: int, password: str) -> bool:
	passHash = sha256Hash(password)
	return (accountNumber == ADMIN_ID and passHash == ADMIN_HASH)

def doesValueExist(field: str, value: any) -> bool:
	if isinstance(value, str):
		value = "'" + value + "'"
	
	status = executeQuery('''
		SELECT {}
		FROM CUSTOMERS
		WHERE {}={}
	'''.format(field, field, value)
	)
	return len(status[1])>0

def authenticate(accountNumber: int, password: str) -> bool:
	passhash = sha256Hash(password)
	status = executeQuery('''
		SELECT account_num
		FROM AUTH 
		WHERE account_num={} AND password='{}'
	'''.format(accountNumber, passhash)
	)
	return len(status[1])>0

def sendSMS(accounts, amount, type, date):
	account_sid = 'ACd9ac09604561be5c00ae44340b3d92b1'
	auth_token = '2640171df4b3b27a208ed83a8c0b10e2'
	client = tr.Client(account_sid, auth_token)

	phone = None
	body = None
	if type == 'd':
		status = executeQuery('''
			SELECT phone_num
			FROM CUSTOMERS
			WHERE account_num={}
		'''.format(accounts[0])
		)
		phone = '+91' + status[1][0][0]
		body = ('manipal bank account XXX' + str(accounts[0]).zfill(3)[-3:] 
			+ ' was credited for Rs ' + str(amount) + ' on ' + date + '.'
		)

	elif type == 'w':
		status = executeQuery('''
			SELECT phone_num
			FROM CUSTOMERS
			WHERE account_num={}
		'''.format(accounts[0])
		)
		phone = '+91' + status[1][0][0]
		body = ('manipal bank account XXX' + str(accounts[0]).zfill(3)[-3:] 
			+ ' was debited for Rs ' + str(amount) + ' on ' + date + '.'
		)

	elif type == 'ts':
		status = executeQuery('''
			SELECT phone_num
			FROM CUSTOMERS
			WHERE account_num={}
		'''.format(accounts[0])
		)
		status = executeQuery('''
			SELECT first_name
			FROM CUSTOMERS
			WHERE account_num={}
		'''.format(accounts[1])
		)
		firstName = status[1][0][0]
		status = executeQuery('''
			SELECT last_name
			FROM CUSTOMERS
			WHERE account_num={}
		'''.format(accounts[1])
		)
		lastName = status[1][0][0]
		name = firstName.upper() + ' ' + lastName.upper()

		status = executeQuery('''
			SELECT phone_num
			FROM CUSTOMERS
			WHERE account_num={}
		'''.format(accounts[1])
		)
		phone = '+91' + status[1][0][0]
		body = ('manipal bank account XXX' + str(accounts[0]).zfill(3)[-3:] 
			+ ' was debited for Rs ' + str(amount) + ' on ' + date + '.' 
			+ ' ' + name + ' credited.'
		)


	elif type == 'tr':
		status = executeQuery('''
			SELECT phone_num
			FROM CUSTOMERS
			WHERE account_num={}
		'''.format(accounts[1])
		)
		phone = '+91' + status[1][0][0]
		body = ('manipal bank account XXX' + str(accounts[1]).zfill(3)[-3:] 
			+ ' was credited for Rs ' + str(amount) + ' on ' + date + '.'
		)
	client.messages.create(
		from_ ='+13343784452',
		body=body,
		to=phone
	)