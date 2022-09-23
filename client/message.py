class Message():
	def __init__(self, command = "", container = None):
		self.__command = command
		self.__container = container
	def command(self):
		return self.__command
	def container(self):
		return self.__container