const BLACK = 1;
const WHITE = 2;
const EMPTY = 0;

const canvas = document.getElementById("boardCanvas");
const ctx = canvas.getContext("2d");
const statusText = document.getElementById("statusText");
const agentSelect = document.getElementById("agentSelect");
const boardSizeSelect = document.getElementById("boardSizeSelect");
const newGameButton = document.getElementById("newGameButton");
const undoButton = document.getElementById("undoButton");
const moveList = document.getElementById("moveList");
const thinkingOverlay = document.getElementById("thinkingOverlay");
const humanScoreEl = document.getElementById("humanScore");
const aiScoreEl = document.getElementById("aiScore");
const drawScoreEl = document.getElementById("drawScore");

const state = {
  size: 15,
  board: [],
  human: BLACK,
  ai: WHITE,
  turn: BLACK,
  gameOver: false,
  thinking: false,
  lastMove: null,
  hoverMove: null,
  winLine: null,
  history: [],
  scores: { human: 0, ai: 0, draw: 0 },
};

function makeEmptyBoard(size) {
  return Array.from({ length: size }, () => Array(size).fill(EMPTY));
}

function selectedHumanColor() {
  return Number(document.querySelector("input[name='humanColor']:checked").value);
}

function updateColorsFromControls() {
  state.human = selectedHumanColor();
  state.ai = state.human === BLACK ? WHITE : BLACK;
}

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * ratio);
  canvas.height = Math.round(rect.height * ratio);
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  drawBoard();
}

function boardMetrics() {
  const rect = canvas.getBoundingClientRect();
  const size = Math.min(rect.width, rect.height);
  const padding = Math.max(22, size * 0.065);
  const step = (size - padding * 2) / (state.size - 1);
  return { size, padding, step };
}

function drawBoard() {
  const rect = canvas.getBoundingClientRect();
  ctx.clearRect(0, 0, rect.width, rect.height);

  const { size, padding, step } = boardMetrics();
  ctx.fillStyle = "#d9b06f";
  ctx.fillRect(0, 0, rect.width, rect.height);

  ctx.strokeStyle = "#493520";
  ctx.lineWidth = 1;
  for (let i = 0; i < state.size; i += 1) {
    const p = padding + i * step;
    ctx.beginPath();
    ctx.moveTo(padding, p);
    ctx.lineTo(size - padding, p);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(p, padding);
    ctx.lineTo(p, size - padding);
    ctx.stroke();
  }

  drawStarPoints(padding, step);

  for (let x = 0; x < state.size; x += 1) {
    for (let y = 0; y < state.size; y += 1) {
      if (state.board[x][y] !== EMPTY) {
        drawStone(x, y, state.board[x][y], padding, step);
      }
    }
  }

  if (state.lastMove) {
    drawLastMove(state.lastMove, padding, step);
  }
  if (state.hoverMove && !state.gameOver && !state.thinking && state.turn === state.human) {
    drawPreviewStone(state.hoverMove, state.human, padding, step);
  }
  if (state.winLine) {
    drawWinLine(state.winLine, padding, step);
  }
}

function drawStarPoints(padding, step) {
  const points = starPoints(state.size);
  ctx.fillStyle = "#493520";
  for (const [x, y] of points) {
    ctx.beginPath();
    ctx.arc(padding + x * step, padding + y * step, 3.2, 0, Math.PI * 2);
    ctx.fill();
  }
}

function starPoints(size) {
  if (size < 9) return [];
  const low = size >= 13 ? 3 : 2;
  const high = size - 1 - low;
  const mid = Math.floor(size / 2);
  return [
    [low, low],
    [low, high],
    [high, low],
    [high, high],
    [mid, mid],
  ];
}

function drawStone(x, y, player, padding, step) {
  const cx = padding + x * step;
  const cy = padding + y * step;
  const radius = Math.max(8, step * 0.42);
  const gradient = ctx.createRadialGradient(cx - radius * 0.35, cy - radius * 0.45, radius * 0.1, cx, cy, radius);

  if (player === BLACK) {
    gradient.addColorStop(0, "#445047");
    gradient.addColorStop(1, "#090d0b");
  } else {
    gradient.addColorStop(0, "#ffffff");
    gradient.addColorStop(1, "#d8d8d0");
  }

  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fillStyle = gradient;
  ctx.fill();
  ctx.strokeStyle = player === BLACK ? "#030504" : "#b6b6ad";
  ctx.lineWidth = 1.2;
  ctx.stroke();
}

