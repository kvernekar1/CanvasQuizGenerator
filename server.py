from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from json_to_qti import convert
from dotenv import load_dotenv
import uuid
import tempfile
import pdfplumber
import os

load_dotenv()
app = FastAPI()

task_results = {}

def _run_conversion(task_id: str, file_path: str):
    """Background task: convert PDF/DOCX to QTI ZIP"""
    try:
        with open(file_path, 'rb') as f:
            text = ""
            with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as tmp:
                tmp.write(f.read())
                tmp_path = tmp.name
        
        try:
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        finally:
            os.unlink(tmp_path)
        
        json_str = convertToJson(text)
        outputfile = convert(json_str, output_zip=f"canvas_quiz_{task_id}.zip", quiz_title="Quiz")
        
        task_results[task_id] = {"status": "complete", "file": outputfile, "error": None}
    except Exception as e:
        task_results[task_id] = {"status": "error", "file": None, "error": str(e)}
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)


@app.post("/convert")
def convertToQTI(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Accept file and start background conversion, return task ID immediately"""
    task_id = str(uuid.uuid4())
    
    with tempfile.NamedTemporaryFile(delete=False, suffix="") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    
    task_results[task_id] = {"status": "processing", "file": None, "error": None}
    background_tasks.add_task(_run_conversion, task_id, tmp_path)
    
    return {"task_id": task_id, "status": "processing"}


@app.get("/result/{task_id}")
def get_result(task_id: str):
    """Poll for conversion result or download the ZIP"""
    if task_id not in task_results:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    
    result = task_results[task_id]
    
    if result["status"] == "processing":
        return JSONResponse({"status": "processing", "message": "Conversion in progress..."})
    elif result["status"] == "error":
        return JSONResponse({"status": "error", "error": result["error"]}, status_code=500)
    else:
        return FileResponse(result["file"], media_type="application/zip", filename="canvas_quiz.zip")


def convertToJson(text):
    client = genai.Client(api_key=os.environ.get("API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction="You are excellent at converting quizzes into JSON. Respond only in JSON format, and do not try to format it with backticks. The brackets must be first."
        ),
        contents=f"""
        Can you please convert the following test I have into a JSON object with questions in it?
        It will contain multiple-choice questions, free-response questions, matching questions, and true/false questions.
        Please format the JSON like this:
        {{
          "questions": [
            {{
              "type": "mcq",
              "question": "Question text here",
              "choices": ["choice A", "choice B", "choice C", "choice D"],
              "answer": "correct choice letter (e.g., 'A')"
            }},
            {{
              "type": "free_response",
              "question": "Question text here",
              "answer": "blank"
            }},
            {{
              "type": "matching",
              "question": "Instructions for matching here",
              "pairs": [
                {{"left": "Left item", "right": "Right item"}}
              ]
            }},
            {{
              "type": "true_false",
              "question": "Question text here",
              "answer": "true or false"
            }}
          ]
        }}

        Here is a small example:
        {{
          "questions": [
            {{
              "type": "mcq",
              "question": "What is 2+2?",
              "choices": ["3", "4", "5", "6"],
              "answer": "B"
            }},
            {{
              "type": "free_response",
              "question": "Explain the process of photosynthesis.",
              "answer": ""
            }},
            {{
              "type": "matching",
              "question": "Match the following countries with their capitals.",
              "pairs": [
                {{"left": "France", "right": "Paris"}},
                {{"left": "Italy", "right": "Rome"}}
              ]
            }},
            {{
              "type": "true_false",
              "question": "The Earth is flat.",
              "answer": "false"
            }}
          ]
        }}
        Please use whatever is provided in the text WORD-FOR-WORD when generating the JSON. DO NOT PARAPHRASE.
        Here is the test:
        {text}

        Thank you!
        """,
    )
    return response.text


app.mount("/", StaticFiles(directory=".", html=True), name="static")
