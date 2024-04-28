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
    return ""

def AnswerMatch_prompt():
    prompt="""
    Your are going to access a candidate answer ,so Compare the question and Candidate_answer and give the relevancy score for them.Strictly give response in the mentioned JSON format
Instructions:
1. Provide the relevancy score in percentage
2. Explain the relevancy of two paragraphs
JSON Response Format:
{{
"Relevancy score": "",
"Comparison": ""
}}  """
    return prompt

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