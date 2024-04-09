import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import common
import dbs_exec as dbe

import datetime
import socket
import tabulate

# A global dictionary that contains various menus
MENU_LIST = {}

def menuReader(menuName):
	with open(menuName, 'r') as file:
		content = file.read()
	return content

def loadMenus():
	menus = ['adminMenu', 'loginMenu', 'customerMenu']
	for menu in menus:
		MENU_LIST[menu] = menuReader('menu/' + menu + '.txt')

def checkConnectionError(status: list, clientSocket: socket.socket, details: tuple) -> None:
	if not status[0]:
		clientSocket.close()
		ip, port = details
		print('Due to {}, connection with {}:{} was closed'.format(status[1], ip, port))
		sys.exit(1)

def safeSend(clientSocket: socket.socket, message: str, key: int, details: tuple) -> None:
	status = common.sendEncryptedMessage(clientSocket, message, key)
	checkConnectionError(status, clientSocket, details)

def safeReceive(clientSocket: socket.socket, key: int, details: tuple) -> str:
	status = common.recvEncryptedMessage(clientSocket, key)
	checkConnectionError(status, clientSocket, details)
	return status[1]

def invalidOption(clientSocket: socket.socket, key:int, details:tuple):
	prompt = '\nInvalid option was entered. Press any key to continue...'
	safeSend(clientSocket, prompt, key, details)
	_ = safeReceive(clientSocket, key, details)
	
def loginMenu(clientSocket:socket.socket, key: int, details) -> None:
	while True:
		safeSend(clientSocket, MENU_LIST['loginMenu'], key, details)
		
		data = safeReceive(clientSocket, key, details)
		
		choice = data.casefold()
		if choice == 'a':
			prompt = '\nEnter your account number: '
			safeSend(clientSocket, prompt, key, details)
			data = safeReceive(clientSocket, key, details)

			try:
				accountNumber = int(data)
				prompt = '@PASS\nEnter your password: '
				safeSend(clientSocket, prompt, key, details)
				password = safeReceive(clientSocket, key, details)

				if dbe.isUserAdmin(accountNumber, password):
					adminMenu(clientSocket, key, details)
				else:
					if dbe.authenticate(accountNumber, password):
						customerMenu(accountNumber, clientSocket, key, details)
					else:
						prompt = '\nInvalid credentials. Press any key to continue...'
						safeSend(clientSocket, prompt, key, details)
						_ = safeReceive(clientSocket, key, details)

			except ValueError as ve:
				prompt = '\nAccount number must be an integer. Press any key to continue...'
				safeSend(clientSocket, prompt, key, details)
				_ = safeReceive(clientSocket, key, details)
		elif choice == 'b':
			prompt = '@EXIT\n\nThank you for using Manipal Bank\n'
			safeSend(clientSocket, prompt, key, details)
			ip, port = details
			clientSocket.close()
			print('{}:{} has exited'.format(ip, port))
			break
		else:
			invalidOption(clientSocket, key, details)

