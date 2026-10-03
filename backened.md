# TaskFlow – API Documentation & Analysis

**Backend:** Django (REST, JWT auth) | **Frontend:** Flutter
**Total Endpoints:** 71 | **Modules:** 15

---

## 1. Overview

TaskFlow is a company mobile app where users manage projects and tasks. Roles: `Admin`, `Project Manager`, `Team Lead`, `Employee`, `Viewer`.

Base URL: `/api/`
Auth: JWT (`Authorization: Bearer <access_token>`)

---

## 2. Endpoints (by Module)

### 2.1 Auth

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/login/` | Login, returns access + refresh tokens |
| POST | `/api/auth/refresh/` | Get a new access token |
| GET | `/api/auth/me/` | Current user's profile + role |

### 2.2 Users

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/users/` | List users |
| POST | `/api/users/` | Create user (Admin) |
| GET | `/api/users/{id}/` | User detail |
| PATCH | `/api/users/{id}/` | Update user |
| DELETE | `/api/users/{id}/` | Delete / deactivate user |

### 2.3 Teams

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/teams/` | List teams |
| POST | `/api/teams/` | Create team |
| GET | `/api/teams/{id}/` | Team detail (members + lead) |
| PATCH | `/api/teams/{id}/` | Update team |
| DELETE | `/api/teams/{id}/` | Delete team |

### 2.4 Projects

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/projects/` | List projects |
| POST | `/api/projects/` | Create project |
| GET | `/api/projects/{id}/` | Project detail |
| PATCH | `/api/projects/{id}/` | Update project |
| DELETE | `/api/projects/{id}/` | Delete project |
| GET | `/api/projects/{id}/progress/` | Progress % (completed / total tasks) |

### 2.5 Project Members

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/project-members/` | List members |
| POST | `/api/project-members/` | Add member to a project |
| GET | `/api/project-members/{id}/` | Member detail |
| PATCH | `/api/project-members/{id}/` | Update member role |
| DELETE | `/api/project-members/{id}/` | Remove member |

### 2.6 Milestones

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/milestones/` | List milestones |
| POST | `/api/milestones/` | Create milestone |
| GET | `/api/milestones/{id}/` | Milestone detail |
| PATCH | `/api/milestones/{id}/` | Update milestone |
| DELETE | `/api/milestones/{id}/` | Delete milestone |

### 2.7 Tasks

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/tasks/` | List tasks |
| POST | `/api/tasks/` | Create task |
| GET | `/api/tasks/{id}/` | Task detail |
| PATCH | `/api/tasks/{id}/` | Update task |
| DELETE | `/api/tasks/{id}/` | Delete task |
| GET | `/api/tasks/my/` | Logged-in user's tasks |
| GET | `/api/tasks/dashboard/` | Employee dashboard stats |
| GET | `/api/tasks/manager-dashboard/` | Manager dashboard stats |
| GET | `/api/tasks/team-lead-dashboard/` | Team Lead dashboard stats |
| GET | `/api/tasks/calendar/` | Calendar data (due dates) |
| PATCH | `/api/tasks/{id}/status/` | Change status only |

Task statuses: `TODO`, `IN_PROGRESS`, `IN_REVIEW`, `COMPLETED`, `BLOCKED`

### 2.8 Subtasks

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/subtasks/` | List subtasks |
| POST | `/api/subtasks/` | Create subtask |
| GET | `/api/subtasks/{id}/` | Detail |
| PATCH | `/api/subtasks/{id}/` | Update / check-uncheck |
| DELETE | `/api/subtasks/{id}/` | Delete |

### 2.9 Comments

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/comments/` | List comments |
| POST | `/api/comments/` | Add comment |
| GET | `/api/comments/{id}/` | Detail |
| PATCH | `/api/comments/{id}/` | Edit |
| DELETE | `/api/comments/{id}/` | Delete |

### 2.10 Labels

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/labels/` | List labels |
| POST | `/api/labels/` | Create label |
| GET | `/api/labels/{id}/` | Detail |
| PATCH | `/api/labels/{id}/` | Update |
| DELETE | `/api/labels/{id}/` | Delete |

### 2.11 Attachments

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/attachments/` | List attachments |
| POST | `/api/attachments/` | Upload file (multipart) |
| GET | `/api/attachments/{id}/` | Detail / file URL |
| PATCH | `/api/attachments/{id}/` | Update |
| DELETE | `/api/attachments/{id}/` | Delete |

### 2.12 Activity Logs (read-only)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/activity-logs/` | History list |
| GET | `/api/activity-logs/{id}/` | Single log entry |

