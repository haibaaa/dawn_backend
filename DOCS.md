# API Documentation

This document provides a complete reference for the Academic Planner API based on the `api.json` specification. All protected endpoints require a valid **Bearer Token** obtained via the login endpoint.

## 1. Authentication
Endpoints for user management and session control.

### POST `/auth/signup`
Creates a new user account.
- **Request Body**: `{"email": "user@example.com", "password": "securepassword"}`

### POST `/auth/login`
Authenticates user and returns an access token.
- **Request Body**: `{"email": "user@example.com", "password": "securepassword"}`

### POST `/auth/refresh`
Refreshes an expired session.
- **Query Parameter**: `refresh_token` (string)

---

## 2. Tasks & Smart Prioritization
Manage your academic to-do list with automated priority scoring.

### GET `/tasks/`
Fetch your tasks.
- **Parameters**: 
  - `task_status`: `pending` (default) or `completed`.
  - `sort_by`: Default is `priority`.
- **Example Response**: 
  ```json
  [
    {
      "id": 1,
      "title": "Study for Physics Midterm",
      "priority": 9.5,
      "status": "pending",
      "deadline": "2024-11-20"
    }
  ]

```

### POST `/tasks/`

Create a task with parameters for the priority algorithm.

* **Body Example**:
```json
{
  "title": "Math Assignment",
  "description": "Calculus Chapter 3",
  "deadline": "2024-11-15",
  "grade_impact": 15.0,
  "estimated_hours": 4.0
}

```



---

## 3. Grade Portal & Performance

Track your scores and calculate what you need for your target grade.

### POST `/enrollments/`

Enroll in a course and set goals.

* **Body Example**: `{"course_code": "CS101", "target_grade": "A", "target_score": 90.0}`

### GET `/student-assessments/`

View your current grades for a specific course.

* **Query Parameter**: `course_code` (e.g., `?course_code=CS101`)

### POST `/student-assessments/`

Record a new score.

* **Body Example**: `{"assessment_id": 10, "score": 85.5}`

---

## 4. Resource Bank & AI Tools

Shared study materials and AI-generated content.

### GET `/resources/` (The Bank)

Search for materials uploaded by all users.

* **Query Parameter**: `tags` (Array). Supports **overlap search** (e.g., `?tags=pdf&tags=exam`).

### POST `/resources/upload`

Upload a document to the bank.

* **Multipart Form**: `title`, `tags` (comma-separated), `file` (binary).

### POST `/flashcards/generate`

Convert a lecture file into study flashcards.

* **Response**: `{"flashcards": [{"question": "...", "answer": "..."}]}`

### POST `/quiz/generate`

Turn past year papers or notes into a practice quiz.

* **Response**: An array of generated question objects.

---

## 5. Course Structure Management

Define how grades are calculated.

### POST `/assessment-groups/`

Define weightage (e.g., "Final Exam" worth 40%).

* **Body Example**: `{"name": "Quizzes", "weight": 20.0, "count": 5, "best_of": 3, "course_code": "CS101"}`

### POST `/assessments/`

Add an item to a group.

* **Body Example**: `{"name": "Quiz 1", "max_score": 100, "assessment_group_id": 5}`