function drawLastMove(move, padding, step) {
  const [x, y] = move;
  const cx = padding + x * step;
  const cy = padding + y * step;
  ctx.save();
  ctx.strokeStyle = "#b44335";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.arc(cx, cy, Math.max(5, step * 0.16), 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();
}

function drawPreviewStone(move, player, padding, step) {
  const [x, y] = move;
  const cx = padding + x * step;
  const cy = padding + y * step;
  const radius = Math.max(8, step * 0.42);

  ctx.save();
  ctx.globalAlpha = 0.38;
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fillStyle = player === BLACK ? "#111614" : "#fbfbf5";
  ctx.fill();
  ctx.globalAlpha = 0.7;
  ctx.strokeStyle = player === BLACK ? "#030504" : "#9f9f96";
  ctx.lineWidth = 1.2;
  ctx.stroke();
  ctx.restore();
}

function drawWinLine(line, padding, step) {
  const [start, end] = line;
  ctx.save();
  ctx.strokeStyle = "#b44335";
  ctx.lineWidth = 5;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(padding + start[0] * step, padding + start[1] * step);
  ctx.lineTo(padding + end[0] * step, padding + end[1] * step);
  ctx.stroke();
  ctx.restore();
}

function canvasToPoint(event) {
  const rect = canvas.getBoundingClientRect();
  const { padding, step } = boardMetrics();
  const x = Math.round((event.clientX - rect.left - padding) / step);
  const y = Math.round((event.clientY - rect.top - padding) / step);
  if (x < 0 || y < 0 || x >= state.size || y >= state.size) return null;

  const px = padding + x * step;
  const py = padding + y * step;
  const distance = Math.hypot(event.clientX - rect.left - px, event.clientY - rect.top - py);
  if (distance > step * 0.45) return null;
  return [x, y];
}

function placeMove(move, player, source) {
  const [x, y] = move;
  state.board[x][y] = player;
  state.lastMove = move;
  state.history.push({ move, player, source });
  appendMove(move, player, source);
  const result = checkWinner();
  if (result.winner) {
    finishGame(result.winner, result.line);
  } else if (isBoardFull()) {
    finishGame(EMPTY, null);
  } else {
    state.turn = player === BLACK ? WHITE : BLACK;
    setStatusForTurn();
  }
  drawBoard();
}

function appendMove(move, player, source) {
  const li = document.createElement("li");
  const stone = player === BLACK ? "Black" : "White";
  const actor = source === "human" ? "You" : "AI";
  li.innerHTML = `<strong>${actor}</strong> ${stone} ${move[0] + 1},${move[1] + 1}`;
  moveList.appendChild(li);
  moveList.scrollTop = moveList.scrollHeight;
}

function rebuildMoveList() {
  moveList.innerHTML = "";
  for (const entry of state.history) {
    appendMove(entry.move, entry.player, entry.source);
  }
}

function setStatusForTurn() {
  if (state.gameOver) return;
  if (state.thinking) {
    statusText.textContent = `${agentSelect.value} is choosing a move.`;
  } else if (state.turn === state.human) {
    statusText.textContent = `Your turn as ${state.human === BLACK ? "black" : "white"}.`;
  } else {
    statusText.textContent = `AI turn as ${state.ai === BLACK ? "black" : "white"}.`;
  }
}

function finishGame(winner, line) {
  state.gameOver = true;
  state.winLine = line;
  if (winner === state.human) {
    state.scores.human += 1;
    statusText.textContent = "You win.";
  } else if (winner === state.ai) {
    state.scores.ai += 1;
    statusText.textContent = "AI wins.";
  } else {
    state.scores.draw += 1;
    statusText.textContent = "Draw.";
  }
  updateScoreboard();
}

function updateScoreboard() {
  humanScoreEl.textContent = state.scores.human;
  aiScoreEl.textContent = state.scores.ai;
  drawScoreEl.textContent = state.scores.draw;
}

async function requestAiMove() {
  if (state.gameOver || state.thinking || state.turn !== state.ai) return;
  state.thinking = true;
  state.hoverMove = null;
  thinkingOverlay.hidden = false;
  setStatusForTurn();

  try {
    const response = await fetch("/api/ai-move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agent: agentSelect.value,
        board: state.board,
        player: state.ai,
        seed: Date.now() + state.history.length,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "AI request failed");
    }
    if (payload.move) {
      placeMove(payload.move, state.ai, "ai");
      const ms = Number(payload.elapsed_ms || 0).toFixed(1);
      if (!state.gameOver) {
        statusText.textContent = `AI moved in ${ms} ms. Your turn.`;
      }
    } else if (payload.game_over) {
      finishGame(payload.winner, null);
    }
  } catch (error) {
    statusText.textContent = `AI error: ${error.message}`;
  } finally {
    state.thinking = false;
    thinkingOverlay.hidden = true;
    drawBoard();
  }
}

