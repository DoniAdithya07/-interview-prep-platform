# Firestore Data Architecture (Phase 3, Step 6)

## Collections

### `/users/{userId}`
- `name`: string
- `email`: string
- `role`: string
- `createdAt`: timestamp
- `profilePicture`: string (URL, optional)

### `/interviews/{interviewId}`
- `userId`: string (Firebase Auth UID)
- `type`: string (`DSA`, `HR`, `Core`)
- `questions`: array<string>
- `answers`: array<string>
- `score`: number
- `aiFeedback`: string
- `duration`: number (minutes)
- `createdAt`: timestamp

### `/progress/{userId}`
- `totalInterviews`: number
- `avgScore`: number
- `topicBreakdown`: map<string, number>
- `streakDays`: number
- `lastActive`: timestamp

## Security Model
- Users can read/write only their own `/users/{userId}` document.
- Interview documents are owner-scoped using `interviews.userId == request.auth.uid`.
- Progress is owner-scoped using `/progress/{userId}` where `userId == request.auth.uid`.

## Indexes
- `interviews`: (`userId` asc, `createdAt` desc)
  - For "recent interviews by user" screens.
- `interviews`: (`userId` asc, `type` asc, `createdAt` desc)
  - For "recent interviews by user and type" filters.
