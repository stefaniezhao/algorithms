#! /usr/bin/python

__author__ = "Stefanie Zhao <zhaochenting@gmail.com>"
__date__ = "$Mar 11, 2013"

from collections import defaultdict
from count_freqs import *
import re

def calculate_counts(input):
	counts = defaultdict(int)
	iterator = simple_conll_corpus_iterator(input)
	for word, tag in iterator:
		counts[word] += 1
	return counts

def get_rare_class(word):
	if re.match('.*\d+.*', word):
		return "_NUMBER_"
	elif re.match('^[A-Z]+\Z', word):
		return "_CAPITAL_"
	elif re.match('.*[A-Z]\Z', word):
		return "_LAST_CAPITAL_"
	else:
		return "_RARE_"
		

def replace_rare_word(input, refined_corpusfile):
	counts = calculate_counts(input)
	input.seek(0,0)
	l = input.readline()
	while l:
		line = l.strip()
		if line:  # Nonempty line
			fields = line.split(" ")
			ne_tag = fields[-1]
			word = " ".join(fields[:-1])
			count = counts[word]
			if counts[word] < 5:
				clazz = get_rare_class(word)
#				print word, clazz
				word = clazz
			refined_corpusfile.write("%s %s\n" % (word, ne_tag))
		else:  # Empty line
			refined_corpusfile.write('\n')
		l = input.readline()


def find_max_tag(counter, word, tags):
	max_tag = ""
	max_count = 0
	for tag in tags:
		count = counter.predict_emssiion_counts[(word, tag)]
		if count > max_count:
			max_tag = tag
			max_count = count
	return max_tag


def is_rare_word(counter, word, tags):
	for tag in tags:
		count = counter.predict_emssiion_counts[(word, tag)]
		if count > 0:
			return False
	return True

def calculate_proability(input, counter, counts, output):
	tags = set()
	for ngram in counter.ngram_counts[0]:
		ngramstr = " ".join(ngram)
		tags.add(ngramstr)
	
	rare_tag = find_max_tag(counter, "_RARE_", tags)
	gene_tag = find_max_tag(counter, "genes", tags)
	
	l = input.readline()
	while l:
		word = l.strip()
		if word:  # Nonempty line
			max_tag = find_max_tag(counter, word, tags)
			if max_tag:
				output.write("%s %s\n" % (word, max_tag))
			else:
				output.write("%s %s\n" % (word, rare_tag))
		else:
			output.write("\n")
		l = input.readline()

def get_possible_tags(index, tags, begin):
	if index > 0:
		return tags
	else:
		return begin

def viterbi(counter, input, output):
	sents = sentence_iterator(simple_conll_corpus_iterator(input))
	tags = set()
	for ngram in counter.ngram_counts[0]:
		ngramstr = " ".join(ngram)
		tags.add(ngramstr)
		
	begin = set()
	begin.add("*")
		
	for sent in sents:
		# print sent
		pi = defaultdict(float)
		pi_tag = defaultdict(str)
		pi[(0, "*", "*")] = 1
		k = 0
		n = len(sent)
		for tag, word in sent:
			k += 1
			# print word
			if is_rare_word(counter, word, tags):
				word = get_rare_class(word)
				#word = "_RARE_"
			for u in get_possible_tags(k - 1, tags, begin):
				for v in get_possible_tags(k, tags, begin):
					e_prob = counter.predict_emssiion_counts[(word, v)]
					# print word, v, e_prob
					if e_prob:
						max_pi = -1;
						max_tag = ""
						for w in get_possible_tags(k - 2, tags, begin):
							if k % 80 == 0: #fix to avoid out of float
								pi_w = pi[(k - 1, w, u)] * counter.trigram_prob[(w, u, v)] * e_prob * 1.0e100
							else:
								pi_w = pi[(k - 1, w, u)] * counter.trigram_prob[(w, u, v)] * e_prob
							#print word, pi_w, w, u, v
							if pi_w > max_pi:
								max_tag = w
								max_pi = pi_w
						pi[(k, u, v)] = max_pi
						#if max_tag == "":
							#print "maxtag == null", k, u, v
						pi_tag[(k, u, v)] = max_tag
						#print k, word, max_tag, u, v, max_pi
					else:
						pi[(k, u, v)] = 0
						pi_tag[(k, u, v)] = "-"
			
		
			
		max_tags = []
			
		max_pi = 0
		max_u = ""
		max_v = ""
		for u in get_possible_tags(n - 1, tags, begin):
			for v in get_possible_tags(n, tags, begin):
				pi_u_v = pi[(n, u, v)] * counter.trigram_prob[(u, v, "STOP")]
				#print n, u, v, pi[(n, u, v)], counter.trigram_prob[(u, v, "STOP")], pi_u_v
				if pi_u_v > max_pi:
					max_pi = pi_u_v
					max_u = u
					max_v = v
			
		
		max_tags.append(max_v)
		max_tags.append(max_u)
			
		
		for k in range(3, n + 1)[::-1]:
			l = len(max_tags)
			max_y = pi_tag[(k, max_tags[l - 1], max_tags[l - 2])]
			# print max_y, pi[(k,max_tags[l-1],max_tags[l-2])]
			max_tags.append(max_y)
			
		#print max_tags
		for k in range(0, n)[::-1]:
			tag = max_tags[k]
			word = sent[n - k - 1][1]
			output.write("%s %s\n" % (word, tag))
			
		output.write("\n")
			
							
			
		
def testClazz():
	print get_rare_class("8777")
	print get_rare_class("hshusu7")
	print get_rare_class("hsyyyshy")
	print get_rare_class("UUUUS")
	print get_rare_class("YSSsY")
	print get_rare_class("HUSU7Z")
	print get_rare_class("shuZ")


def prepare_train_data():
	input = file(sys.argv[1],"r")
	replace_rare_word(input, sys.stdout)
	
def test_viterbi():
	counter = Hmm(3)
	input = file(sys.argv[1],"r")
	counter.read_counts(input)
	
	test_file = file(sys.argv[2],"r")
	viterbi(counter, test_file, sys.stdout)

if __name__ == "__main__":
	test_viterbi()
