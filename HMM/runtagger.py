# python3.5 runtagger.py <test_file_absolute_path> <model_file_absolute_path> <output_file_absolute_path>

import os
import math
import sys
import datetime
import numpy as np


def tag_sentence(test_file, model_file, out_file):
    # write your code here. You can add functions as well.
    transition_probs = {} # transit from prev_tag to tag; key_1=prev_tag, key_2=tag; sum(prev_tag) = 1
    emission_probs = {} # word given POS tag: key_1=word, key_2=tag
    q0 = {}
    qF = {}

    output = open(out_file, 'w+')
    model = open(model_file, 'r')
    line_type = 0 # 0-initProb, 1-transmissionProb, 2-emissionProb
    for line in model.readlines():
        line = line[:-1]
        if str.isdigit(line):
            line_type = int(line)
        else:
            if line_type == 0:
                tag, prob = line.split('=')
                q0[tag] = float(prob)

            elif line_type == 1:
                tags, prob = line.split('=')
                tag, prev_tag = tags.split('|')
                if prev_tag not in transition_probs:
                    transition_probs[prev_tag] = {}
                transition_probs[prev_tag][tag] = float(prob)

            elif line_type == 2:
                if line.startswith('='):
                    word_tag, prob = line[1:].split('=')
                    word_tag = '='+word_tag
                else:
                    word_tag, prob = line.split('=')
                word, tag = word_tag.split('|')
                if tag not in emission_probs:
                    emission_probs[tag] = {}
                emission_probs[tag][word] = float(prob)

            else:
                tag, prob = line.split('=')
                qF[tag] = float(prob)


    test_data = open(test_file, 'r')
    tags = list(q0.keys())
    q0_probs = list(map(lambda x:q0[x], tags))
    
    for line_no, line in enumerate(test_data.readlines()):
        line = line.split()
        v_matrix = []
        tracer = []

        for i, word in enumerate(line):
            v_matrix.append([0]*len(tags))
            tracer.append(['']*len(tags))

            for tag_index, tag in enumerate(tags):
                if i == 0:
                    prev_values = q0_probs
                else:
                    prev_values = v_matrix[i-1]

                if word not in emission_probs[tag]:
                    emission_prob = emission_probs[tag]['<UNK>']
                else:
                    emission_prob = emission_probs[tag][word]

                max_prob, max_index = 0, 0
                for prev_tag_index, prev_tag in enumerate(tags):
                    if i == 0:
                        transition_prob = 1
                    else:
                        transition_prob = transition_probs[prev_tag][tag]
                    prob = prev_values[prev_tag_index] * transition_prob * emission_prob
                    if prob > max_prob:
                        max_prob = prob
                        max_index = prev_tag_index
                v_matrix[i][tag_index] = max_prob
                tracer[i][tag_index] = max_index

        max_prob, trace_index = 0, 0
        for j, prob in enumerate(v_matrix[-1]):
            if prob * qF[tags[j]] > max_prob:
                max_prob = prob * qF[tags[j]]
                trace_index = j

        # for r in range(len(v_matrix)):
        #   print(line[r])
        #   for c in range(len(v_matrix[r])):
        #       print(tags[c], v_matrix[r][c], tracer[r][c])
        #   print()

        tags_index = []
        for k in reversed(range(len(v_matrix))):
            line[k] += '/'+tags[trace_index]
            tags_index.append(trace_index)
            trace_index = tracer[k][trace_index]

        line = ' '.join(line) +'\n'
        output.write(line)
    print('Finished...')

if __name__ == "__main__":
    # make no changes here
    test_file = sys.argv[1]
    model_file = sys.argv[2]
    out_file = sys.argv[3]
    start_time = datetime.datetime.now()
    tag_sentence(test_file, model_file, out_file)
    end_time = datetime.datetime.now()
    print('Time:', end_time - start_time)