def addAccount(clientSocket: socket.socket, key:int, details: tuple) -> None:
	prompt = '@CLEAR\nEnter Aadhar number: '
	safeSend(clientSocket, prompt, key, details)
	aadhar = safeReceive(clientSocket, key, details)
	exists = dbe.doesValueExist('aadhar_num', aadhar)
	if exists:
		prompt = '\nError: The Aadhar number is already in use. Press any key to continue...'
		safeSend(clientSocket, prompt, key, details)
		_ = safeReceive(clientSocket, key, details)
		return

	prompt = '\nEnter phone number: '
	safeSend(clientSocket, prompt, key, details)
	phone = safeReceive(clientSocket, key, details)
	exists = dbe.doesValueExist('phone_num', phone)
	if exists:
		prompt = '\nError: The Phone number is already in use. Press any key to continue...'
		safeSend(clientSocket, prompt, key, details)
		_ = safeReceive(clientSocket, key, details)
		return
	
	prompt = '\nEnter first name: '
	safeSend(clientSocket, prompt, key, details)
	firstName = safeReceive(clientSocket, key, details)

	prompt = '\nEnter last name: '
	safeSend(clientSocket, prompt, key, details)
	lastName = safeReceive(clientSocket, key, details)

	prompt = '\nActivate SMS service for user? (Y or N): '
	safeSend(clientSocket, prompt, key, details)
	data = safeReceive(clientSocket, key, details).casefold()
	sms = 'Y' if (data=='y' or data=='yes') else 'N'

	prompt = '\nEnter password: '
	safeSend(clientSocket, prompt, key, details)
	password = safeReceive(clientSocket, key, details).casefold()

	passhash = dbe.sha256Hash(password)

	status = dbe.executeQuery('''
		INSERT INTO CUSTOMERS(
			first_name, last_name, aadhar_num, phone_num, balance, sms
		) VALUES(
			'{}', '{}', '{}', '{}', {}, '{}'
		)
	'''.format(firstName, lastName, aadhar, phone, 100000, sms)
	)

	inserted = status[0]
	if inserted:
		status = dbe.executeQuery('''
			SELECT account_num
			FROM CUSTOMERS
			WHERE aadhar_num='{}'
		'''.format(aadhar)
		)

		data = status[1]
		accountNumber = data[0][0]

		status = dbe.executeQuery('''
			INSERT INTO AUTH(
				account_num, password
			) VALUES(
				'{}', '{}'
			)
		'''.format(accountNumber, passhash)
		)

		prompt = '\nAccount added successfully. Press any key to continue...'
		safeSend(clientSocket, prompt, key, details)
	else:
		prompt = '\nAccount could not be added. Press any key to continue...'
		safeSend(clientSocket, prompt, key, details)

	_ = safeReceive(clientSocket, key, details)

def deleteAccount(clientSocket: socket.socket, key:int, details: tuple) -> None:
	prompt = '\nEnter account number: '
	safeSend(clientSocket, prompt, key, details)
	data = safeReceive(clientSocket, key, details)
	try:
		accountNumber = int(data)
		exists = dbe.doesValueExist('account_num', accountNumber)
		if exists:
			prompt = '@PASS\n\nEnter admin password to proceed: '
			safeSend(clientSocket, prompt, key, details)
			password = safeReceive(clientSocket, key, details)
			admin = dbe.isUserAdmin(0, password)
			if admin:
				dbe.executeQuery('''
					DELETE FROM CUSTOMERS
					WHERE account_num={}
				'''.format(accountNumber)
				)
				dbe.executeQuery('''
					DELETE FROM AUTH
					WHERE account_num={}
				'''.format(accountNumber)
				)
				prompt = '\nAccount {} was deleted. Press any key...'.format(accountNumber)
				safeSend(clientSocket, prompt, key, details)
			else:
				prompt = '\nWrong password. Deletion will not happen. Press any key to continue...'
				safeSend(clientSocket, prompt, key, details)
		else:
			prompt = '\nAccount with that account number does not exist. Press any key to continue...'
			safeSend(clientSocket, prompt, key, details)
	except ValueError:
		prompt = '\nAccount number must be an integer. Press any key to continue...'
		safeSend(clientSocket, prompt, key, details)
	_ = safeReceive(clientSocket, key, details)

def displayTable(tableName: str, clientSocket: socket.socket, 
		key:int, details: tuple, condition='') -> None:
	query = 'SELECT * FROM {}'.format(tableName)
	if condition != '':
		query += ' WHERE ' + condition
	status = dbe.executeQuery(query)
	if status[0]:
		headers = [desc[0] for desc in status[2]]
		table = tabulate.tabulate(status[1], headers=headers,tablefmt='presto')
		prompt = '@CLEAR\n{} table\n\n{}\n\nPress any key to continue...'.format(
			tableName.upper(), table
		)
		safeSend(clientSocket, prompt, key, details)
	else:
		prompt = '\nUnable to show {} table. Press any key to continue...'.format(
			tableName.upper()
		)
	_ = safeReceive(clientSocket, key, details)

