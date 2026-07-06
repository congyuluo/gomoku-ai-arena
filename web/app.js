const BLACK = 1;
const WHITE = 2;
const EMPTY = 0;
const HUMAN = "human";

const canvas = document.getElementById("boardCanvas");
const ctx = canvas.getContext("2d");
const statusText = document.getElementById("statusText");
const boardSizeSelect = document.getElementById("boardSizeSelect");
const blackPlayerSelect = document.getElementById("blackPlayerSelect");
const whitePlayerSelect = document.getElementById("whitePlayerSelect");
const swapPlayersButton = document.getElementById("swapPlayersButton");
const newGameButton = document.getElementById("newGameButton");
const pauseButton = document.getElementById("pauseButton");
const undoButton = document.getElementById("undoButton");
const moveList = document.getElementById("moveList");
const thinkingOverlay = document.getElementById("thinkingOverlay");
const blackScoreEl = document.getElementById("blackScore");
const whiteScoreEl = document.getElementById("whiteScore");
const drawScoreEl = document.getElementById("drawScore");

const state = {
  size: 15,
  board: [],
  turn: BLACK,
  paused: false,
  gameOver: false,
  thinking: false,
  lastMove: null,
  hoverMove: null,
  winLine: null,
  history: [],
  scores: { black: 0, white: 0, draw: 0 },
  aiRequestId: 0,
  autoTimer: null,
};

function makeEmptyBoard(size) {
  return Array.from({ length: size }, () => Array(size).fill(EMPTY));
}

function playerName(player) {
  return player === BLACK ? "Black" : "White";
}

function playerSelect(player) {
  return player === BLACK ? blackPlayerSelect : whitePlayerSelect;
}

function controllerValue(player) {
  return playerSelect(player).value;
}

function controllerLabel(player) {
  const select = playerSelect(player);
  return select.options[select.selectedIndex]?.textContent || select.value;
}

