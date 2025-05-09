# AI-Powered Learning Management System

An intelligent learning management system that leverages AI to provide personalized learning experiences for students.

## Features

- User Authentication with JWT and Role-Based Access Control
- Course Management with Materials and Quizzes
- AI-Generated Course Content and Quizzes
- Real-time Chat System
- Personalized Learning Recommendations
- Performance Analytics
- Administrative Dashboard

## Tech Stack

- Frontend: React.js (TypeScript), Tailwind CSS
- Backend: Python (FastAPI)
- Database: MongoDB
- AI Integration: OpenAI API
- Real-time Communication: WebSockets

## API Documentation

### Authentication Endpoints
- `POST /api/auth/register`
  - Register a new user
  - Content-Type: `application/json`
  - Body:
    ```json
    {
        "email": "user@example.com",
        "name": "User Name",
        "role": "student",
        "password": "secure_password"
    }
    ```

- `POST /api/auth/login`
  - Login and get access token
  - Content-Type: `application/json`
  - Body:
    ```json
    {
        "email": "your.email@example.com",
        "password": "your_password"
    }
    ```
  - Returns:
    ```json
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "token_type": "bearer"
    }
    ```

- `GET /api/auth/me`
  - Get current user profile
  - Requires: Bearer token in Authorization header
  - Returns: User profile data

### User Management
- `GET /api/users`
  - List all users (admin only)
  - Requires: Admin access

- `GET /api/users/{user_id}`
  - Get specific user details
  - Requires: Admin access or own profile

- `DELETE /api/users/{user_id}`
  - Delete a user
  - Requires: Admin access

### Course Management
- `POST /api/courses`
  - Create a new course
  - Requires: Instructor access
  - Body: Course details

- `GET /api/courses`
  - List all courses
  - Filtered by user role (students see enrolled, instructors see own courses)

- `GET /api/courses/{course_id}`
  - Get course details
  - Requires: Course access

- `DELETE /api/courses/{course_id}`
  - Delete a course
  - Requires: Course instructor or admin access

### Materials
- `POST /api/materials`
  - Add course material
  - Requires: Instructor access
  - Body: Material details

- `GET /api/materials/course/{course_id}`
  - List course materials
  - Requires: Course access

- `GET /api/materials/{material_id}`
  - Get material details
  - Requires: Course access

### Progress Tracking
- `GET /api/progress/course/{course_id}`
  - Get course progress
  - Requires: Course access

- `POST /api/progress/update`
  - Update progress
  - Requires: Course access

### AI Features
- `POST /api/ai/personalize`
  - Get personalized content recommendations
  - Body: `{ "course_id": string }`

- `POST /api/ai/generate-content`
  - Generate learning content
  - Body: `{ "topic": string, "difficulty": string }`

- `POST /api/ai/analyze-performance`
  - Analyze student performance
  - Body: `{ "course_id": string, "student_id": string? }`

- `POST /api/ai/chat-assistant`
  - Chat with AI learning assistant
  - Body: `{ "message": string, "course_id": string? }`

### Admin Dashboard
- `GET /api/admin/dashboard`
  - Get system statistics
  - Requires: Admin access

- `GET /api/admin/users`
  - List all users with details
  - Requires: Admin access

- `PUT /api/admin/users/{user_id}/role`
  - Update user roles
  - Requires: Admin access
  - Body: `{ "is_instructor": boolean, "is_admin": boolean }`

- `GET /api/admin/audit-log`
  - Get system audit logs
  - Requires: Admin access

### Chat System
- `POST /api/chat/rooms`
  - Create chat room
  - Requires: Instructor access
  - Body: Room details

- `GET /api/chat/rooms/{course_id}`
  - List course chat rooms
  - Requires: Course access

- `GET /api/chat/messages/{room_id}`
  - Get chat messages
  - Requires: Room access

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-lms
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with:
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=lms_db
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key
```

5. Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

6. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. To access protected endpoints:

1. Register a user or login to get an access token
2. Include the token in the Authorization header:
   `Authorization: Bearer <your-token>`

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

Error responses include a detail message explaining the error.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License. #   m e n t o r o i d - b a c k e n d  
 #   m e n t o r o i d - b a c k e n d  
 