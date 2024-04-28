from fastapi import FastAPI, File, BackgroundTasks, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import json
import google.generativeai as genai
import prompt as p
from threading import Thread

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

# CORS (Cross-Origin Resource Sharing) middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allowing all origins, you should adjust this in production
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

with open("config.json", "r") as config_file:
    config = json.load(config_file)
    WHISPER_AI_API_URL = config.get("API_URL")
    GOOGLE_API_KEY = config.get("GOOGLE_API_KEY")
    headers = config.get("headers")

    
UPLOAD_FOLDER = 'audios'

@app.post("/whisperAI")
async def transc(audio_file: UploadFile = File(...),
                 question_no: str = Form(...),
                 candidate_name: str = Form(...),
                 topic: str = Form(...)):
    print("API called")

    if not audio_file:
        raise HTTPException(status_code=400, detail="No selected file")

    filename = f"{candidate_name.strip()}{topic.strip()}{question_no.strip()}.wav"
    wav_file_path = os.path.join(UPLOAD_FOLDER, filename)

    try:
        os.makedirs(os.path.dirname(wav_file_path), exist_ok=True)
        with open(wav_file_path, "wb") as f:
            f.write(await audio_file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    print("wav path:", wav_file_path)

    try:
        with open(wav_file_path, "rb") as f:
            data = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

    # Assuming API_URL and headers are defined elsewhere
    response = requests.post(WHISPER_AI_API_URL, headers=headers, data=data)
    response_json = response.json()

    print(response_json)
    return response_json

genai.configure(api_key=GOOGLE_API_KEY)
@app.post('/calculate_matching_score')
async def calculate_matching_score_route(Actual_answer: str = Form(...), Candidate_answer: str = Form(...)):
    try:
        matching_score = calculate_matching_score(Actual_answer, Candidate_answer)
        return {'matching_score': matching_score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def calculate_matching_score(answers_generated, candiadate_ans):
    try:
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history=[])
        response = chat.send_message(answers_generated)
        response = chat.send_message(candiadate_ans)
        prompt= p.AnswerMatch_prompt()
        response = chat.send_message(prompt)
        output = response.text
    except genai.types.generation_types.StopCandidateException as e:
        print("Generation stopped:", e)
        raise HTTPException(status_code=500, detail="Generation stopped")
    return output


@app.post('/matching')
async def matching_endpoint(question: str = Form(...), candidate_answer: str = Form(...)):
    try:
        match_results = matching(question, candidate_answer)
        match_response = json.loads(match_results)
        return {'data': match_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def matching(question, candidate_response):
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = p.QA_prompt(question=question, candidate_response=candidate_response)
        response = model.generate_content(prompt)
        match_results = response.parts[0].text
        return match_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
model = genai.GenerativeModel('gemini-pro')
def generate_questions(Topic,Experience,No_of_questions):
    oprompt=p.question_generation_prompt(Topic,No_of_questions,Experience)
    print(oprompt)
    response = model.generate_content(oprompt)
    interview_questions = response.text
    print(interview_questions)

    start_index = interview_questions.find('{')
    end_index = interview_questions.rfind('}') + 1
    json_str = interview_questions[start_index:end_index]
    return json_str


@app.get('/generate-interview-questions')
async def get_questions(topic: str, experience: str, no_of_questions: int, background_tasks: BackgroundTasks):
        
    background_tasks.add_task(generate_questions, topic, experience, no_of_questions)
    return generate_questions(topic, experience, no_of_questions), 200
    
