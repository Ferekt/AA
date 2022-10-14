import os
import ftplib
from tqdm import tqdm

class TransferHandler():
	def __init__(self,ctrl):
		self.user= "user"
		self.password="kek"
		self.ctrl=ctrl
	
	def transfer(self,client):

		algorithmDir=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),"algorithms",str(self.ctrl.algorithm_name),"resources"))
		host=str(client.address[0])
		user="user"
		password="password"

		ftps = ftplib.FTP(host)
		ftps.login(user=self.user,passwd=self.password)
		if not 'algorithms' in ftps.nlst():
			print("MKD",'algorithms')
			ftps.mkd('algorithms')
		ftps.cwd('algorithms')
		if not self.ctrl.algorithm_name in ftps.nlst():
			print("MKD",self.ctrl.algorithm_name)
			ftps.mkd(self.ctrl.algorithm_name)
			print("CWD",self.ctrl.algorithm_name)
			ftps.cwd(self.ctrl.algorithm_name)
			if not "resources" in ftps.nlst():
				print("MKD", "resources")
				ftps.mkd("resources")
			print("CWD","resources")
			ftps.cwd("resources")
			self.navigate(algorithmDir,ftps)
		else:
			pass

	def navigate(self,path,ftps):
		for name in os.listdir(path):
			localpath= os.path.join(path,name)
			if os.path.isfile(localpath)and not name in ftps.nlst():
				self.upload(name,localpath,ftps)
			elif os.path.isdir(localpath):
				if not name in ftps.nlst():
					print("MKD", name)
					try:
						ftps.mkd(name)

					except ftplib.error_perm as e:
						if not e.args[0].startswith('550'):
							raise
				print("CWD", name)
				ftps.cwd(name)
				self.navigate(localpath,ftps)
				print("CWD","..")
				ftps.cwd("..")
	
	def upload(self, name, path,ftps):
		print("STOR", name , path)
		size=os.path.getsize(path)
		with tqdm(mininterval = 0 , unit = 'b', unit_scale = True, leave = False, miniters = 1, desc = 'Uploading......', total = size) as tqdm_instance:
				ftps.storbinary('STOR '+name,open(path,'rb'),int(size/5), callback = lambda sent: tqdm_instance.update(len(sent)))
