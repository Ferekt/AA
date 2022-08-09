import os

class TransferHandler():
	def __init__(self,ctrl):
		self.user= "user"
		self.password="kek"
		self.ctrl=ctrl
	
	def transfer(self,client):

		algorithmDir=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),"algorithms",str(self.ctrl.algorithm_name),"resources"))
		host=str(client.address[0]) + " 21"
		user="user"
		password="password"

		os.system('''
cd {_algorithmDir}
ftp -inv {_host} <<EOF
user {_user} {_password}
cd algorithms
mkdir {_algorithm}
cd {_algorithm}
mkdir resources
cd resources
prompt	
{_ftpOrders}
bye
'''.format(
			_algorithmDir=algorithmDir,
			_host=host,
			_user=self.user,
			_password=self.password,
			_algorithm=self.ctrl.algorithm_name,
			_ftpOrders=self.navigate(algorithmDir))
		)


	def navigate(self,path):
		output=""
		for obj in os.scandir(path):
			if obj.is_file():
				output+=("put "+ str(obj.name)+"\n") 
		for obj in os.scandir(path):
			if obj.is_dir():
				output+=("mkdir "+ str(obj.name)+"\n")
				output+=("cd "+ str(obj.name)+"\n")
				output+=("lcd "+str(obj.name)+"\n")
				output+=self.navigate(path+"/"+str(obj.name))
				output+=("lcd .. \n")
				output+=("cd .. \n")
		return output

		
		"""f=open("shell.sh","w")
		f.write("#!/bin/bash\n"
				+"cd "+ algorithmDir+"\n"
				+"HOST=\""+str(client.address[0])+" 21\"\n"
				+"USER=\"user\"\n"
				+"PASSWORD=\"kek\"\n"
				+"ftp -inv $HOST <<EOF\n"
				+"user $USER $PASSWORD\n"
				+"cd algorithms\n"
				+"mkdir "+str(self.algorithm_name)+"\n"
				+"cd "+str(self.algorithm_name)+"\n"
				+"mkdir resources\n"
				+"cd resources\n"
				+"prompt\n"+
				self.shell_dir(algorithmDir))
		f.close()"""