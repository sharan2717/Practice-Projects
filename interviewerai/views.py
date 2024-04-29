from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import os
import requests
import json
from django.conf import settings
from interviewerai.models import Match  # Import your Match model
from dataclasses import asdict
import google.generativeai as genai
from interviewerai.prompt import QA_prompt, ResumeMatch_prompt, AnswerMatch_prompt

API_URL = settings.API_URL
HEADERS = settings.HEADERS
GOOGLE_API_KEY = settings.GOOGLE_API_KEY


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

@csrf_exempt
def calculate_matching_score_route(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        answers_generated = data.get('Actual_answer')
        summary = data.get('Candidate_answer')
        
        matching_score = calculate_matching_score(answers_generated, summary)
        
        return JsonResponse({'matching_score': matching_score}, status=200)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

def calculate_matching_score(answers_generated, summary):
    try:
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history=[])
        response = chat.send_message(answers_generated)
        response = chat.send_message(summary)
        response = chat.send_message(AnswerMatch_prompt())
        output = response.text
    except genai.types.generation_types.StopCandidateException as e:
        print("Generation stopped:", e)
        return None
    return output

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
        prompt = QA_prompt(question, candidate_response)
        response = model.generate_content(prompt)
        match_results = response.parts[0].text
        
        return match_results
    except Exception as e:
        return JsonResponse({"error": str(e)})