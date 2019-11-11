# python3.5 buildtagger.py <train_file_absolute_path> <model_file_absolute_path>

import os
import math
import sys
import datetime
import numpy as np

def train_model(train_file, model_file):
	# write your code here. You can add functions as well.
	emission_counts = {} # word given POS tag: key_1=tag, key_2=word; sum(tag)=1
	transition_counts = {} # transit from prev_tag to tag; key_1=prev_tag, key_2=tag; sum(prev_tag) = 1
	tags_preceding_tag = {}
	word_tags = {}
	no_of_different_bigrams = 0
	no_of_different_word_tags = 0
	tags_count = {}
	q0 = {}
	qF = {}

	total_count = 0

	train_data = open(train_file, 'r')
	for line in train_data.readlines():
		line_split = line[:-1].split()
		prev_tag = 'q0'
		total_count += 1

		for word_with_tag in line_split:
			word_split = word_with_tag.split('/')
			words, tag = word_split[:-1], word_split[-1]
			for word in words:
				if str.isdigit(word):
					frac = True
				else:
					frac = False
			if frac: words = '/'.join(words)
			
			for word in words:

				if tag not in tags_count:
					tags_count[tag] = 0				
				tags_count[tag] += 1				

				if tag not in emission_counts:
					emission_counts[tag] = {}
				if word not in emission_counts[tag]:
					emission_counts[tag][word] = 0
				emission_counts[tag][word] += 1
				
				if word not in word_tags:
					word_tags[word] = {}
				if tag not in word_tags[word]:
					word_tags[word][tag] = 1
					no_of_different_word_tags += 1

				if tag not in tags_preceding_tag:
					tags_preceding_tag[tag] = {}

				if tag not in transition_counts:
					transition_counts[tag] = {}

				if prev_tag not in tags_preceding_tag[tag]:
					tags_preceding_tag[tag][prev_tag] = 1

				if prev_tag == 'q0':
					if tag not in q0:
						q0[tag] = 0
						no_of_different_bigrams += 1
					q0[tag] += 1
				else:
					if tag not in transition_counts[prev_tag]:
						transition_counts[prev_tag][tag] = 0
						no_of_different_bigrams += 1
					transition_counts[prev_tag][tag] += 1

			prev_tag = tag

		if tag not in qF:
			qF[tag] = 0
		if tag not in transition_counts:
			transition_counts[tag] = {}
		if 'qF' not in transition_counts[tag]:
			transition_counts[tag]['qF'] = 0
		transition_counts[tag]['qF'] += 1
		qF[tag] += 1

	discount = 0.75

	model = open(model_file, 'w+')
	model.write('0\n')
	for tag in tags_count:
		max_term = 0
		if tag in q0:
			max_term = (q0[tag]-discount)/total_count
		lambda_term = (discount*len(q0)/total_count)
		cont_term = len(tags_preceding_tag[tag])/no_of_different_bigrams
		prob = max_term+lambda_term*cont_term
		temp = tag + '=' + str(prob) + '\n'
		model.write(temp)

	model.write('1\n')
	for prev_tag in transition_counts:
		for tag in tags_count:
			max_term = 0
			if tag in transition_counts[prev_tag]:
				max_term = (transition_counts[prev_tag][tag] - discount)/tags_count[prev_tag]
			lambda_term = (discount*len(transition_counts[prev_tag]))/tags_count[prev_tag]
			cont_term = len(tags_preceding_tag[tag])/no_of_different_bigrams
			prob = max_term+lambda_term*cont_term
			temp = tag + '|' + prev_tag + '=' + str(prob) + '\n'
			model.write(temp)


	model.write('2\n')
	for tag in emission_counts:
		for word in emission_counts[tag]:
			max_term = (emission_counts[tag][word]-discount)/(tags_count[tag])
			lambda_term = (discount*len(emission_counts[tag]))/tags_count[tag]
			cont_term = len(word_tags[word])/no_of_different_word_tags
			prob = max_term + lambda_term*cont_term
			if word == 'qF': prob = 1
			temp = word + '|' + tag + '=' + str(prob) + '\n'
			model.write(temp)
		lambda_term = (discount*len(emission_counts[tag]))/tags_count[tag]
		cont_term = 1/no_of_different_word_tags
		prob = lambda_term*cont_term
		if tag == 'qF': prob = 0
		temp = '<UNK>|' + tag + '=' + str(prob) + '\n'
		model.write(temp)

	model.write('3\n')
	for tag in tags_count:
		max_term = 0
		if tag in qF:
			max_term = (qF[tag]-discount)/tags_count[tag]
		lambda_term = (discount*len(transition_counts[tag])/tags_count[tag])
		cont_term = len(qF)/no_of_different_bigrams
		prob = max_term+lambda_term*cont_term
		temp = tag + '=' + str(prob) + '\n'
		model.write(temp)


	model.close()

	print('Finished...')

if __name__ == "__main__":
	# make no changes here
	train_file = sys.argv[1]
	model_file = sys.argv[2]
	start_time = datetime.datetime.now()
	train_model(train_file, model_file)
	end_time = datetime.datetime.now()
	print('Time:', end_time - start_time)
