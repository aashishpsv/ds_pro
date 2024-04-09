import os
import sys

# To use the common.py module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import common
import dbs_view as dbv
import dbs_exec as dbe

import socket
import threading

# Constants
SERVER_IP = '127.0.0.1'
SERVER_PORT = 1069
LISTEN_COUNT = 10

def createServerSocket(serverIP=SERVER_IP, serverPort=SERVER_PORT, listenCount=LISTEN_COUNT):
	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serverSocket.bind((serverIP, serverPort))
	serverSocket.listen(listenCount)
	return serverSocket

def handleClient(client: socket.socket, address: any) -> None:
	status = common.recvEncryptedMessage(client, 0)
	if not status[0] or status[1] == '':
		print('TODO FIX HANDLE CLIENT') 
		quit()
	key = int(status[1])
	dbv.loginMenu(client, key, address)

def main():
	status  = dbe.createDatabase()
	if not status[0]:
		print('Creation of DBS failed due to {}, program will be terminated...'.format(status[1]))
		sys.exit(1)
	
	print('Databases initialized...')
	dbv.loadMenus()
	print('Menu text loaded...')
	serverSocket = createServerSocket()
	print('Server socket is now available...')
	while True:
		clientSocket, address = serverSocket.accept()
		print('Made connection with ', address)
		threading.Thread(target=handleClient, args=(clientSocket, address)).start()

if __name__ == '__main__':
	main()