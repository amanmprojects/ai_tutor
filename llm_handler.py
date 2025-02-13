from groq import Groq
from config import GROQ_API_KEY
import json

class LLMHandler:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "mixtral-8x7b-32768"  # Using Mixtral as it's more reliable for structured output

    def generate_quiz(self, topic: str, difficulty: float) -> list:
        difficulty_level = "beginner" if difficulty < 0.3 else "intermediate" if difficulty < 0.7 else "advanced"
        prompt = f"""Generate a quiz about {topic} at {difficulty_level} level. 
        Create 3 multiple-choice questions. The response must be a valid JSON array of dictionaries.
        Each dictionary must have exactly these keys:
        - 'question': string with the question text
        - 'options': array of 4 strings with possible answers
        - 'correct_answer': integer 0-3 indicating the index of the correct answer
        
        Example format:
        [
            {{"question": "What is Python?", 
             "options": ["Programming language", "Snake", "Movie", "Book"],
             "correct_answer": 0}}
        ]"""
        
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
            )
            
            # Try to parse as JSON first
            try:
                quiz_data = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the text
                content = response.choices[0].message.content
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                if start_idx != -1 and end_idx != 0:
                    quiz_data = json.loads(content[start_idx:end_idx])
                else:
                    return []
            
            # Validate the structure
            if not isinstance(quiz_data, list):
                return []
            
            for q in quiz_data:
                if not all(k in q for k in ['question', 'options', 'correct_answer']):
                    return []
                if not isinstance(q['options'], list) or len(q['options']) != 4:
                    return []
                if not isinstance(q['correct_answer'], int) or q['correct_answer'] not in range(4):
                    return []
            
            return quiz_data
        except Exception as e:
            print(f"Quiz generation error: {str(e)}")
            return []

    def get_topic_recommendations(self, past_topics: list) -> list:
        topics_str = ", ".join(past_topics)
        prompt = f"""Based on the user's past learning topics: {topics_str}, 
        suggest 3 related topics they might be interested in. 
        Return just the list of topics, one per line."""
        
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
            )
            
            recommendations = response.choices[0].message.content.strip().split('\n')
            return [r.strip() for r in recommendations if r.strip()]
        except Exception as e:
            print(f"Recommendation error: {str(e)}")
            return []

    def answer_question(self, topic: str, question: str) -> str:
        prompt = f"""As an AI tutor helping with {topic}, please answer this question: {question}
        Keep the answer concise but informative. If the question is not related to {topic}, 
        remind the user that we're currently studying {topic}."""
        
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Question answering error: {str(e)}")
            return "I'm having trouble processing your question. Please try again."