def adminMenu(clientSocket:socket.socket, key: int, details) -> None:
	while True:
		safeSend(clientSocket, MENU_LIST['adminMenu'], key, details)
		data = safeReceive(clientSocket, key, details)
		choice = data.casefold()
		if choice == 'a':
			addAccount(clientSocket, key, details)
		elif choice == 'b':
			deleteAccount(clientSocket, key, details)
		elif choice == 'c':
			displayTable('CUSTOMERS', clientSocket, key, details)
		elif choice == 'd':
			displayTable('TRANSACTIONS', clientSocket, key, details)
		elif choice == 'e':
			break
		else:
			invalidOption(clientSocket, key, details)

def customerMenu(accountNumber: int, clientSocket:socket.socket, key: int, details) -> None:
	while True:
		status = dbe.executeQuery('''
			SELECT balance
			FROM CUSTOMERS
			WHERE account_num={}
		'''.format(accountNumber)
		)

		data = status[1]
		balance = data[0][0]
		prompt = MENU_LIST['customerMenu'].format(account_num=accountNumber, balance=balance)
		safeSend(clientSocket, prompt, key, details)
		data = safeReceive(clientSocket, key, details)
		choice = data.casefold()
		if choice == 'a':
			pass
		elif choice == 'b':
			depositMenu(accountNumber, clientSocket, key, details)
		elif choice == 'c':
			withdrawMenu(accountNumber, clientSocket, key, details)
		elif choice == 'd':
			transferMenu(accountNumber, clientSocket, key, details)
		elif choice == 'e':
			condition = 'from_account={} OR to_account={}'.format(accountNumber, accountNumber)
			displayTable('TRANSACTIONS', clientSocket, key, details, condition)
		elif choice == 'f':
			break
		else:
			invalidOption(clientSocket, key, details)

def depositMenu(accountNumber: int, clientSocket: socket.socket, key: int, details: tuple) -> None:
	prompt = '\nEnter amount to deposit: '
	safeSend(clientSocket, prompt, key, details)
	data = safeReceive(clientSocket, key, details)
	try:
		amount = float(data)
		status = dbe.executeQuery('''
			SELECT balance
			FROM CUSTOMERS
			WHERE account_num={}
		'''.format(accountNumber)
		)

		data = status[1]
		balance = data[0][0]
		status = dbe.executeQuery('''
			UPDATE CUSTOMERS
			SET balance = {}
			WHERE account_num={}
		'''.format(balance+amount, accountNumber)
		)

		date = str(datetime.datetime.now())[:19]
		status = dbe.executeQuery('''
			INSERT INTO TRANSACTIONS(
				from_account, to_account, amount, type, date
			) VALUES (
				{}, {}, {}, '{}', '{}'
			)
		'''.format(accountNumber, accountNumber, amount, 'DEPOSIT', date)
		)

		data = dbe.executeQuery('''
			SELECT sms
			FROM CUSTOMERS
			WHERE account_num={}
		'''.format(accountNumber)
		)
		sms = data[1][0][0]
		if sms == 'Y':
			dbe.sendSMS([accountNumber], amount, 'd', date)

		#PLAYSOUND

		prompt = '\nDeposit was successful. Press any key to continue...'
		safeSend(clientSocket, prompt, key, details)

	except ValueError:
		prompt = '\nEnter a valid number. Press any key to continue...'
		safeSend(clientSocket, prompt, key, details)
	
	_ = safeReceive(clientSocket, key, details)

