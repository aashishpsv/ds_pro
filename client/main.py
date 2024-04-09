import os
import sys

# To use the common.py module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import common

import getpass
import random
import platform
import socket
import time

SERVER_IP = '127.0.0.1'
SERVER_PORT = 1069

def clearScreen():
	os_name = platform.system()
	if os_name == 'Windows':
		os.system('cls')
	else:
		os.system('clear')

def checkSendError(status:list, clientSocket: socket.socket) -> None:
	if not status[0]:
		clientSocket.close()
		print('There was some error in sending the message to the server')
		print('Please try again later...')
		sys.exit(1)
	
def checkReceiveError(status: list, clientSocket: socket.socket) -> None:
	if not status[0]:
		clientSocket.close()
		print('There was some error in receiving data from the server')
		print('Please try again later...')
		sys.exit(1)

def displayText(request: str, start: int, end='') -> None:
	print(request[start:], end=end)
	sys.stdout.flush()

def main():
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		print('Trying to connect to the server...')
		clientSocket.connect((SERVER_IP, SERVER_PORT))
		print('Connection was successful!')
		time.sleep(3)
		key = random.randint(0, 255)
		status = common.sendEncryptedMessage(clientSocket, str(key), 0)
		checkSendError(status, clientSocket)

		while True:
			reply = None
			status = common.recvEncryptedMessage(clientSocket, key)
			checkReceiveError(status, clientSocket)
			
			response = status[1]
			if response.startswith('@EXIT'):
				displayText(response, 6, '\n')
				clientSocket.close()
				break
			
			if response.startswith('@PASS'):
				displayText(response, 6)
				reply = getpass.getpass('')
			else:
				if response.startswith('@CLEAR'):
					clearScreen()
					displayText(response, 7)
				else:
					displayText(response, 0)
				reply = input('')
			
			if reply == '': reply = ' '
			
			status = common.sendEncryptedMessage(clientSocket, reply, key)
			checkSendError(status, clientSocket)

	except ConnectionRefusedError:
		print('\nCould not connect to the banking server. Please try again later')

if __name__ == '__main__':
	main()
