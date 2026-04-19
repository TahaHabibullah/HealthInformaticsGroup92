## How to Run

### Back End

1. Install dependencies:
   pip install -r requirements.txt

2. Run:
   (This step must be run once before starting the app):
   command: python rag.py

3. Start backend:
   command: uvicorn main:app --reload

4. Open:
   http://127.0.0.1:8000

### Front End

1. Navigate to nextjs folder
   cd nextjs

2. Install dependencies
   npm install

3. Run front end
   npm run dev

4. Open:
   http://127.0.0.1:3000

## Features
- LLM Model uses RAG documents to give analysis on possible conditions based on user symptoms
- Next.js + Material UI Front End
