# GNN Brain

**Ask a school question and watch it travel through the network.** GNN Brain combines an interactive graph, source-backed node chat, and a small graph-convolution model that routes subject questions.

The fictional school has **207 nodes**, **226 links**, and **34 searchable example questions**. Five classes of 35 students are connected through class representatives, subject in-charges, department heads, the Dean, and the Director.

## Quick start

Requires Python 3.10+ and Node.js 20.19+ on the 20.x line, or 22.12+. Clone the public repository:

```sh
git clone https://github.com/bsaiteja0714/GNN-brain.git
cd GNN-brain
```

Start the FastAPI backend on **port 8000**.

<details open>
<summary>Windows PowerShell</summary>

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r gnn-brain-backend\requirements.txt
Set-Location gnn-brain-backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

</details>

<details>
<summary>macOS or Linux</summary>

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r gnn-brain-backend/requirements.txt
cd gnn-brain-backend
../.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

</details>

In a second terminal, from the repository root, start the React frontend:

```sh
cd gnn-brain-ui
npm ci
npm run dev -- --host 127.0.0.1
```

Open [the app](http://127.0.0.1:5173/) or [the API docs](http://127.0.0.1:8000/docs). Node chat and the message-passing example work without a provider key.

## Try the school graph

Select a student and ask **“When is Founders Day?”** The question travels through the class representative, an in-charge, and a department head to the Dean. The reply appears in chat while the graph animates its return. Use **Replay path** to revisit the route.

| Try asking | Source |
| --- | --- |
| What are you working on? | Selected student or class representative |
| Where is our morning assembly? | Class representative |
| When is the maths assignment due? | Maths in-charge |
| When is the coding workshop? | Computing HOD |
| How do I borrow or renew a library book? | Dean |
| What should I do if I lost my student ID? | Director |

Use **Question library** to browse more examples. Search for a node by name or role, drag nodes to explore connections, and use **Fit graph** to reset the view. The graph menu also includes a standalone mean-aggregation example.

## How routing works

Each node checks its own records before passing the question onward. At a class representative’s subject branch, the model aggregates neighboring HOD signals and ranks the available in-charges. General school questions start on the Science branch. If a relevant published record is reachable outside the upward chain, the app can consult its owner within the class or school-wide scope. Answers cite their demo record, and unrecognized questions return an unresolved result.

The frontend uses React, TypeScript, Vite, and a D3 force layout rendered on Canvas. The backend uses FastAPI, NetworkX, and NumPy. The [school graph](gnn-brain-backend/app/graph/data.py), [knowledge records](gnn-brain-backend/app/graph/knowledge.py), and [routing model](gnn-brain-backend/app/graph/gnn_model.py) are separate so they can be inspected independently.

## Optional graph assistant

Open the plug icon and choose **OpenAI**, **Groq**, or **Google AI Studio (Gemini)**. Enter your API key and a model that supports JSON output. The assistant can explain the active graph, show a valid example path, or propose a graph edit for you to review and apply. Custom graphs are saved in the browser.

Verification sends a short test message. Assistant requests send the active graph, the question, and recent chat to your selected provider through the local backend. For the demo school, this includes fictional public records and the selected student’s demo profile. Your key stays in the open tab’s memory. [Get a Gemini API key](https://aistudio.google.com/api-keys)

## Checks

```sh
# From gnn-brain-backend, with the virtual environment active
python -m unittest discover -s tests

# From gnn-brain-ui
npm run lint
npm run build
```

## Demo data

School names, schedules, policies, and student profiles are fictional. Scenario ideas came from published guidance on library use, missed assessments, trips, and exams. [Bradford High School](https://www.kusd.edu/bradford/information/practices-procedures/) · [Pottsgrove School District](https://www.pgsd.org/resources/parent-resources/pgms-student-handbook) · [Rankin County School District](https://www.rcsd.ms/parents/student-handbook) · [CBSE](https://www.cbse.gov.in/cbsenew/Examination_Circular.html)
