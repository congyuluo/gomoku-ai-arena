CXX ?= g++
CXXFLAGS ?= -O3 -std=c++20 -Wall -Wextra -pedantic
ROOT := $(abspath ..)
PYTHON ?= $(ROOT)/.venv/bin/python

BIN := minizero_native
SRC := src/minizero_native.cpp

.PHONY: all clean

all: $(BIN)

$(BIN): $(SRC) include/weights_current.hpp
	$(CXX) $(CXXFLAGS) -Iinclude $(SRC) -o $(BIN)

include/weights_current.hpp: tools/export_weights.py ../numpy_network_weights.npz
	$(PYTHON) tools/export_weights.py

clean:
	rm -f $(BIN)
