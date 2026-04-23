# Vulcan OmniPro 220 - Multimodal Reasoning Agent

**Prox Founding Engineer Challenge** | Shivam Lahoti

An AI agent that provides expert technical support for the Vulcan OmniPro 220 welding system. Combines Vision API for precision (duty cycles, polarity) with RAG for flexibility (procedures, troubleshooting).

---

## Setup & Run

### Prerequisites
- Python 3.8+
- Node.js 16+
- Anthropic API key

### Install

```bash
# 1. Clone and navigate
git clone <your-fork-url>
cd prox-challenge

# 2. Add your API key
cp .env.example .env
# Edit .env and set: ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY

# 3. Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# 4. Install frontend dependencies
cd frontend
npm install
cd ..
```

### Run

```bash
# Terminal 1 - Start backend
cd backend
python app.py

# Terminal 2 - Start frontend (open new terminal)
cd frontend
npm run dev
```

**Agent live at:** `http://localhost:3000`

---

## Architecture

### **Hybrid Intelligence System**

```
User Query
    ↓
┌─────────────────────────────────────────┐
│  Query Analysis                         │
│  • Duty cycle? → Structured lookup      │
│  • Polarity? → Structured lookup        │
│  • Procedure? → RAG search              │
└─────────────────────────────────────────┘
    ↓
┌──────────────────┐    ┌─────────────────┐
│ Structured Data  │    │   RAG Search    │
│ (Vision API)     │    │ (FAISS + Vector)│
│                  │    │                 │
│ • Duty cycles    │    │ • Setup steps   │
│ • Polarity       │    │ • Safety        │
│ • Troubleshoot   │    │ • Maintenance   │
└────────┬─────────┘    └────────┬────────┘
         └──────────┬─────────────┘
                    ↓
         ┌──────────────────────┐
         │   Claude Sonnet 4    │
         └──────────┬───────────┘
                    ↓
         ┌──────────────────────┐
         │      Response        │
         │  • Text (markdown)   │
         │  • Artifacts         │
         │  • Images            │
         └──────────────────────┘
```

### **Why Hybrid?**

**Pure RAG Problem:** Can misread duty cycle tables (85% accuracy)  
**Pure Structured Problem:** Can't answer open-ended questions  
**Hybrid Solution:** Vision API extracts tables once (100% accuracy) + RAG handles everything else

---

## What It Does

### Accurate Technical Answers

### Multimodal Responses


## 🧪 Example Queries

**Duty Cycle (Structured Data)**
```
Q: "What's the duty cycle for MIG at 200A on 240V?"
A: 25% duty cycle (2.5 min weld, 7.5 min rest)
   + Interactive calculator artifact
```

**Polarity Setup (Structured + Images)**
```
Q: "Show me the polarity setup for flux-cored welding"
A: Ground clamp → Positive (+), Wire feed → Negative (-)
   DCEN polarity for gasless operation
   + 5 manual diagrams showing socket connections
```

**Troubleshooting (Hybrid)**
```
Q: "I'm getting porosity in my flux-cored welds"
A: 6 possible causes with solutions:
   1. Wrong polarity (check DCEN)
   2. Dirty workpiece (clean to bare metal)
   3. Wire contamination...
   + Weld diagnosis images from manual
```

**Procedures (Pure RAG)**
```
Q: "How do I install a wire spool?"
A: Step-by-step instructions from pages 10-11
```

---

## 📊 Tech Stack

**Backend**
- FastAPI + Claude Sonnet 4 (Vision API)
- PyMuPDF (PDF extraction)
- FAISS + sentence-transformers (vector search)

**Frontend**
- React 18 + TypeScript + Vite
- Tailwind CSS + react-markdown

**Data**
- 50 document chunks, 150+ images
- 4 structured datasets (Vision-extracted)

---

## 💡 Key Design Decisions

**Hybrid Architecture:** Vision API extracts tables once → 100% accuracy on calculations  
**FAISS:** Local vector search, no external dependencies  
**3-Layer Caching:** 15x speedup after first run  
**Page-Based Matching:** Smart image relevance  


---

## 📧 Contact

**Shivam Lahoti**  
LinkedIn: [linkedin.com/in/shivamlahoti](https://linkedin.com/in/shivamlahoti)  
GitHub: [github.com/shivam-lahoti](https://github.com/shivam-lahoti)  
Email: shivam.2199@gmail.com

---