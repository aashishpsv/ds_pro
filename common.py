import socket

def __encrypt(unencryptedData:str, key:int) -> list[bytes]:
	'''
	Function that accepts a string and a key that returns a byte array 
	of the string encrypted.
	The encryption operation is forming XOR of ASCII value of each letter
	with the key and converting the end result to a bytes array.
	'''
	asc = [ord(char) for char in unencryptedData]
	return bytes([char ^ key for char in asc])

def __decrypt(encryptedData: list[bytes], key: int) -> str:
	'''
	Function that accepts a bytes array containing an encrypted string
	and a key, and decrypts it and returns the original string.
	The decryption assumes that the encryption was using XOR.
	'''
	decryptedData = bytes([byte ^ key for byte in encryptedData])
	return decryptedData.decode("utf-8")

def sendEncryptedMessage(sock: socket.socket, message: str, key: int) -> list:
	'''
	Function that accepts a TCP socket, message and key. The message is 
	encrypted into a bytes array and sent to the other end.
	Return list containing True if successful and list containing False and
	exception object if not.
	'''
	encryptedMessage = __encrypt(message, key)
	try:
		sock.send(encryptedMessage)
		return [True]
	except (OSError) as cre:
		return [False, cre]

def recvEncryptedMessage(sock: socket.socket, key: int)-> list[object]:
	'''
	Function that accepts a TCP socket and key. It waits for an encrypted 
	message to be sent to it. It decrypts the message returns list containing
	True and the message on success and list containing False and exception
	object if some problem occurs.
	'''
	try:
		data = sock.recv(1024)
		message = __decrypt(data, key)
		return [True, message]
	except (OSError) as cre:
		return [False, cre]