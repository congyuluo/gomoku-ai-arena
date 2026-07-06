#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "weights_current.hpp"

namespace {

constexpr int kEmpty = 0;
constexpr int kSelf = 1;
constexpr int kOpponent = 2;

struct Move {
    int x = -1;
    int y = -1;
};

struct Board {
    int size = 0;
    std::vector<int> cells;

    explicit Board(int board_size = 0) : size(board_size), cells(board_size * board_size, 0) {}

    int at(int x, int y) const { return cells[x * size + y]; }
    int& at(int x, int y) { return cells[x * size + y]; }

    bool has_empty() const {
        return std::find(cells.begin(), cells.end(), kEmpty) != cells.end();
    }

    bool any_stone() const {
        return std::any_of(cells.begin(), cells.end(), [](int value) { return value != kEmpty; });
    }
};

struct Child {
    Board board;
    Move move;
};

struct Pattern {
    std::string_view pattern;
    int index;
};

std::vector<int>* g_generation_trace = nullptr;
std::size_t g_generation_trace_limit = 0;

constexpr Pattern kSelfPatterns[] = {
    {"00001", 0}, {"00010", 1}, {"00011", 2}, {"00100", 3}, {"00101", 4}, {"00110", 5},
    {"00111", 6}, {"01001", 7}, {"01010", 8}, {"01011", 9}, {"01101", 10}, {"01110", 11},
    {"01111", 12}, {"10001", 13}, {"10011", 14}, {"10101", 15}, {"10111", 16}, {"11011", 17},
    {"11111", 18}, {"011110", 19}, {"011010", 20}, {"101110", 21},
};

constexpr Pattern kOpponentPatterns[] = {
    {"00002", 0}, {"00020", 1}, {"00022", 2}, {"00200", 3}, {"00202", 4}, {"00220", 5},
    {"00222", 6}, {"02002", 7}, {"02020", 8}, {"02022", 9}, {"02202", 10}, {"02220", 11},
    {"02222", 12}, {"20002", 13}, {"20022", 14}, {"20202", 15}, {"20222", 16}, {"22022", 17},
    {"22222", 18}, {"022220", 19}, {"022020", 20}, {"202220", 21},
};

constexpr Pattern kSelfNoMirrorPatterns[] = {
    {"00001", 0}, {"00010", 1}, {"00011", 2}, {"00101", 4}, {"00110", 5}, {"00111", 6},
    {"01001", 7}, {"01011", 9}, {"01101", 10}, {"01111", 12}, {"10011", 14}, {"10111", 16},
    {"011010", 20}, {"101110", 21},
};

constexpr Pattern kOpponentNoMirrorPatterns[] = {
    {"00002", 0}, {"00020", 1}, {"00022", 2}, {"00202", 4}, {"00220", 5}, {"00222", 6},
    {"02002", 7}, {"02022", 9}, {"02202", 10}, {"02222", 12}, {"20022", 14}, {"20222", 16},
    {"022020", 20}, {"202220", 21},
};

int level_to_depth(const std::string& level) {
    if (level == "test") {
        return 1;
    }
    if (level == "EASY" || level == "easy") {
        return 2;
    }
    if (level == "MEDIUM" || level == "medium") {
        return 3;
    }
    throw std::invalid_argument("unknown level: " + level);
}

bool in_range_2(const Board& board, int x, int y) {
    const int n = board.size;
    if (x - 2 >= 0 && board.at(x - 2, y) != 0) return true;
    if (x + 2 < n && board.at(x + 2, y) != 0) return true;
    if (y - 2 >= 0 && board.at(x, y - 2) != 0) return true;
    if (y + 2 < n && board.at(x, y + 2) != 0) return true;
    if (x - 1 >= 0 && board.at(x - 1, y) != 0) return true;
    if (x + 1 < n && board.at(x + 1, y) != 0) return true;
    if (y - 1 >= 0 && board.at(x, y - 1) != 0) return true;
    if (y + 1 < n && board.at(x, y + 1) != 0) return true;
    if (x + 1 < n && y + 1 < n && board.at(x + 1, y + 1) != 0) return true;
    if (x + 1 < n && y - 1 >= 0 && board.at(x + 1, y - 1) != 0) return true;
    if (x - 1 >= 0 && y + 1 < n && board.at(x - 1, y + 1) != 0) return true;
    if (x - 1 >= 0 && y - 1 >= 0 && board.at(x - 1, y - 1) != 0) return true;
    if (x + 2 < n && y + 2 < n && board.at(x + 2, y + 2) != 0) return true;
    if (x + 2 < n && y - 2 >= 0 && board.at(x + 2, y - 2) != 0) return true;
    if (x - 2 >= 0 && y + 2 < n && board.at(x - 2, y + 2) != 0) return true;
    if (x - 2 >= 0 && y - 2 >= 0 && board.at(x - 2, y - 2) != 0) return true;
    return false;
}

std::vector<Child> get_positions_2(const Board& parent, int player) {
    if (g_generation_trace != nullptr && g_generation_trace->size() < g_generation_trace_limit) {
        g_generation_trace->push_back(player);
    }

    std::vector<Child> children;
    for (int x = 0; x < parent.size; ++x) {
        for (int y = 0; y < parent.size; ++y) {
            if (parent.at(x, y) == 0 && in_range_2(parent, x, y)) {
                Board child = parent;
                child.at(x, y) = player;
                children.push_back({std::move(child), {x, y}});
            }
        }
    }
    return children;
}

bool has_sequence(const std::vector<int>& line, int player) {
    int run = 0;
    for (int value : line) {
        run = (value == player) ? run + 1 : 0;
        if (run >= 5) return true;
    }
    return false;
}

std::vector<std::vector<int>> get_1d_arrays(const Board& board) {
    std::vector<std::vector<int>> lines;
    const int n = board.size;
    for (int i = 0; i < n; ++i) {
        std::vector<int> row;
        std::vector<int> col;
        row.reserve(n);
        col.reserve(n);
        for (int j = 0; j < n; ++j) {
            row.push_back(board.at(i, j));
            col.push_back(board.at(j, i));
        }
        lines.push_back(std::move(row));
        lines.push_back(std::move(col));

        auto add_diag = [&](int offset, bool flipped) {
            std::vector<int> line;
            if (offset >= 0) {
                for (int k = 0; k < n - offset; ++k) {
                    const int x = k;
                    const int y = k + offset;
                    line.push_back(flipped ? board.at(x, n - 1 - y) : board.at(x, y));
                }
            } else {
                const int positive = -offset;
                for (int k = 0; k < n - positive; ++k) {
                    const int x = k + positive;
                    const int y = k;
                    line.push_back(flipped ? board.at(x, n - 1 - y) : board.at(x, y));
                }
            }
            lines.push_back(std::move(line));
        };

        if (i == 0) {
            add_diag(0, false);
            add_diag(0, true);
        } else {
            add_diag(i, false);
            add_diag(-i, false);
            add_diag(i, true);
            add_diag(-i, true);
        }
    }
    return lines;
}

int check_win(const Board& board) {
    for (const auto& line : get_1d_arrays(board)) {
        if (line.size() < 5) continue;
        if (std::all_of(line.begin(), line.end(), [](int value) { return value == 0; })) continue;
        if (has_sequence(line, kSelf)) return kSelf;
        if (has_sequence(line, kOpponent)) return kOpponent;
    }
    return 0;
}

bool check_game_over(const Board& board) {
    return check_win(board) != 0 || !board.has_empty();
}

void match_patterns(const std::string& text, const Pattern* patterns, std::size_t count, std::vector<float>& counts, int offset) {
    for (std::size_t i = 0; i < count; ++i) {
        if (text.find(patterns[i].pattern) != std::string::npos) {
            counts[offset + patterns[i].index] += 1.0f;
        }
    }
}

std::vector<float> get_feature(const Board& board, bool maximizing_player) {
    std::vector<float> counts(66, 0.0f);
    for (const auto& line : get_1d_arrays(board)) {
        if (line.size() < 5) continue;
        if (std::all_of(line.begin(), line.end(), [](int value) { return value == 0; })) continue;

        std::string text;
        text.reserve(line.size());
        for (int value : line) {
            text.push_back(static_cast<char>('0' + value));
        }
        std::string reversed(text.rbegin(), text.rend());
        match_patterns(text, kSelfPatterns, std::size(kSelfPatterns), counts, 0);
        match_patterns(reversed, kSelfNoMirrorPatterns, std::size(kSelfNoMirrorPatterns), counts, 0);
        match_patterns(text, kOpponentPatterns, std::size(kOpponentPatterns), counts, 22);
        match_patterns(reversed, kOpponentNoMirrorPatterns, std::size(kOpponentNoMirrorPatterns), counts, 22);
    }

    const float marker = maximizing_player ? 0.0f : 1.0f;
    std::fill(counts.begin() + 44, counts.end(), marker);
    return counts;
}

float predict(const std::vector<float>& features) {
    float hidden[minizero_weights::HIDDEN_SIZE];
    for (int j = 0; j < minizero_weights::HIDDEN_SIZE; ++j) {
        float value = minizero_weights::B0[j];
        for (int i = 0; i < minizero_weights::INPUT_SIZE; ++i) {
            value += features[i] * minizero_weights::W0[i * minizero_weights::HIDDEN_SIZE + j];
        }
        hidden[j] = std::max(0.0f, value);
    }

    float output = minizero_weights::B1[0];
    for (int i = 0; i < minizero_weights::HIDDEN_SIZE; ++i) {
        output += hidden[i] * minizero_weights::W1[i];
    }
    return std::tanh(output);
}

float minimax_value(const Board& position, int depth, float alpha, float beta, bool maximizing_player) {
    const bool game_over = check_game_over(position);
    if (depth == 0 || game_over) {
        if (game_over) {
            const int winner = check_win(position);
            if (winner == kSelf) return 1.0f;
            if (winner == kOpponent) return -1.0f;
            return 0.0f;
        }
        return predict(get_feature(position, maximizing_player));
    }

    if (maximizing_player) {
        float max_eval = -std::numeric_limits<float>::infinity();
        const auto children = get_positions_2(position, kSelf);
        for (const auto& child : children) {
            const float evaluation = minimax_value(child.board, depth - 1, alpha, beta, false);
            max_eval = std::max(max_eval, evaluation);
            alpha = std::max(alpha, evaluation);
            if (beta <= alpha) {
                break;
            }
        }
        return max_eval;
    } else {
        float min_eval = std::numeric_limits<float>::infinity();
        const auto children = get_positions_2(position, kOpponent);
        for (const auto& child : children) {
            const float evaluation = minimax_value(child.board, depth - 1, alpha, beta, true);
            min_eval = std::min(min_eval, evaluation);
            beta = std::min(beta, evaluation);
            if (beta <= alpha) {
                break;
            }
        }
        return min_eval;
    }
}

Move choose_move(const Board& position, int depth) {
    if (!position.any_stone()) {
        throw std::invalid_argument("empty-board first moves are random in the Python implementation");
    }

    Move best_move{-1, -1};
    float max_eval = -std::numeric_limits<float>::infinity();
    float alpha = -std::numeric_limits<float>::infinity();
    float beta = std::numeric_limits<float>::infinity();

    const auto children = get_positions_2(position, kSelf);
    for (const auto& child : children) {
        const float evaluation = minimax_value(child.board, depth - 1, alpha, beta, false);
        if (evaluation > max_eval) {
            best_move = child.move;
        }
        max_eval = std::max(max_eval, evaluation);
        alpha = std::max(alpha, evaluation);
        if (beta <= alpha) {
            break;
        }
    }

    if (best_move.x < 0) {
        throw std::runtime_error("no candidate move found");
    }
    return best_move;
}

Board parse_board(int size, const std::string& flat) {
    if (size < 5 || flat.size() != static_cast<std::size_t>(size * size)) {
        throw std::invalid_argument("board string length does not match size");
    }
    Board board(size);
    for (std::size_t i = 0; i < flat.size(); ++i) {
        const char ch = flat[i];
        if (ch < '0' || ch > '2') {
            throw std::invalid_argument("board string must contain only 0, 1, and 2");
        }
        board.cells[i] = ch - '0';
    }
    return board;
}

std::string arg_value(int argc, char** argv, const std::string& key, const std::string& fallback = "") {
    for (int i = 1; i + 1 < argc; ++i) {
        if (argv[i] == key) {
            return argv[i + 1];
        }
    }
    return fallback;
}

bool has_arg(int argc, char** argv, const std::string& key) {
    for (int i = 1; i < argc; ++i) {
        if (argv[i] == key) return true;
    }
    return false;
}

void run_single(int argc, char** argv) {
    const std::string level = arg_value(argc, argv, "--level", "test");
    const int size = std::stoi(arg_value(argc, argv, "--size"));
    const std::string flat = arg_value(argc, argv, "--board");
    const int depth = level_to_depth(level);
    const Board board = parse_board(size, flat);

    const auto start = std::chrono::steady_clock::now();
    const Move move = choose_move(board, depth);
    const auto end = std::chrono::steady_clock::now();
    const auto micros = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    std::cout << move.x << ' ' << move.y << ' ' << micros << '\n';
}

void run_batch() {
    std::string level;
    int size = 0;
    std::string flat;
    while (std::cin >> level >> size >> flat) {
        try {
            const int depth = level_to_depth(level);
            const Board board = parse_board(size, flat);
            const auto start = std::chrono::steady_clock::now();
            const Move move = choose_move(board, depth);
            const auto end = std::chrono::steady_clock::now();
            const auto micros = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
            std::cout << move.x << ' ' << move.y << ' ' << micros << '\n';
        } catch (const std::exception& exc) {
            std::cout << "ERR " << exc.what() << '\n';
        }
    }
}

void run_self_test() {
    Board board(5);
    board.at(2, 2) = kSelf;

    std::vector<int> trace;
    g_generation_trace = &trace;
    g_generation_trace_limit = 3;
    (void)choose_move(board, level_to_depth("MEDIUM"));
    g_generation_trace = nullptr;
    g_generation_trace_limit = 0;

    const std::vector<int> expected = {kSelf, kOpponent, kSelf};
    if (trace != expected) {
        std::string actual;
        for (int player : trace) {
            if (!actual.empty()) actual += ',';
            actual += std::to_string(player);
        }
        throw std::runtime_error("MEDIUM minimax generation order mismatch: " + actual);
    }

    std::cout << "OK medium alternates 1,2,1\n";
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (has_arg(argc, argv, "--self-test")) {
            run_self_test();
            return 0;
        }
        if (has_arg(argc, argv, "--batch")) {
            run_batch();
            return 0;
        }
        run_single(argc, argv);
        return 0;
    } catch (const std::exception& exc) {
        std::cerr << "error: " << exc.what() << '\n';
        return 1;
    }
}
