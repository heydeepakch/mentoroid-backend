from typing import List, Dict, Any, Optional
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

# Load environment variables
load_dotenv()

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-4-turbo-preview"
EMBEDDING_MODEL = "text-embedding-3-small"

class AIHelper:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.model = DEFAULT_MODEL
    
    async def generate_course_outline(self, title: str, description: str) -> Dict[str, Any]:
        """
        Generate a structured course outline based on title and description.
        """
        prompt = f"""
        Create a detailed course outline for a course with the following details:
        Title: {title}
        Description: {description}
        
        The outline should include:
        1. Learning objectives
        2. Main topics (5-8)
        3. Subtopics for each main topic
        4. Suggested time allocation
        5. Recommended quiz points
        
        Format the response as a JSON object.
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert curriculum designer."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error generating course outline: {e}")
            return None
    
    async def generate_quiz_questions(
        self,
        topic: str,
        content: str,
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions based on course content.
        """
        prompt = f"""
        Generate {num_questions} quiz questions based on the following topic and content:
        Topic: {topic}
        Content: {content}
        
        For each question, provide:
        1. Question text
        2. Multiple choice options (4 options)
        3. Correct answer
        4. Explanation
        
        Format the response as a JSON array of question objects.
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert assessment creator."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error generating quiz questions: {e}")
            return None
    
    async def get_learning_recommendations(
        self,
        user_id: str,
        course_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get personalized learning recommendations based on user progress.
        """
        # Get user progress and course data
        progress = await self.db.user_progress.find_one({
            "user_id": user_id,
            "course_id": course_id
        })
        
        if not progress:
            return []
        
        # Get completed materials and quizzes
        completed_materials = progress.get("completed_materials", [])
        completed_quizzes = progress.get("completed_quizzes", [])
        
        # Get course materials and quizzes
        materials = await self.db.materials.find({
            "course_id": course_id,
            "_id": {"$nin": completed_materials}
        }).to_list(None)
        
        quizzes = await self.db.quizzes.find({
            "course_id": course_id,
            "_id": {"$nin": completed_quizzes}
        }).to_list(None)
        
        # Generate recommendations
        recommendations = []
        
        if materials:
            recommendations.append({
                "type": "material",
                "items": [
                    {
                        "id": str(material["_id"]),
                        "title": material["title"],
                        "priority": "high" if material.get("is_prerequisite") else "normal"
                    }
                    for material in materials[:3]
                ]
            })
        
        if quizzes:
            recommendations.append({
                "type": "quiz",
                "items": [
                    {
                        "id": str(quiz["_id"]),
                        "title": quiz["title"],
                        "difficulty": quiz.get("difficulty", "medium")
                    }
                    for quiz in quizzes[:2]
                ]
            })
        
        return recommendations
    
    async def analyze_quiz_performance(
        self,
        user_id: str,
        quiz_id: str
    ) -> Dict[str, Any]:
        """
        Analyze user's quiz performance and provide feedback.
        """
        submission = await self.db.quiz_submissions.find_one({
            "user_id": user_id,
            "quiz_id": quiz_id,
            "status": "completed"
        })
        
        if not submission:
            return None
        
        # Get quiz details
        quiz = await self.db.quizzes.find_one({"_id": quiz_id})
        if not quiz:
            return None
        
        # Analyze performance
        total_questions = len(submission["answers"])
        correct_answers = len([a for a in submission["answers"] if a["is_correct"]])
        performance_ratio = correct_answers / total_questions
        
        # Generate feedback
        prompt = f"""
        Analyze the following quiz performance and provide detailed feedback:
        Topic: {quiz["title"]}
        Score: {submission["total_score"]} / {submission["max_score"]}
        Correct Answers: {correct_answers} out of {total_questions}
        
        Provide:
        1. Overall performance assessment
        2. Areas of strength
        3. Areas for improvement
        4. Study recommendations
        
        Format the response as a JSON object.
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educational analyst."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis = json.loads(response.choices[0].message.content)
            analysis["performance_metrics"] = {
                "score": submission["total_score"],
                "max_score": submission["max_score"],
                "correct_answers": correct_answers,
                "total_questions": total_questions,
                "performance_ratio": performance_ratio
            }
            
            return analysis
        except Exception as e:
            print(f"Error analyzing quiz performance: {e}")
            return None
    
    async def get_content_summary(self, content: str) -> Dict[str, Any]:
        """
        Generate a concise summary of course content.
        """
        prompt = f"""
        Create a comprehensive summary of the following content:
        {content[:4000]}  # Limit content length
        
        Provide:
        1. Main points (3-5)
        2. Key concepts
        3. Brief summary (2-3 sentences)
        
        Format the response as a JSON object.
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert content summarizer."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error generating content summary: {e}")
            return None
    
    async def generate_study_plan(
        self,
        user_id: str,
        course_id: str,
        target_completion_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a personalized study plan based on user progress and goals.
        """
        # Get course and progress data
        course = await self.db.courses.find_one({"_id": course_id})
        progress = await self.db.user_progress.find_one({
            "user_id": user_id,
            "course_id": course_id
        })
        
        if not course or not progress:
            return None
        
        # Calculate remaining work
        remaining_materials = len(course.get("materials", [])) - len(progress.get("completed_materials", []))
        remaining_quizzes = len(course.get("quizzes", [])) - len(progress.get("completed_quizzes", []))
        
        prompt = f"""
        Create a personalized study plan with the following details:
        Course: {course["title"]}
        Progress: {progress["progress_percentage"]}%
        Remaining Materials: {remaining_materials}
        Remaining Quizzes: {remaining_quizzes}
        Target Completion: {target_completion_date.isoformat() if target_completion_date else "Not specified"}
        
        Include:
        1. Weekly schedule
        2. Time allocation per topic
        3. Milestones
        4. Study tips
        
        Format the response as a JSON object.
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert learning strategist."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error generating study plan: {e}")
            return None 