def QA_prompt(question, candidate_response):
    prompt=f"""**Generate a response indicating how well the candidate's response matches the question, with a score (0-100) reflecting conceptual similarity.**
                
                **Question:** {question}
                **Candidate Response:** {candidate_response}
                
                **Analysis:**
                
                * Identify key concepts and entities in the question. 
                * Analyze the candidate response for relevance to these concepts. 
                * Calculate a conceptual matching score (0-100) based on the overlap between question concepts and the candidate's response.  
                **Response:**
                
                * **Qamatching_score:** score  (This will be populated by the calculated score,relvant score according to match)
                * **Whats_Wrong:** (Provide a brief explanation of why the score was given, highlighting strengths and weaknesses in the candidate's response. Optionally, suggest improvements) 
                * **Match_level:** score  (Too Poor,Poor,Average,Excellant,Best)
                
                Format the result in the following JSON format:
               {{
                "Qamatching_score": "",
                "Whats_Wrong": "",
                "Match_level": ""
                }}""
                """
    return prompt

def ResumeMatch_prompt():
    prompt="""I have provided a job description and a resume summary. I need you to match the semantic context of both 
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

    return prompt

def AnswerMatch_prompt():
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
    return resume_prompt, jd_prompt, match_prompt

def question_generation_prompt(topic,number_of_questions,experience_level):
    prompt = f"""
As an AI assistant specializing in technical interviews, I am tasked with generating interview questions for a software engineering role. The interview will 
focus on the following:

* **Skill:** {topic}
* **Number of Questions:** {number_of_questions}
* **Experience Level:** {experience_level}

Please generate a set of {number_of_questions} scenario-based and theoretical questions that assess the candidate's proficiency in {topic} at a {experience_level} level, focusing on theoretical understanding and problem-solving approaches. 

**For each question, provide the following:**

* **Question:** A clear and concise scenario based question that tests the candidate's theoretical knowledge and problem-solving skills in {topic}, without requiring code implementation.
* **Answer:** A detailed explanation of the expected answer, focusing on concepts, principles, and decision-making processes, rather than code syntax or specific libraries.

**Additional Considerations:**

* Ensure the questions cover a variety of theoretical topics within {topic} relevant to the {experience_level} level.
* Encourage critical thinking and problem-solving skills through scenario-based questions that can be tackled without coding.
* Maintain a clear and professional tone throughout the questions and answers.

**Example Output Format (JSON):**

```json
{{
  "topic": "skill",
  "questions": [
    {{
      "question_no": 1,
      "question": "[Question 1]",
      "answer": "[Answer 1]"
    }},
    {{
      "question_no": 2,
      "question": "[Question 2]",
      "answer": "[Answer 2]"
    }},
    ... (and so on for all number of questions)
  ]
}}

"""
    return prompt