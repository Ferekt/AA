import pickle
import os
import shutil



def deleteFolder(folder):
	shutil.rmtree(folder)


def createFolder(folder):
	try:
		if not os.path.exists(folder):
			os.makedirs(folder)
	except OSError:
		print ('Can not create folder. ' +  folder)
		return False
	return True


def save(data, directory, file):
	try:
		with open(directory + file + ".gen", "xb") as f:
			pickle.dump(data, f)
			f.close()

	except FileExistsError:
		print("file exists")
	print("Save successful")

def load(directory, file):
	try:
		with open(directory + file + ".gen", "rb") as f:
			data = pickle.load(f)
			f.close()
	except FileNotFoundError:
		print("File doesn't exist")
		return None
	return data

def listDir(path):
	return [str(f) for f in os.listdir(path)]

def printDir(path):
	for f in os.listdir(path):
		print(str(f) + "\t")
