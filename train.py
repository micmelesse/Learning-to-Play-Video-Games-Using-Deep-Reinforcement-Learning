#!/usr/bin/env python
#
# Implements the Deep Q-Learning Algorithm as shown in the DeepMind paper

import os
import sys
import atari_py
import numpy as np
from network import network
import random
import time

# set parameters, these are in the paper
REPLAY_MEMORY_SIZE = 1000000
REPLAY_START_SIZE = int(REPLAY_MEMORY_SIZE / 50)
REPLAY_MINIBATCH_SIZE = 32
AGENT_HISTORY_LENGTH = 4
# TARGET_NETWORK_UPDATE_FREQUENCY = 10000
DISCOUNT_FACTOR = 0.99
INITIAL_EXPLORATION = 1.0
FINAL_EXPLORATION = 0.1
FINAL_EXPLORATION_FRAME = 40000
DESCEND_EXPLORATION = True
NUM_EPISODES = 200
learning_rate = 0.000001

# initialize ALE interface
ale = atari_py.ALEInterface()
pong_path = atari_py.get_game_path('pong')
ale.loadROM(pong_path)
legal_actions = ale.getMinimalActionSet()
print("legal actions {}".format(legal_actions))
num_of_actions = len(legal_actions)
(screen_width, screen_height) = ale.getScreenDims()
screen_data = np.zeros((screen_height, screen_width, 3),
                       dtype=np.uint8)  # Using RGB

state1 = np.zeros((AGENT_HISTORY_LENGTH, screen_height,
                   screen_width, 3), dtype=np.uint8)
state2 = np.zeros((AGENT_HISTORY_LENGTH, screen_height,
                   screen_width, 3), dtype=np.uint8)

# observe initial state
a = random.randint(0, num_of_actions-1)
for i in range(AGENT_HISTORY_LENGTH):
    ale.act(legal_actions[a])
    ale.getScreenRGB(screen_data)
    state1[i] = np.copy(screen_data)

# initialize replay memory D
D = []
for i in range(REPLAY_START_SIZE):
    is_game_over = 0
    a = random.randint(0, num_of_actions-1)
    for j in range(AGENT_HISTORY_LENGTH):
        r = ale.act(legal_actions[a])
        if (ale.game_over()):
            is_game_over = 1
        ale.getScreenRGB(screen_data)
        state2[j] = np.copy(screen_data)
    D.append((np.copy(state1), a, r, np.copy(state2), is_game_over))
    state1 = np.copy(state2)

# initialize action-value function Q with random weights and its target clone

# main loop
episode = 0
# step = 0
score = 0
e = INITIAL_EXPLORATION
e_decrease = (INITIAL_EXPLORATION - FINAL_EXPLORATION) / \
    FINAL_EXPLORATION_FRAME

losses = []
rewards = []
scores = []
net = network(learning_rate, screen_height, screen_width, num_of_actions)
start_time = time.time()
episode_time = start_time
while (episode < NUM_EPISODES):
    is_game_over = 0

    # select an action a
    if (np.random.sample() < e):
        a = random.randint(0, num_of_actions-1)
    else:
        a = np.argmax(net.evaluate(net.preprocess(state1)))

    # carry out action and observe reward
    reward_sum = 0.0
    # print("action {}".format(action))
    for i in range(AGENT_HISTORY_LENGTH):
        r = ale.act(legal_actions[a])
        reward_sum = reward_sum + r
        if (ale.game_over()):
            is_game_over = 1
        ale.getScreenRGB(screen_data)
        state2[i] = np.copy(screen_data)
    reward_avg = reward_sum / AGENT_HISTORY_LENGTH
    score = score + reward_sum
    rewards.append(reward_sum)

    # store transition <s, a, r, s'> in replay memory D
    if (len(D) == REPLAY_MEMORY_SIZE):
        D.pop(0)
    D.append((np.copy(state1), a, reward_sum,
              np.copy(state2), is_game_over))

    # sample random transitions <ss, aa, rr, ss'> from replay memory D
    D_sample = random.sample(D, REPLAY_MINIBATCH_SIZE)

    # calculate target for each minibatch transition
    for sample in D_sample:
        q_target = net.evaluate(net.preprocess(sample[3]))
        r = sample[2]
        if (sample[4]):
            target = r
        else:
            target = r + DISCOUNT_FACTOR * np.max(q_target)
        # network.backpropagate((t - values[sample[1]]) ** 2)
        losses.append(net.backpropagate(net.preprocess(
            sample[0]), sample[1], target))

    state1 = np.copy(state2)

    if DESCEND_EXPLORATION and e > FINAL_EXPLORATION:
        e = e - e_decrease

    # step = step + 1
    # if (step == TARGET_NETWORK_UPDATE_FREQUENCY):
    #     Q_target = Q.copy()
    #     step = 0

    if (is_game_over):
        ale.reset_game()
        episode = episode + 1
        scores.append(score)
        score = 0
        print("--- Episode %d took %s seconds ---" %
              (episode, time.time() - episode_time))
        episode_time = time.time()
        net.save(losses, rewards, scores)
net.save(losses, rewards, scores)


print("--- Program took %s seconds ---" % (time.time() - start_time))
