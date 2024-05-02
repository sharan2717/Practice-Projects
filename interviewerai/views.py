from http.client import HTTPException
from typing import Collection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import os
import requests
from PyPDF2 import PdfReader
from .models import Candidate
from xml.dom.minidom import Document
from pymongo import MongoClient
import json
from django.conf import settings
from interviewerai.models import Match  # Import your Match model
from dataclasses import asdict
import google.generativeai as genai
import interviewerai.prompt as p

API_URL = settings.API_URL
HEADERS = settings.HEADERS
GOOGLE_API_KEY = settings.GOOGLE_API_KEY


mongo_uri = "mongodb://localhost:27017/Avengers"
client = MongoClient(mongo_uri)
db = client['Avengers']
collection = db['Candidates']

@csrf_exempt
def whisper_ai(request, UPLOAD_FOLDER='audios/'):
    if request.method == 'POST':
        audio_file = request.FILES.get("audio_file")
        question_no = request.POST.get("question_no")
        candidate_name = request.POST.get("candidate_name")
        topic = request.POST.get("topic")

        # Create the 'audios' folder if it doesn't exist
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        if not audio_file:
            return JsonResponse({"error": "No audio file provided"}, status=400)

        filename = f"{candidate_name}_{topic}_{question_no}.wav"
        filename = filename.replace(" ", "")
        wav_file_path = os.path.join(UPLOAD_FOLDER, filename)

        with default_storage.open(wav_file_path, 'wb+') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)

        with open(wav_file_path, "rb") as f:
            data = f.read()

        response = requests.post(API_URL, headers=HEADERS, data=data)

        if not response.ok:
            return JsonResponse({"error": "Transcription failed"}, status=500)

        return JsonResponse(json.loads(response.content), safe=False)

    return JsonResponse({"error": "Method not allowed"}, status=405)

genai.configure(api_key=GOOGLE_API_KEY)

# @csrf_exempt
# def calculate_matching_score_route(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         answers_generated = data.get('Actual_answer')
#         summary = data.get('Candidate_answer')
        
#         matching_score = calculate_matching_score(answers_generated, summary)
        
#         return JsonResponse({'matching_score': matching_score}, status=200)
#     else:
#         return JsonResponse({"error": "Method not allowed"}, status=405)

# def calculate_matching_score(answers_generated, summary):
#     try:
#         model = genai.GenerativeModel('gemini-pro')
#         chat = model.start_chat(history=[])
#         response = chat.send_message(answers_generated)
#         response = chat.send_message(summary)
#         response = chat.send_message(AnswerMatch_prompt())
#         output = response.text
#     except genai.types.generation_types.StopCandidateException as e:
#         print("Generation stopped:", e)
#         return None
#     return output

@csrf_exempt
def matching_endpoint(request):
    if request.method == 'POST':
        try:
            question = request.POST.get("question")
            candidate_response = request.POST.get("candidate_answer")
            match_results = matching(question, candidate_response)
            json_data = json.loads(match_results)
            
            match_response = Match(
                matching_score=json_data["Qamatching_score"],
                whats_Wrong=json_data["Whats_Wrong"],
                match_level=json_data["Match_level"],
            )
            match_response_dict = asdict(match_response)
            
            return JsonResponse({'data': match_response_dict})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

def matching(question, candidate_response):
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = p.QA_prompt(question, candidate_response)
        response = model.generate_content(prompt)
        match_results = response.parts[0].text
        
        return match_results
    except Exception as e:
        return JsonResponse({"error": str(e)})



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
        result = Collection.insert_one(asdict(candidate))
        return result.inserted_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error from db: {e}")

@csrf_exempt
def process_resume(request):
    if request.method == 'POST':
        try:
            uploads_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)

            resume_file = request.FILES.get('resume')
            jd_file = request.FILES.get('jd')

            resume_path = os.path.join(uploads_dir, resume_file.name)
            jd_path = os.path.join(uploads_dir, jd_file.name)

            with open(resume_path, 'wb') as resume:
                for chunk in resume_file.chunks():
                    resume.write(chunk)

            with open(jd_path, 'wb') as jd:
                for chunk in jd_file.chunks():
                    jd.write(chunk)

            resume_text = extract_text(resume_path)
            jd_text = extract_text(jd_path)

            resume_text = preprocess_text(resume_text)
            jd_text = preprocess_text(jd_text)

            resume_prompt = p.resume_prompt()
            jd_prompt = p.jd_prompt()
            match_prompt = p.match_prompt()

            resume_summary = summarize_text_with_gemini(resume_text, resume_prompt)
            jd_summary = summarize_text_with_gemini(jd_text, jd_prompt)

            matching_score_analysis = assess_alignment_with_gemini(resume_summary, jd_summary, match_prompt)
            json_data = json.loads(matching_score_analysis)

            # candidate = Candidate(
            #     candidate_name=json_data["candidate_name"],
            #     position_applied_for=json_data["position_applied_for"],
            #     jd_summary=json_data["Given_Jd_Summary"],
            #     resume_summary=json_data["Given_Resume_Summary"],
            #     matching_score=json_data["matching_score"],
            #     matched_skills=json_data["matched_skills"],
            #     non_matched_skills=json_data["non_matched_skills"],
            #     overview=json_data["overview"],
            #     final_conclusion=json_data["final_conclusion"],
            #     expertise_level=json_data["expertise_level"],
            # )

            # result = collection.insert_one(candidate.to_mongo())
            # candidate.mongo_id = str(result.inserted_id)
            # return JsonResponse({'data': candidate})
            return JsonResponse(json_data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)
