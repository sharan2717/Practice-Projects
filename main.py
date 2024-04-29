from dataclasses import asdict
from xml.dom.minidom import Document
from fastapi import FastAPI, File, BackgroundTasks, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from pydantic import BaseModel
import os
import requests
import json
from typing import List
import google.generativeai as genai
import prompt as p
import Candidate as Candidate
from threading import Thread
from pymongo import MongoClient
from gridfs import GridFS
import markdown
from PyPDF2 import PdfReader
# from docx import Document

app = FastAPI()

mongo_uri = "mongodb://localhost:27017/Avengers"
client = MongoClient(mongo_uri)
db = client['Avengers']
collection = db['Candidates']
fs = GridFS(db)

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


model = genai.GenerativeModel('models/gemini-1.0-pro-001')

def extract_text(file_path):
    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension.lower() == '.docx':
        return extract_text_from_doc(file_path)
    else:
        return "Unsupported file format"

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_doc(docx_path):
    doc = Document(docx_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text

def preprocess_text(text):
    return text

def summarize_text_with_gemini(text, prompt):
    response = model.generate_content(f"{prompt}\n{text}")
    summary = response.parts[0].text
    return summary

def assess_alignment_with_gemini(res_summary, jd_summary, prompt):
    response = model.generate_content(f"{prompt}\nResume summary: {res_summary}\nJob description summary: {jd_summary}, Provide a matching score after comparing both the summaries . The format of the result should have a topic named Matching score,Matched skills,Non matched skills,Expertise Level,Overview,Final Conclusion by valaditing Matching score out of 100,Give OverView about matching and non matching skills , And if they are an experienced candidate give them an expertise level based on the analysis of their skills (Beginner, Intermediate, Advanced)")
    matching_score_analysis = response.parts[0].text
    return matching_score_analysis
def insert_mongodb(candidate: dict):
    try:
        result = collection.insert_one(asdict(candidate))
        return result.inserted_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error from db: {e}")

@app.post("/")
async def process_resume(resume: UploadFile = File(...), jd: UploadFile = File(...)):
    try:
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)

        resume_path = os.path.join(uploads_dir, resume.filename)
        jd_path = os.path.join(uploads_dir, jd.filename)

        with open(resume_path, "wb") as resume_file:
            resume_file.write(await resume.read())

        with open(jd_path, "wb") as jd_file:
            jd_file.write(await jd.read())

        resume_text = extract_text(resume_path)
        jd_text = extract_text(jd_path)
        
        resume_text = preprocess_text(resume_text)
        jd_text = preprocess_text(jd_text)
        
        resume_prompt = "Create a summary of the provided resume text that highlights the Candidate Name, educational qualifications, technical skills, and experience in organizations of the candidate. Give a single paragraph summarizing the required fields so that it can be used to match a job description. Here is the text:"
        jd_prompt = "Give a detailed summary of the provided job description text that highlights the requirements for the specific position. Provide a single paragraph summary of the required skills for the job that can be matched with the candidate's resume summary. Here is the text:"
        match_prompt = """I have provided a job description and a resume summary. I need you to match the semantic context of both 
        the summaries highlighting the candidate's skills and Job description requirements. Keep a strict matching score such that if 
        the requirements match less than the score should be less.
        structure the JSON response with everything as follows:
            {
            "Given_Resume_Summary":"",
            "Given_Jd_Summary":"",
            "candidate_name": "",
            "position_applied_for": "",
            "matching_score": "",
            "matched_skills": [
                "",
                "",
            ],
            "non_matched_skills": [
                "",
                "",
                
            ],
            "expertise_level": "",
            "overview": "",
            "final_conclusion":""}
        
        """
        
        resume_summary = summarize_text_with_gemini(resume_text, resume_prompt)
        jd_summary = summarize_text_with_gemini(jd_text, jd_prompt)
        
        matching_score_analysis = assess_alignment_with_gemini(resume_summary, jd_summary, match_prompt)
        json_data = json.loads(matching_score_analysis)
       
        # candidate = Candidate.Candidate(
        #     candidate_name=json_data["candidate_name"],
        #     position_applied_for=json_data["position_applied_for"],
        #     jd_summary=markdown.markdown(json_data["Given_Jd_Summary"]),
        #     resume_summary=markdown.markdown(json_data["Given_Resume_Summary"]),
        #     matching_score=json_data["matching_score"],
        #     matched_skills=json_data["matched_skills"],
        #     non_matched_skills=json_data["non_matched_skills"],
        #     overview=json_data["overview"],
        #     final_conclusion=json_data["final_conclusion"],
        #     expertise_level=json_data["expertise_level"],
        # )
        
        # mongo_id = insert_mongodb(candidate)
        # candidate.mongo_id = str(mongo_id)
        # return JSONResponse(content={'data': candidate})
        return json_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
