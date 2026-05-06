import pdfplumber
from google import genai
from google.genai import types
from json_to_qti import convert
text = ""
with pdfplumber.open("Asher Lev Test (C) - Google Docs.pdf") as pdf:
    for page in pdf.pages:
        text += page.extract_text() + "\n"

client = genai.Client(api_key="AIzaSyCEc4hZrMP6mgUjwho0qu3Qth0ZxlfK2uk")

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
print(response.text)

convert(response.text, output_zip="canvas_quiz.zip", quiz_title="Quiz")






