# -*- coding: utf-8 -*-
"""200N-3LR.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1HKXLsjXvO-QZL0MboRE3cwHvPhw3Xfyo
"""

!pip install gym >/dev/null

!pip install JSAnimation >/dev/null

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
from JSAnimation.IPython_display import display_animation
from matplotlib import animation
import matplotlib.pyplot as plt
from IPython.display import HTML

def display_frames_as_gif(frames):
    """
    Displays a list of frames as a gif, with controls
    """
    plt.figure(figsize=(frames[0].shape[1] / 72.0, frames[0].shape[0] / 72.0), dpi = 144)
    patch = plt.imshow(frames[0])
    plt.axis('off')

    def animate(i):
        patch.set_data(frames[i])

    anim = animation.FuncAnimation(plt.gcf(), animate, frames = len(frames), interval=50)
    HTML(anim.to_jshtml())

"""## Step 2: Playing Pong"""

# Commented out IPython magic to ensure Python compatibility.
# %pip install -U gym>=0.21.0
# %pip install -U gym[atari,accept-rom-license]

import gym
env = gym.make('Pong-v0')

env.action_space

env.observation_space

# demo environment
observation = env.reset()
cumulated_reward = 0

frames = []
for t in range(1000):
    frames.append(env.render(mode = 'rgb_array'))
    action = env.action_space.sample()
#     it will print Action: {}.format(t+1)  
    observation, reward, done, info = env.step(action)
    cumulated_reward += reward
    if done:
        print("Episode finished after {} timesteps, accumulated reward = {}".format(t+1, cumulated_reward))
        break
print("Episode finished without success, accumulated reward = {}".format(cumulated_reward))

env.close()

def sigmoid(x): 
  return 1.0 / (1.0 + np.exp(-x)) 

def prepro(I):
  """ prepro 210x160x3 uint8 frame into 6400 (80x80) 1D float vector """
  I = I[35:195] 
  I = I[::2,::2,0] 
  I[I == 144] = 0 
  I[I == 109] = 0 
  I[I != 0] = 1 
  return I.astype(np.float).ravel()

def policy_forward(x):
  h = np.dot(model['W1'], x)
  h[h<0] = 0 
  logp = np.dot(model['W2'], h)
  p = sigmoid(logp)
  return p, h 

def model_step(model, observation, prev_x):
  
  cur_x = prepro(observation)
  x = cur_x - prev_x if prev_x is not None else np.zeros(D)
  prev_x = cur_x
  
  
  aprob, _ = policy_forward(x)
  action = 2 if aprob >= 0.5 else 3 
  
  return action, prev_x

def play_game(env, model):
  observation = env.reset()

  frames = []
  cumulated_reward = 0

  prev_x = None 

  for t in range(1000):
      frames.append(env.render(mode = 'rgb_array'))
      action, prev_x = model_step(model, observation, prev_x)
      observation, reward, done, info = env.step(action)
      cumulated_reward += reward
      if done:
          print("Episode finished after {} timesteps, accumulated reward = {}".format(t+1, cumulated_reward))
          break
  print("Episode finished without success, accumulated reward = {}".format(cumulated_reward))
  display_frames_as_gif(frames)
  env.close()

"""## Step 3: Policy Gradient from Scratch"""

import numpy as np

# model initialization
H = 200 # number of hidden layer neurons
D = 80 * 80 
model = {}
model['W1'] = np.random.randn(H,D) / np.sqrt(D) 
model['W2'] = np.random.randn(H) / np.sqrt(H)

# hyperparameters
batch_size = 10 
# learning_rate = 1e-3
learning_rate = 1e-3
 
gamma = 0.99 
decay_rate = 0.99 
  
grad_buffer = { k : np.zeros_like(v) for k,v in model.items() } 
rmsprop_cache = { k : np.zeros_like(v) for k,v in model.items() } 

def discount_rewards(r):
  """ take 1D float array of rewards and compute discounted reward """
  discounted_r = np.zeros_like(r, dtype=np.float32)
  running_add = 0
  for t in reversed(range(0, r.size)):
    if r[t] != 0: running_add = 0 
    running_add = running_add * gamma + r[t]
    discounted_r[t] = running_add
  return discounted_r

def policy_backward(epx, eph, epdlogp):
  """ backward pass. (eph is array of intermediate hidden states) """
  dW2 = np.dot(eph.T, epdlogp).ravel()
  dh = np.outer(epdlogp, model['W2'])
  dh[eph <= 0] = 0 
  dW1 = np.dot(dh.T, epx)
  return {'W1':dW1, 'W2':dW2}

def train_model(env, model, total_episodes = 100):
  hist = []
  observation = env.reset()

  prev_x = None 
  xs,hs,dlogps,drs = [],[],[],[]
  running_reward = None
  reward_sum = 0
  episode_number = 0

  while True:
    
    cur_x = prepro(observation)
    x = cur_x - prev_x if prev_x is not None else np.zeros(D)
    prev_x = cur_x

    
    aprob, h = policy_forward(x)
    action = 2 if np.random.uniform() < aprob else 3 

    
    xs.append(x) 
    hs.append(h) 
    y = 1 if action == 2 else 0 
    dlogps.append(y - aprob) 

    
    observation, reward, done, info = env.step(action)
    reward_sum += reward

    drs.append(reward) 

    if done: 
      episode_number += 1

      
      epx = np.vstack(xs)
      eph = np.vstack(hs)
      epdlogp = np.vstack(dlogps)
      epr = np.vstack(drs)
      xs,hs,dlogps,drs = [],[],[],[] 

      
      discounted_epr = discount_rewards(epr)
      
      discounted_epr -= np.mean(discounted_epr)
      discounted_epr /= np.std(discounted_epr)

      epdlogp *= discounted_epr 
      grad = policy_backward(epx, eph, epdlogp)
      for k in model: grad_buffer[k] += grad[k] 

      
      if episode_number % batch_size == 0:
        for k,v in model.items():
          g = grad_buffer[k] 
          rmsprop_cache[k] = decay_rate * rmsprop_cache[k] + (1 - decay_rate) * g**2
          model[k] += learning_rate * g / (np.sqrt(rmsprop_cache[k]) + 1e-5)
          grad_buffer[k] = np.zeros_like(v) 

      
      running_reward = reward_sum if running_reward is None else running_reward * 0.99 + reward_sum * 0.01
      hist.append((episode_number, reward_sum, running_reward))
      print ('resetting env. episode %f, reward total was %f. running mean: %f' % (episode_number, reward_sum, running_reward))
      reward_sum = 0
      observation = env.reset() 
      prev_x = None
      if episode_number == total_episodes: return hist

      if reward != 0: 
        print (('ep %d: game finished, reward: %f' % (episode_number, reward)) + ('' if reward == -1 else ' !!!!!!!!'))

# Commented out IPython magic to ensure Python compatibility.
# %time hist1 = train_model(env, model, total_episodes=500)

# Commented out IPython magic to ensure Python compatibility.
# %time hist2 = train_model(env, model, total_episodes=500)

play_game(env, model)

# Commented out IPython magic to ensure Python compatibility.
# %time hist3 = train_model(env, model, total_episodes=1500)

play_game(env, model)