### 2.13 Time Logs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/time-logs/` | List time logs |
| POST | `/api/time-logs/` | Manual time entry |
| GET | `/api/time-logs/{id}/` | Detail |
| POST | `/api/time-logs/start/` | Start timer |
| POST | `/api/time-logs/stop/` | Stop timer |

### 2.14 Notifications

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/notifications/` | List notifications |
| PATCH | `/api/notifications/{id}/read/` | Mark one as read |
| PATCH | `/api/notifications/read-all/` | Mark all as read |

### 2.15 Admin

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/admin-dashboard/` | Admin overall stats |

---

## 3. Analysis

### 3.1 What's Good

- **Coverage:** Almost every concept from the explanation (users, teams, projects, tasks, subtasks, comments, attachments, labels, time tracking, activity log, notifications, milestones, calendar, dashboards) has an endpoint.
- **Consistent REST pattern:** Most modules use standard CRUD (`GET / POST / GET{id} / PATCH / DELETE`), so the Flutter repository layer can follow one pattern.
- **PATCH for partial updates:** The right choice.
- **Read-only activity logs:** Correct, since users shouldn't edit an audit trail.
- **`start/stop` for time logs:** Covers the timer flow naturally.
- **Separate status endpoint:** `/tasks/{id}/status/` lets Employees change only the status without edit rights on the whole task.
- **Notifications:** Both `read` and `read-all` exist, which UX needs.

### 3.2 Gaps / Missing Endpoints

| Area | What's missing | Why it matters |
|------|----------------|----------------|
| Auth | `POST /auth/logout/` (blacklist refresh token) | Secure logout |
| Auth | `POST /auth/change-password/` | Standard requirement |
| Auth | Forgot / reset password | Account recovery |
| Profile | `PATCH /auth/me/` | Users can update their own profile / photo |
| Teams | `team-members` endpoints or `POST /teams/{id}/members/` | The design mentions "Team + Team Members", but there's no clear add/remove endpoint |
| Reports | `/api/reports/...` | A "Reports Screen" is planned in Flutter, but only `admin-dashboard` exists |
| Viewer role | Dashboard / read-only project view | No dedicated endpoint for Viewer (client) |
| Time logs | `PATCH` / `DELETE` and `GET /time-logs/active/` | Fix wrong entries; restore a running timer after app restart |
| Notifications | `GET /notifications/unread-count/` and `DELETE` | Bell icon badge count |
| Push | `POST /devices/` (register FCM token) | Mobile push notifications |
| Labels | Clear way to attach/detach labels on a task | Task serializer should accept `label_ids`, or add a separate endpoint |
| Search | `?search=` | Search in tasks/projects |

### 3.3 Design Issues / Risks

1. **Dashboards are scattered.**
   `/tasks/dashboard/`, `/tasks/manager-dashboard/`, `/tasks/team-lead-dashboard/` and `/admin-dashboard/` live in different places.
   *Suggestion:* A single `GET /api/dashboard/` that returns data based on the caller's role. Flutter would make one call, and Viewer would be covered too. If you keep the current design, just call the right endpoint per role in Flutter.

2. **Route conflict risk.**
   `/tasks/my/`, `/tasks/calendar/`, etc. can clash with `/tasks/{id}/`. With DRF `@action(detail=False)` this is fine, but if you used manual `path()` entries, put **static routes before `{id}`**.

3. **Nested data is hard without filters.**
   Comments, subtasks, attachments, time-logs and activity-logs are all top-level. To fetch them per task you need query params:
   ```
   GET /api/comments/?task=12
   GET /api/subtasks/?task=12
   GET /api/attachments/?task=12
   GET /api/activity-logs/?task=12
   GET /api/tasks/?project=3&status=TODO&assignee=5
   GET /api/milestones/?project=3
   ```
   Make sure these filters are implemented, otherwise Flutter has to download everything and filter on the client.

4. **Write down a permissions matrix.**
   Every module has the same CRUD, so real security depends on role-based permissions. A suggested matrix is below.

5. **Pagination.**
   Paginate list endpoints (`?page=1&page_size=20`). Infinite scroll in Flutter depends on it.

6. **Attachments `PATCH`.**
   It should update metadata only (name/description), not replace the file. Decide this explicitly.

7. **`/projects/{id}/progress/` vs project detail.**
   If progress is always needed, include a `progress` field in project list/detail too. Otherwise the list screen makes one extra call per project (N+1 problem).

8. **Project Members vs Team.**
   A project has both a `team` and `project-members`. Clarify which one decides access, or permission logic will get confusing.

### 3.4 Suggested Permission Matrix