def withdrawMenu(accountNumber: int, clientSocket: socket.socket, key: int, details: tuple) -> None:
	prompt = '\nEnter amount to withdraw: '
	safeSend(clientSocket, prompt, key, details)
	data = safeReceive(clientSocket, key, details)
	try:
		amount = float(data)
		status = dbe.executeQuery('''
			SELECT balance
			FROM CUSTOMERS
			WHERE account_num={}
		'''.format(accountNumber)
		)

		data = status[1]
		balance = data[0][0]

		if balance >= amount:
			status = dbe.executeQuery('''
				UPDATE CUSTOMERS
				SET balance = {}
				WHERE account_num={}
			'''.format(balance-amount, accountNumber)
			)
			date = str(datetime.datetime.now())[:19]
			status = dbe.executeQuery('''
				INSERT INTO TRANSACTIONS(
					from_account, to_account, amount, type, date
				) VALUES (
				{}, {}, {}, '{}', '{}'
				)
			'''.format(accountNumber, accountNumber, amount, 'WITHDRAWAL', date)
			)

			data = dbe.executeQuery('''
				SELECT sms
				FROM CUSTOMERS
				WHERE account_num={}
			'''.format(accountNumber)
			)
			sms = data[1][0][0]
			if sms == 'Y':
				dbe.sendSMS([accountNumber], amount, 'w', date)

			#PLAYSOUND

			prompt = '\nWithdrawal was successful. Press any key to continue...'
			safeSend(clientSocket, prompt, key, details)
		else:
			prompt = '\nInsufficient balance to perform withdrawal. Press any key to continue...'
			safeSend(clientSocket, prompt, key, details)
	except ValueError:
		prompt = '\nEnter a valid number. Press any key to continue...'
		safeSend(clientSocket, prompt, key, details)

	_ = safeReceive(clientSocket, key, details)

def transferMenu(accountNumber: int, clientSocket: socket.socket, key: int, details: tuple) -> None:
	prompt = '\nEnter account number of receiver: '
	safeSend(clientSocket, prompt, key, details)
	data = safeReceive(clientSocket, key, details)
	try:
		theirAccount = int(data)
		exists = dbe.doesValueExist('account_num', theirAccount)
		if exists:
			prompt = '\nEnter amount to transfer: '
			safeSend(clientSocket, prompt, key, details)
			data = safeReceive(clientSocket, key, details)
			try:
				amount = float(data)
				status = dbe.executeQuery('''
					SELECT balance
					FROM CUSTOMERS
					WHERE account_num={}
				'''.format(accountNumber)
				)
				data = status[1]
				yourBalance = data[0][0]

				status = dbe.executeQuery('''
					SELECT balance
					FROM CUSTOMERS
					WHERE account_num={}
				'''.format(theirAccount)
				)
				data = status[1]
				theirBalance = data[0][0]

				if yourBalance >= amount:
					status = dbe.executeQuery('''
						UPDATE CUSTOMERS
						SET balance = {}
						WHERE account_num={}
					'''.format(yourBalance-amount, accountNumber)
					)
					status = dbe.executeQuery('''
						UPDATE CUSTOMERS
						SET balance = {}
						WHERE account_num={}
					'''.format(theirBalance+amount, theirAccount)
					)
					date = str(datetime.datetime.now())[:19]
				
					status = dbe.executeQuery('''
						INSERT INTO TRANSACTIONS(
							from_account, to_account, amount, type, date
						) VALUES (
							{}, {}, {}, '{}', '{}'
						)
					'''.format(accountNumber, theirAccount, amount, 'TRANSFER', date)
					)

					data = dbe.executeQuery('''
						SELECT sms
						FROM CUSTOMERS
						WHERE account_num={}
					'''.format(accountNumber)
					)
					sms = data[1][0][0]
					if sms == 'Y':
						dbe.sendSMS([accountNumber, theirAccount], amount, 'ts', date)

					data = dbe.executeQuery('''
						SELECT sms
						FROM CUSTOMERS
						WHERE account_num={}
					'''.format(theirAccount)
					)
					sms = data[1][0][0]
					if sms == 'Y':
						dbe.sendSMS([accountNumber, theirAccount], amount, 'tr', date)

					#PLAYSOUND
					
					prompt = '\nTransfer was successful. Press any key to continue...'
					safeSend(clientSocket, prompt, key, details)
				else:
					prompt = '\nInsufficient balance to perform withdrawal. Press any key to continue...'
					safeSend(clientSocket, prompt, key, details)
			except ValueError:
				prompt = '\nEnter a valid number. Press any key to continue...'
				safeSend(clientSocket, prompt, key, details)
		else:
			prompt = '\nThe account does not exist. Press any key to continue...'
			safeSend(clientSocket, prompt, key, details)
	except ValueError:
		prompt = '\nAccount number must be an integer. Press any key to continue...'
		safeSend(clientSocket, prompt, key, details)
	
	_ = safeReceive(clientSocket, key, details)