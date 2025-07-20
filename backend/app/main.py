from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from stockfish import Stockfish

app = FastAPI()

stockfish = Stockfish(path="./stockfish/stockfish")

class PlayRequest(BaseModel):
    fen: str
    user_move: str

@app.get("/move")
def get_best_move(fen: str = Query(..., description="FEN position before the user move")):
    stockfish.set_fen_position(fen)
    return {"best_move": stockfish.get_best_move()}

@app.get("/evaluate")
def evaluate_position(fen: str = Query(..., description="FEN string representing the position")):
    stockfish.set_fen_position(fen)
    evaluation = stockfish.get_evaluation()
    print(evaluation)
    if evaluation["type"] == "cp":
        score = round(evaluation["value"] / 100, 2)
        return JSONResponse(content={"evaluation": f"{score}"})
    elif evaluation["type"] == "mate":
        return JSONResponse(content={"evaluation": f"Mate in {evaluation['value']}"})
    else:
        return JSONResponse(content={"error": "Unknown evaluation type"}, status_code=500)
    
@app.get("/feedback")
def get_feedback(
    fen: str = Query(..., description="FEN position before the user move"),
    user_move: str = Query(..., description="User move in UCI format (e.g., e2e4)")
):
    # Set the initial position
    stockfish.set_fen_position(fen)

    # Get Stockfish's best move from this position
    best_move = stockfish.get_best_move()

    # Evaluate the position *before* the move
    base_eval = stockfish.get_evaluation()

    # Apply user move
    if not stockfish.is_move_correct(user_move):
        return JSONResponse(content={"error": "Illegal move"}, status_code=400)

    stockfish.make_moves_from_current_position([user_move])
    user_eval = stockfish.get_evaluation()

    # Revert back for safety (optional but clean)
    stockfish.set_fen_position(fen) # MAYBE ILL CHANGE THIS IN THE FUTURE

    def get_score(eval):
        if eval["type"] == "cp":
            return eval["value"]
        elif eval["type"] == "mate":
            return 10000 if eval["value"] > 0 else -10000
        else:
            return 0

    base_score = get_score(base_eval)
    user_score = get_score(user_eval)
    delta = user_score - base_score

    # Interpretation
    diff = abs(delta)
    if diff <= 20:
        verdict = "Excellent"
    elif diff <= 50:
        verdict = "Good"
    elif diff <= 150:
        verdict = "Inaccuracy"
    elif diff <= 300:
        verdict = "Mistake"
    else:
        verdict = "Blunder"

    return {
        "base_score": get_score(base_eval),
        "user_score":get_score(user_eval),
        "best_move": best_move,
        "user_move": user_move,
        "score_diff": round(delta / 100, 2),
        "feedback": verdict
    }

@app.post("/play")
def play_move(data: PlayRequest):
    # Set up position
    if not stockfish.is_fen_valid(data.fen):
        raise HTTPException(status_code=400, detail="Invalid FEN")

    stockfish.set_fen_position(data.fen)

    # Make user's move
    if not stockfish.is_move_correct(data.user_move):
        raise HTTPException(status_code=400, detail="Invalid user move")

    stockfish.make_moves_from_current_position([data.user_move])

    # Engine's move
    engine_move = stockfish.get_best_move()
    if engine_move is None:
        return {
            "user_move": data.user_move,
            "engine_move": None,
            "message": "Game over or no legal move.",
            "updated_fen": stockfish.get_fen_position()
        }

    stockfish.make_moves_from_current_position([engine_move])

    return {
        "user_move": data.user_move,
        "engine_move": engine_move,
        "updated_fen": stockfish.get_fen_position()
    }