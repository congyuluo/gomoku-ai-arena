"""
  Generated using Konverter: https://github.com/ShaneSmiskol/Konverter
"""

import numpy as np
import os

wb = np.load(os.getcwd() + '/numpy_network_weights.npz', allow_pickle=True)
w, b = wb['wb']

def predict(x):
  x = np.array(x, dtype=np.float32)
  l0 = np.dot(x, w[0]) + b[0]
  l0 = np.maximum(0, l0)
  l1 = np.dot(l0, w[1]) + b[1]
  l1 = np.tanh(l1)
  return l1