function isHumanPlayer(player) {
  return controllerValue(player) === HUMAN;
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
  if (state.hoverMove && !state.gameOver && !state.thinking && !state.paused && isHumanPlayer(state.turn)) {
    drawPreviewStone(state.hoverMove, state.turn, padding, step);
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

function placeMove(move, player, source, actor, elapsedMs = null) {
  const [x, y] = move;
  state.board[x][y] = player;
  state.lastMove = move;
  state.hoverMove = null;
  state.history.push({ move, player, source, actor, elapsedMs });
  appendMove(move, player, source, actor, elapsedMs);
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

function appendMove(move, player, source, actor, elapsedMs = null) {
  const li = document.createElement("li");
  const side = playerName(player);
  const actorLabel = actor || (source === HUMAN ? "Human" : "AI");
  const timeLabel = elapsedMs === null ? "" : ` <span>${Number(elapsedMs).toFixed(1)} ms</span>`;
  li.innerHTML = `<strong>${side}</strong> ${actorLabel} ${move[0] + 1},${move[1] + 1}${timeLabel}`;
  moveList.appendChild(li);
  moveList.scrollTop = moveList.scrollHeight;
}

function rebuildMoveList() {
  moveList.innerHTML = "";
  for (const entry of state.history) {
    appendMove(entry.move, entry.player, entry.source, entry.actor, entry.elapsedMs);
  }
}

function setStatusForTurn() {
  if (state.gameOver) return;
  const side = playerName(state.turn);
  const label = controllerLabel(state.turn);
  if (state.paused) {
    statusText.textContent = `Paused. ${side} to move.`;
  } else if (state.thinking) {
    statusText.textContent = `${side} ${label} is choosing a move.`;
  } else if (isHumanPlayer(state.turn)) {
    statusText.textContent = `${side} human to move.`;
  } else {
    statusText.textContent = `${side} ${label} to move.`;
  }
}

function finishGame(winner, line) {
  state.gameOver = true;
  state.winLine = line;
  clearAutoTimer();
  if (winner === BLACK) {
    state.scores.black += 1;
    statusText.textContent = `Black wins with ${controllerLabel(BLACK)}.`;
  } else if (winner === WHITE) {
    state.scores.white += 1;
    statusText.textContent = `White wins with ${controllerLabel(WHITE)}.`;
  } else {
    state.scores.draw += 1;
    statusText.textContent = "Draw.";
  }
  updateScoreboard();
}

function updateScoreboard() {
  blackScoreEl.textContent = state.scores.black;
  whiteScoreEl.textContent = state.scores.white;
  drawScoreEl.textContent = state.scores.draw;
}

function updatePauseButton() {
  const icon = pauseButton.querySelector("span");
  if (state.paused) {
    icon.textContent = "▶";
    pauseButton.title = "Resume game";
    pauseButton.setAttribute("aria-label", "Resume game");
  } else {
    icon.textContent = "⏸";
    pauseButton.title = "Pause game";
    pauseButton.setAttribute("aria-label", "Pause game");
  }
}

function clearAutoTimer() {
  if (state.autoTimer) {
    window.clearTimeout(state.autoTimer);
    state.autoTimer = null;
  }
}

function scheduleTurn(delayMs = 180) {
  clearAutoTimer();
  if (state.gameOver || state.paused || state.thinking || isHumanPlayer(state.turn)) return;
  state.autoTimer = window.setTimeout(requestAiMove, delayMs);
}

function invalidateAiRequest() {
  state.aiRequestId += 1;
  state.thinking = false;
  thinkingOverlay.hidden = true;
  clearAutoTimer();
}

function isCurrentAiRequest(requestId, player, spec) {
  return (
    requestId === state.aiRequestId &&
    !state.paused &&
    !state.gameOver &&
    state.turn === player &&
    controllerValue(player) === spec
  );
}

async function requestAiMove() {
  if (state.gameOver || state.paused || state.thinking || isHumanPlayer(state.turn)) return;

  const player = state.turn;
  const spec = controllerValue(player);
  const actor = controllerLabel(player);
  const requestId = state.aiRequestId + 1;
  state.aiRequestId = requestId;
  state.thinking = true;
  state.hoverMove = null;
  thinkingOverlay.hidden = false;
  setStatusForTurn();
  drawBoard();

  try {
    const response = await fetch("/api/ai-move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agent: spec,
        board: state.board,
        player,
        seed: Date.now() + state.history.length,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "AI request failed");
    }
    if (!isCurrentAiRequest(requestId, player, spec)) return;

    state.thinking = false;
    thinkingOverlay.hidden = true;
    if (payload.move) {
      placeMove(payload.move, player, "ai", actor, payload.elapsed_ms);
      if (!state.gameOver) {
        statusText.textContent = `${playerName(player)} ${actor} moved.`;
      }
    } else if (payload.game_over) {
      finishGame(payload.winner, null);
    }
  } catch (error) {
    if (requestId === state.aiRequestId) {
      state.thinking = false;
      state.paused = true;
      thinkingOverlay.hidden = true;
      updatePauseButton();
      statusText.textContent = `AI error: ${error.message}`;
    }
  } finally {
    if (requestId === state.aiRequestId) {
      state.thinking = false;
      thinkingOverlay.hidden = true;
      drawBoard();
      scheduleTurn(220);
    }
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
  invalidateAiRequest();
  state.size = Number(boardSizeSelect.value);
  state.board = makeEmptyBoard(state.size);
  state.turn = BLACK;
  state.paused = false;
  state.gameOver = false;
  state.lastMove = null;
  state.hoverMove = null;
  state.winLine = null;
  state.history = [];
  moveList.innerHTML = "";
  thinkingOverlay.hidden = true;
  updatePauseButton();
  if (!keepScores) {
    state.scores = { black: 0, white: 0, draw: 0 };
    updateScoreboard();
  }
  resizeCanvas();
  setStatusForTurn();
  scheduleTurn(180);
}

function undoRound() {
  if (state.thinking || state.history.length === 0) return;
  const wasPaused = state.paused;
  invalidateAiRequest();
  if (state.gameOver) {
    revertFinishedScore();
  }

  const removed = [];
  const last = state.history.pop();
  removed.push(last);
  state.board[last.move[0]][last.move[1]] = EMPTY;

  const previous = state.history[state.history.length - 1];
  if (last.source === "ai" && previous?.source === HUMAN) {
    const paired = state.history.pop();
    removed.push(paired);
    state.board[paired.move[0]][paired.move[1]] = EMPTY;
  }

  const firstRemoved = removed[removed.length - 1];
  state.gameOver = false;
  state.paused = wasPaused;
  state.winLine = null;
  state.hoverMove = null;
  state.lastMove = state.history.length ? state.history[state.history.length - 1].move : null;
  state.turn = firstRemoved.player;
  updatePauseButton();
  rebuildMoveList();
  setStatusForTurn();
  drawBoard();
  scheduleTurn(220);
}

function revertFinishedScore() {
  const result = checkWinner();
  if (result.winner === BLACK) {
    state.scores.black = Math.max(0, state.scores.black - 1);
  } else if (result.winner === WHITE) {
    state.scores.white = Math.max(0, state.scores.white - 1);
  } else if (isBoardFull()) {
    state.scores.draw = Math.max(0, state.scores.draw - 1);
  }
  updateScoreboard();
}

function togglePause() {
  if (state.gameOver) return;
  state.paused = !state.paused;
  if (state.paused) {
    invalidateAiRequest();
  }
  updatePauseButton();
  setStatusForTurn();
  drawBoard();
  if (!state.paused) {
    scheduleTurn(120);
  }
}

function handleBoardClick(event) {
  if (state.gameOver || state.paused || state.thinking || !isHumanPlayer(state.turn)) return;
  const move = canvasToPoint(event);
  if (!move) return;
  const [x, y] = move;
  if (state.board[x][y] !== EMPTY) return;
  placeMove(move, state.turn, HUMAN, "Human");
  scheduleTurn(160);
}

function handleBoardPointerMove(event) {
  if (state.gameOver || state.paused || state.thinking || !isHumanPlayer(state.turn)) {
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

function populatePlayerSelect(select, agents, defaultValue) {
  select.innerHTML = "";
  const humanOption = document.createElement("option");
  humanOption.value = HUMAN;
  humanOption.textContent = "Human";
  select.appendChild(humanOption);

  for (const agent of agents) {
    const option = document.createElement("option");
    option.value = agent.spec;
    option.textContent = agent.label;
    option.title = agent.description;
    select.appendChild(option);
  }

  select.value = defaultValue;
}

async function loadAgents() {
  const response = await fetch("/api/agents");
  const payload = await response.json();
  populatePlayerSelect(blackPlayerSelect, payload.agents, HUMAN);
  populatePlayerSelect(whitePlayerSelect, payload.agents, "minizero:test");
}

function handleControllerChange() {
  invalidateAiRequest();
  state.hoverMove = null;
  setStatusForTurn();
  drawBoard();
  scheduleTurn(120);
}

function swapPlayers() {
  const blackValue = blackPlayerSelect.value;
  blackPlayerSelect.value = whitePlayerSelect.value;
  whitePlayerSelect.value = blackValue;
  handleControllerChange();
}

canvas.addEventListener("click", handleBoardClick);
canvas.addEventListener("pointermove", handleBoardPointerMove);
canvas.addEventListener("pointerleave", clearHoverMove);
newGameButton.addEventListener("click", () => newGame(true));
pauseButton.addEventListener("click", togglePause);
undoButton.addEventListener("click", undoRound);
swapPlayersButton.addEventListener("click", swapPlayers);
boardSizeSelect.addEventListener("change", () => newGame(true));
blackPlayerSelect.addEventListener("change", handleControllerChange);
whitePlayerSelect.addEventListener("change", handleControllerChange);
window.addEventListener("resize", resizeCanvas);

loadAgents()
  .then(() => {
    newGame(false);
  })
  .catch((error) => {
    statusText.textContent = `Could not load agents: ${error.message}`;
  });
