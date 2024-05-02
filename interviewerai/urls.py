from django.urls import path
from .views import matching_endpoint, whisper_ai, process_resume

urlpatterns = [
    path('whisperAI/', whisper_ai, name='whisper_ai'),
    # path('calculate_matching_score/', calculate_matching_score_route, name = 'calculate_matching_score_route'),
    path('matching/', matching_endpoint, name = 'matching_endpoint'),
    path('process/', process_resume, name = 'process_resume'),

]
