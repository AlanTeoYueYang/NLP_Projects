# python3.5 buildtagger.py <train_file_absolute_path> <model_file_absolute_path>
import os
import math
import sys
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import string
import time
import random


all_chars = string.ascii_letters+string.punctuation+string.digits+' '
start_time = time.time()
class WordCharCNNEmbedding(nn.Module):
	def __init__(self, vocab_size, d_emb, char_size, c_emb, conv_l, char_padding_idx=1, padding_size=2, kernel_size=3):
		super(WordCharCNNEmbedding, self).__init__()
		self.char_embedding = nn.Embedding(char_size, c_emb)
		self._init_char_embedding(char_padding_idx)
		self.conv_embedding = nn.Sequential(nn.Conv1d(in_channels=c_emb, out_channels=conv_l, kernel_size=kernel_size, padding=padding_size), nn.ReLU())
		self.word_embedding = nn.Embedding(vocab_size, d_emb)

	def _init_char_embedding(self, padding_idx):
		nn.init.xavier_normal_(self.char_embedding.weight)
		self.char_embedding.weight.data[padding_idx].uniform_(0, 0)

	def forward(self, X, X_word):
		char_embeddings = []
		for x in X:
			char_embedding = self.char_embedding(x)
			char_embedding = char_embedding.transpose(1,0).unsqueeze(0)
			char_embedding = self.conv_embedding(char_embedding)
			char_embedding = nn.MaxPool1d(char_embedding.size()[2])(char_embedding)
			char_embeddings.append(char_embedding[:,:,0])
		final_char_embedding = torch.cat(char_embeddings, dim=0)
		word_embedding = self.word_embedding(X_word)
		result = torch.cat([final_char_embedding, word_embedding], 1)
		return result

class POSTagger(nn.Module):
	def __init__(self, embedding, n_emb, hidden_dim, ntags, word2idx, num_layers):
		super(POSTagger, self).__init__()
		self.embedding = embedding
		self.tagger_rnn = nn.LSTM(input_size=n_emb, hidden_size=hidden_dim, bidirectional=True)
		self._init_rnn_weights()

		self.hidden2tag = nn.Sequential(nn.Linear(in_features=hidden_dim * 2, out_features=ntags))
		self._init_linear_weights_and_bias()
		self.word2idx = word2idx

	def _init_rnn_weights(self):
		for idx in range(len(self.tagger_rnn.all_weights[0])):
			dim = self.tagger_rnn.all_weights[0][idx].size()
			if len(dim) < 2:
				nn.init.constant_(self.tagger_rnn.all_weights[0][idx], 1)
			elif len(dim) == 2:
				nn.init.xavier_uniform_(self.tagger_rnn.all_weights[0][idx])

	def _init_linear_weights_and_bias(self):
		nn.init.xavier_uniform_(self.hidden2tag[0].weight)
		nn.init.constant_(self.hidden2tag[0].bias, 1)

	def forward(self, sent):
		x_word = sent2tensor(sent, self.word2idx)
		x = []
		for word in sent:
			x.append(word2tensor(word))
		embeds = self.embedding(x, x_word)
		out, _ = self.tagger_rnn(embeds.view(len(sent),1,-1))
		tag_outputs = self.hidden2tag(out.view(len(sent), -1))
		tag_scores = F.log_softmax(tag_outputs, dim=1)
		return tag_scores

def sent2tensor(sent, to_idx):
	idxs = []
	for w in sent:
		w = w.lower()
		if w not in to_idx:
			w = 'UNK'
		idxs.append(to_idx[w])
	return torch.tensor(idxs, dtype=torch.long)

def tags2tensor(tags, to_idx):
	idxs = []
	for tag in tags:
		idxs.append(to_idx[tag])
	return torch.tensor(idxs, dtype=torch.long)

def word2tensor(word):
	tensor = torch.zeros(len(word))
	for i, char in enumerate(word):
		tensor[i] = all_chars.find(char)
	return tensor.long()

def train_model(train_file, model_file):
	train_data = open(train_file, 'r')
	word2idx = {'UNK':0}
	tag2idx = {}
	idx2tag = []

	training_data = []
	for line in train_data.readlines():
		line_split = line[:-1].split()
		sentence, tags = [], []
		for word_with_tag in line_split:
			word_split = word_with_tag.split('/')
			words, tag = word_split[:-1], word_split[-1]
			if len(words) > 1:
				for word in words:
					if str.isdigit(word):
						frac = True
					else:
						frac = False
				if frac: words = '/'.join(words)
			for word in words:
				ori_word = word
				word = word.lower()
				if word.lower() not in word2idx:
					word2idx[word] = len(word2idx)
				if tag not in tag2idx:
					tag2idx[tag] = len(tag2idx)
					idx2tag.append(tag)
				sentence.append(ori_word)
				tags.append(tag)
		training_data.append([sentence, tags])

	d_emb = 256
	c_emb = 64
	conv_l = 128
	hidden_dim = 128
	num_layers = 2

	embedding = WordCharCNNEmbedding(len(word2idx), d_emb, len(all_chars), c_emb, conv_l)
	tagger = POSTagger(embedding, d_emb+conv_l, hidden_dim, len(tag2idx), word2idx, num_layers)
	loss_function = nn.CrossEntropyLoss()
	optimizer = optim.Adam(tagger.parameters(), lr=0.001)
	
	start_time = time.time()
	curr_time = time.time()
	epochs = 100
	batch_size = 100
	for epoch in range(epochs):
		epoch_loss = 0.0
		samples = random.sample(training_data, batch_size)
		for sentence, tags in samples:
			# sentence, tags = training_data[i]
			if time.time() - start_time > 559: break
			tagger.zero_grad()
			targets = tags2tensor(tags, tag2idx)
			tag_scores = tagger(sentence)
			loss = loss_function(tag_scores, targets)
			epoch_loss += loss.item()
			loss.backward()
			optimizer.step()
		print('Time taken: {}s'.format(time.time()-curr_time))
		curr_time = time.time()
		print("Epoch: %d, loss: %1.5f" % (epoch, epoch_loss/len(training_data)))
		if time.time() - start_time > 559: break
	torch.save((d_emb, c_emb, hidden_dim, conv_l, word2idx, tag2idx, idx2tag, num_layers, embedding.state_dict(), tagger.state_dict()), model_file)
	print('Total time taken: {}'.format(time.time()-start_time))
	print('Finished...')
		
if __name__ == "__main__":
	# make no changes here
	train_file = sys.argv[1]
	model_file = sys.argv[2]
	train_model(train_file, model_file)