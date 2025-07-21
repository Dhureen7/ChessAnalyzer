
# ♟️ ChessAnalyzer

A personalized chess training tool that analyzes your games using Stockfish and gives targeted improvement advice to help you get better at chess.

## 🚀 Features

- ♟️ Upload PGN files or paste game notation
- 📊 Get analysis on inaccuracies, blunders, and missed tactics
- 🧠 Categorized mistake insights (forks, pins, missed mates, etc.)
- 🔁 Personalized feedback and training suggestions
- 💾 Stores analysis history with PostgreSQL
- ⚙️ Backend powered by FastAPI and Stockfish
- 🌐 Frontend built with React (Vite)

## 🧰 Tech Stack

- Frontend: React + Vite + Tailwind CSS
- Backend: FastAPI + Python
- Database: PostgreSQL + SQLAlchemy
- Engine: Stockfish 17.1
- Containerisation: Docker

## 📦 Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/Dhureen7/ChessAnalyzer.git
   cd ChessAnalyzer


2. **Start the backend**

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

3. **Start the frontend**

   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

4. **Make sure Stockfish binary is accessible to the backend.**

## 📂 Project Structure

```
ChessAnalyzer/
├── backend/
│   ├── app/
│   ├── stockfish/
│   ├── Dockerfile
│   ├── .gitignore
├── frontend/
│   ├── src/
│   ├── public/
│   ├── vite.config.js
│   └── ...
├── README.md
```

## ✅ TODO

* [ ] Enhance tactical classification model
* [ ] Export annotated PGNs
* [ ] Mobile responsiveness
