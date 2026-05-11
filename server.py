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
import threading
import os

load_dotenv()
app = FastAPI()
count = 0
lock = threading.Lock()
task_results = {}

def _run_conversion(task_id: str, file_path: str):
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
    task_id = str(uuid.uuid4())
    
    with tempfile.NamedTemporaryFile(delete=False, suffix="") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    
    task_results[task_id] = {"status": "processing", "file": None, "error": None}
    background_tasks.add_task(_run_conversion, task_id, tmp_path)
    
    return {"task_id": task_id, "status": "processing"}


@app.get("/result/{task_id}")
def get_result(task_id: str):
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
    global count
    with lock:
        key = count % 2 == 0
        count += 1
    api = os.environ.get("API_KEY" if key else "API_KEY2")
    client = genai.Client(api_key=api)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction="""You are a deterministic quiz-to-JSON conversion engine.

            You must respond only with valid JSON.

            Do not include explanations, markdown, backticks, code blocks, or any extra text.

            The output must:

            Start with a single {
            Be valid JSON
            Use double quotes only
            Contain no trailing commas
            Be parseable by a standard JSON parser
            Not contain comments
            Not contain additional keys outside the required structure

            Do not infer, guess, or modify content.

            Preserve all question text and answer choices exactly as written.

            If information is missing, use empty strings or empty arrays as appropriate.
            Never fabricate content.
            """),
        contents=f"""You are a deterministic JSON conversion engine.

        Your task is to convert the provided test into a single valid JSON object.

        CRITICAL RULES
        Output ONLY valid JSON.
        Do NOT include explanations, markdown, comments, or extra text.
        Do NOT wrap the output in code blocks.
        Use double quotes for all strings.
        Do NOT use trailing commas.
        The output must be parseable by a standard JSON parser.
        Do NOT infer, guess, or modify content.
        Use the test text EXACTLY as written (word-for-word).
        Do NOT paraphrase.
        If information is missing, leave fields empty — do not invent anything.

        REQUIRED OUTPUT STRUCTURE
        Return a JSON object that begins with a single opening brace.

        {{
        "questions": [...]
        }}

        Each question must follow one of the formats below exactly.

        Multiple Choice (mcq)

        {{
        "type": "mcq",
        "question": "exact question text",
        "choices": ["choice A", "choice B", "choice C", "choice D"],
        "answer": "correct choice letter"
        }}

        Rules:

        Choices must appear in the order provided.
        Answer must be a single letter (A, B, C, etc.).
        Only use an answer if it is explicitly provided in the test.
        Free Response (free_response)

        {{
        "type": "free_response",
        "question": "exact question text",
        "answer": ""
        }}

        Rules:

        Always set answer to an empty string.
        Matching (matching)

        {{
        "type": "matching",
        "question": "exact instructions text",
        "pairs": [
        {{"left": "exact left item", "right": "exact right item"}}
        ]
        }}

        Rules:

        Preserve all text exactly.
        Do not reorder pairs.
        True/False (true_false)

        {{
        "type": "true_false",
        "question": "exact question text",
        "answer": "true"
        }}

        Rules:

        Answer must be exactly "true" or "false".
        Lowercase only.
        Additional Constraints
        Do not include any fields other than those specified.
        Do not add metadata.
        Do not add numbering unless it exists in the original text.
        Preserve formatting inside question text exactly.
        Now Convert the Following Test:

        {text}
        """,
    )
    newtext = response.text.replace("{{", "{").replace("}}", "}").replace("[[", "[").replace("]]", "]")
    newtext2 = newtext[newtext.find("{"): newtext.rfind("}") + 1]
    return newtext2


app.mount("/", StaticFiles(directory=".", html=True), name="static")
