from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from json_to_qti import convert
import pdfplumber
import os

app = FastAPI()

@app.post("/convert")
def convertToQTI(file: UploadFile = File(...)):
    text = ""
    with pdfplumber.open(file.file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    json_str = convertToJson(text)
    outputfile = convert(json_str, output_zip="canvas_quiz.zip", quiz_title="Quiz")
    return FileResponse(outputfile, media_type="application/zip", filename="canvas_quiz.zip")

def convertToJson(text):
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY", ""))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction="You are excellent at converting quizzes into JSON. Respond only in JSON format, and do not try to format it with backticks. The brackets must be first."),
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
        """
    )
    return response.text

app.mount("/", StaticFiles(directory=".", html=True), name="static")