| Action | Admin | Manager | Team Lead | Employee | Viewer |
|--------|:-----:|:-------:|:---------:|:--------:|:------:|
| Create/delete users | ✅ | ❌ | ❌ | ❌ | ❌ |
| Create/edit teams | ✅ | ✅ | ❌ | ❌ | ❌ |
| Create/edit projects | ✅ | ✅ | ❌ | ❌ | ❌ |
| View project | ✅ | ✅ (own) | ✅ (own team) | ✅ (assigned) | ✅ (read-only) |
| Create / assign tasks | ✅ | ✅ | ✅ (own team) | ❌ | ❌ |
| Change task status | ✅ | ✅ | ✅ | ✅ (own only) | ❌ |
| Add comments | ✅ | ✅ | ✅ | ✅ | ❌ (or read-only) |
| Start/stop timer | ✅ | ✅ | ✅ | ✅ | ❌ |
| View activity logs | ✅ | ✅ | ✅ | own tasks | ❌ |
| Admin dashboard | ✅ | ❌ | ❌ | ❌ | ❌ |

*(This is only a suggestion. Adjust it to your business rules.)*

---

## 4. Backend → Flutter Screen Mapping

| Flutter Screen | APIs |
|----------------|------|
| Login | `POST /auth/login/` |
| Splash / session restore | `GET /auth/me/`, `POST /auth/refresh/` |
| Dashboard (role-based) | `/tasks/dashboard/`, `/tasks/manager-dashboard/`, `/tasks/team-lead-dashboard/`, `/admin-dashboard/` |
| Projects list | `GET /projects/` |
| Project detail | `GET /projects/{id}/`, `/projects/{id}/progress/`, `/milestones/?project=`, `/project-members/?project=` |
| My Tasks | `GET /tasks/my/` |
| Task detail | `GET /tasks/{id}/`, `/subtasks/`, `/comments/`, `/attachments/`, `/time-logs/`, `/activity-logs/` |
| Status change | `PATCH /tasks/{id}/status/` |
| Timer | `POST /time-logs/start/`, `POST /time-logs/stop/` |
| Calendar | `GET /tasks/calendar/` |
| Notifications | `GET /notifications/`, `PATCH /notifications/{id}/read/`, `PATCH /notifications/read-all/` |
| Teams | `/teams/` |
| Users (Admin) | `/users/` |
| Labels management | `/labels/` |
| Reports | *(endpoint missing for now)* |

---

## 5. Recommended Flutter Build Order

1. **Auth:** Login, secure token storage, auto-refresh interceptor (Dio)
2. **Role-based routing:** Use `/auth/me/` to pick the right dashboard
3. **Dashboard**
4. **Projects:** list + detail
5. **Tasks:** My Tasks, Task detail, status change
6. **Task extras:** Subtasks, Comments, Attachments
7. **Time tracking**
8. **Notifications**
9. **Calendar**
10. **Admin screens:** Users, Teams
11. **Reports**

### Suggested Flutter folder structure

```text
lib/
├── core/            (dio client, interceptors, constants, theme)
├── features/
│   ├── auth/
│   ├── dashboard/
│   ├── projects/
│   ├── tasks/
│   ├── comments/
│   ├── notifications/
│   ├── calendar/
│   ├── teams/
│   └── users/
│       ├── data/         (models, api, repository)
│       ├── domain/
│       └── presentation/ (screens, widgets, state)
└── main.dart
```

---

## 6. Quick Checklist (confirm with the backend)

- [ ] Does the login response include `access`, `refresh` and `user` (with role)?
- [ ] Do list endpoints support pagination and filters?
- [ ] Is role-based permission applied on every endpoint?
- [ ] Is the error response format consistent? (`{"detail": "..."}` or field errors)
- [ ] Do attachments support multipart upload and return absolute file URLs?
- [ ] Does the task response include `assignee`, `labels`, `progress`, `subtasks_count`, `comments_count`?
- [ ] Does calling time-log `start` twice prevent duplicate timers?
- [ ] Is the activity log created automatically (via signals)?
- [ ] Is there a scheduled job (Celery / cron) for deadline reminders?
- [ ] Is Swagger / OpenAPI (`drf-spectacular`) enabled? It helps the Flutter side a lot.

---

## 7. Summary

The API design is **solid and nearly complete**: 71 endpoints, a clean REST structure, and all the core features from the explanation are covered.

**Top improvements:**
1. Logout, change/reset password and profile update
2. A clear team members endpoint
3. Reports endpoints
4. Guaranteed filters and pagination
5. Unify dashboards (and cover the Viewer role)
6. A device-token endpoint for push notifications

Once these are added, the API is ready for Flutter development.
