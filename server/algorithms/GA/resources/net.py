import torch
import torch.nn as nn
import torch.nn.functional as F


torch.autograd.set_grad_enabled(False)

class Net(nn.Module):
	def __init__(self, layers):
		super(Net, self).__init__()
		
		self.model = nn.Sequential()
		for iterator in zip(range(len(layers)-1),layers[:-1],layers[1:]):
			self.model.add_module("Linear{}".format(iterator[0]), nn.Linear(*iterator[1:]))
			if iterator[0] != len(layers)-2:
				self.model.add_module("ReLU{}".format(iterator[0]), nn.ReLU())
			else:
				self.model.add_module("Sigmoid", nn.Sigmoid())

		self.score = 0

	def forward(self, x):
		return self.model(x).numpy()

	#destructor!!!!!4!!!