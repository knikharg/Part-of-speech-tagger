###################################
# CS B551 Fall 2019, Assignment #3
#
# Your names and user ids:
#
# (Based on skeleton code by D. Crandall)
#


import random
import math

import numpy as np


# class object to keep track of transition, emission probabilities, MAP probabilities of viterbi, total number of words and mcmc probability.
class Solver:
    def __init__(self):
        self.tagCount = {}
        self.emission = {}
        self.transition = {}
        self.total_count = 0
        self.posterior_viterbi = []
        self.mcmc_prob = []

    # log of the posterior probability of a given sentence
    def posterior(self, model, sentence, label):
        post_prob = []
        if model == "Simple":
            for i in range(len(sentence)):
                word = sentence[i]
                tag = label[i]
                if word in self.emission.keys():

                    pb_word = self.emission.get(word, {}).get(tag, 1e-10) / sum(self.emission[word].values())
                    if tag in self.tagCount.keys():
                        pb_tagCount = self.tagCount[tag] / self.total_count
                    post_prob.append(np.log(pb_word * pb_tagCount))
                else:
                    post_prob.append(np.log(1e-10))
            return sum(post_prob)
        elif model == "Complex":
            return sum(self.mcmc_prob)
        elif model == "HMM":
            return sum(np.log(self.posterior_viterbi))
        else:
            print("Unknown algo!")

    # training to calculate transition and emission probabilities
    def train(self, data):
        tagCount = {}
        emission = {}
        total_count = 0
        transition = {}
        for (sentence, tag) in data:
            for i in range(len(tag)):
                total_count += 1
                if sentence[i] in emission.keys():
                    if tag[i] in emission[sentence[i]]:
                        emission[sentence[i]][tag[i]] = emission[sentence[i]][tag[i]] + 1
                    else:
                        emission[sentence[i]][tag[i]] = 1
                else:
                    emission[sentence[i]] = {}
                    emission[sentence[i]][tag[i]] = 1
                tagCount[tag[i]] = 1 if tag[i] not in tagCount else tagCount[tag[i]] + 1
                # transition probability
                if i == 0:
                    if tag[i] in transition.keys():
                        if "start" in transition[tag[i]].keys():
                            transition[tag[i]]["start"] = transition[tag[i]]["start"] + 1
                        else:
                            transition[tag[i]]["start"] = {}
                            transition[tag[i]]["start"] = 1
                    else:
                        transition[tag[i]] = {}
                        transition[tag[i]]["start"] = 1
                elif tag[i] in transition.keys():
                    if tag[i - 1] in transition[tag[i]].keys():
                        transition[tag[i]][tag[i - 1]] = transition[tag[i]][tag[i - 1]] + 1
                    else:
                        transition[tag[i]][tag[i - 1]] = {}
                        transition[tag[i]][tag[i - 1]] = 1
                else:
                    transition[tag[i]] = {}
                    transition[tag[i]][tag[i - 1]] = 1
        unique_tags = transition.keys()
        #       set probability for transition of tags do not occur in training set to 1
        for tag in transition.keys():
            for unique_tag in unique_tags:
                if unique_tag not in transition[tag]:
                    transition[tag][unique_tag] = 1

        self.tagCount = tagCount
        self.emission = emission
        self.total_count = total_count
        self.transition = transition

    def simplified(self, sentence):
        tags = []
        for word in sentence:
            if word in self.emission.keys():
                tags.append(max(self.emission[word].keys(), key=(lambda i: self.emission[word][i])))
            else:
                tags.append("noun")
        return tags

    def complex_mcmc(self, sentence):
        sample = []
        tags = self.transition.keys()
        sample.append(["noun"] * len(sentence))

        for s in range(10):
            X = sample[s]
            for i in range(len(sentence)):
                word = sentence[i]

                prob = {}
                for tag in tags:
                    trans_norm = sum(self.transition[tag].values())
                    if word in self.emission.keys():
                        emission_prob = self.emission.get(word, {}).get(tag, 1e-10) / sum(self.emission[word].values())
                    else:
                        emission_prob = 1e-10
                    if i == 0:  # starting word
                        prob[tag] = emission_prob * (self.transition[tag]["start"] / trans_norm)
                    elif i == len(sentence):
                        prob[tag] = emission_prob * (self.transition[tag][X[i - 1]] / trans_norm) * (
                                    self.transition[tag][X[0]] / trans_norm)
                    else:
                        prob[tag] = emission_prob * (self.transition[tag][X[i - 1]] / trans_norm)
                X[i] = max(prob.keys(), key=(lambda x: prob[x]))

            sample.append(X)

        last_sample = sample[-1]
        sample = []
        sample.append(last_sample)

        for s in range(20):
            X = sample[s]
            sentence_prob = []
            for i in range(len(sentence)):
                word = sentence[i]
                prob = {}
                for tag in tags:
                    trans_norm = sum(self.transition[tag].values())
                    if word in self.emission.keys():
                        emission_prob = self.emission.get(word, {}).get(tag, 1e-10) / sum(self.emission[word].values())
                    else:
                        emission_prob = 1e-10
                    if i == 0:  # starting word
                        prob[tag] = np.log(emission_prob) + np.log((self.transition[tag]["start"] / trans_norm))
                    elif i == len(sentence) - 1:
                        prob[tag] = np.log(emission_prob) + np.log(
                            self.transition[tag][X[i - 1]] / trans_norm) + np.log(
                            self.transition[tag][X[0]] / trans_norm)
                    else:
                        prob[tag] = np.log(emission_prob) + np.log(self.transition[tag][X[i - 1]] / trans_norm)
                X[i] = max(prob.keys(), key=(lambda x: prob[x]))
                p = max(prob.values())
            sentence_prob.append(p)
            sample.append(X)
        self.mcmc_prob = sentence_prob
        return sample[-1]

    def hmm_viterbi(self, sentence):
        tags = []
        vt_list = []
        self.posterior_viterbi = []
        for i in range(len(sentence)):
            word = sentence[i]
            if word in self.emission.keys():
                vt_1 = [(key, (value / sum(self.emission[word].values())) * self.transition[key]["start"] / sum(
                    self.transition[key].values())) \
                            if i == 0 else (key, (value / sum(self.emission[word].values())) * (
                            self.transition[key][tags[i - 1]] / sum(self.transition[key].values())) * (vt_list[i - 1])) \
                        for key, value in self.emission[word].items()]
                vt_list.append(max(vt_1, key=lambda x: x[1])[1])
                tags.append(max(vt_1, key=lambda x: x[1])[0])
            else:
                vt_list.append(float(1e-10))
                tags.append("noun")
        self.posterior_viterbi = vt_list
        return tags


        # This solve() method is called by label.py, so you should keep the interface the

    #  same, but you can change the code itself.
    # It should return a list of part-of-speech labelings of the sentence, one
    #  part of speech per word.
    #
    def solve(self, model, sentence):
        if model == "Simple":
            return self.simplified(sentence)
        elif model == "Complex":
            return self.complex_mcmc(sentence)
        elif model == "HMM":
            return self.hmm_viterbi(sentence)
        else:
            print("Unknown algo!")