function checkWinner() {
  const directions = [
    [1, 0],
    [0, 1],
    [1, 1],
    [1, -1],
  ];

  for (let x = 0; x < state.size; x += 1) {
    for (let y = 0; y < state.size; y += 1) {
      const player = state.board[x][y];
      if (player === EMPTY) continue;
      for (const [dx, dy] of directions) {
        const endX = x + dx * 4;
        const endY = y + dy * 4;
        if (endX < 0 || endY < 0 || endX >= state.size || endY >= state.size) continue;
        let count = 1;
        for (let step = 1; step < 5; step += 1) {
          if (state.board[x + dx * step][y + dy * step] === player) count += 1;
        }
        if (count === 5) {
          return { winner: player, line: [[x, y], [endX, endY]] };
        }
      }
    }
  }

  return { winner: EMPTY, line: null };
}

function isBoardFull() {
  return state.board.every((column) => column.every((value) => value !== EMPTY));
}

function newGame(keepScores = true) {
  state.size = Number(boardSizeSelect.value);
  updateColorsFromControls();
  state.board = makeEmptyBoard(state.size);
  state.turn = BLACK;
  state.gameOver = false;
  state.thinking = false;
  state.lastMove = null;
  state.hoverMove = null;
  state.winLine = null;
  state.history = [];
  moveList.innerHTML = "";
  thinkingOverlay.hidden = true;
  if (!keepScores) {
    state.scores = { human: 0, ai: 0, draw: 0 };
    updateScoreboard();
  }
  resizeCanvas();
  setStatusForTurn();
  if (state.ai === BLACK) {
    window.setTimeout(requestAiMove, 180);
  }
}

function undoRound() {
  if (state.thinking || state.gameOver || state.history.length === 0) return;
  let removed = 0;
  while (state.history.length > 0 && removed < 2) {
    const entry = state.history.pop();
    state.board[entry.move[0]][entry.move[1]] = EMPTY;
    removed += 1;
    if (entry.source === "human") break;
  }
  state.gameOver = false;
  state.winLine = null;
  state.hoverMove = null;
  state.lastMove = state.history.length ? state.history[state.history.length - 1].move : null;
  state.turn = state.human;
  rebuildMoveList();
  setStatusForTurn();
  drawBoard();
}

function handleBoardClick(event) {
  if (state.gameOver || state.thinking || state.turn !== state.human) return;
  const move = canvasToPoint(event);
  if (!move) return;
  const [x, y] = move;
  if (state.board[x][y] !== EMPTY) return;
  placeMove(move, state.human, "human");
  if (!state.gameOver) {
    window.setTimeout(requestAiMove, 160);
  }
}

function handleBoardPointerMove(event) {
  if (state.gameOver || state.thinking || state.turn !== state.human) {
    clearHoverMove();
    return;
  }
  const move = canvasToPoint(event);
  if (!move || state.board[move[0]][move[1]] !== EMPTY) {
    clearHoverMove();
    return;
  }
  if (!state.hoverMove || state.hoverMove[0] !== move[0] || state.hoverMove[1] !== move[1]) {
    state.hoverMove = move;
    drawBoard();
  }
}

function clearHoverMove() {
  if (!state.hoverMove) return;
  state.hoverMove = null;
  drawBoard();
}

async function loadAgents() {
  const response = await fetch("/api/agents");
  const payload = await response.json();
  agentSelect.innerHTML = "";
  for (const agent of payload.agents) {
    const option = document.createElement("option");
    option.value = agent.spec;
    option.textContent = agent.label;
    option.title = agent.description;
    agentSelect.appendChild(option);
  }
}

canvas.addEventListener("click", handleBoardClick);
canvas.addEventListener("pointermove", handleBoardPointerMove);
canvas.addEventListener("pointerleave", clearHoverMove);
newGameButton.addEventListener("click", () => newGame(true));
undoButton.addEventListener("click", undoRound);
boardSizeSelect.addEventListener("change", () => newGame(true));
agentSelect.addEventListener("change", () => newGame(true));
document.querySelectorAll("input[name='humanColor']").forEach((input) => {
  input.addEventListener("change", () => newGame(true));
});
window.addEventListener("resize", resizeCanvas);

loadAgents()
  .then(() => {
    newGame(false);
  })
  .catch((error) => {
    statusText.textContent = `Could not load agents: ${error.message}`;
  });
