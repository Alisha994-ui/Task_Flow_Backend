"""What the app looks like from each role's seat.

The assistant is given this alongside the person's data, so "how do I
move a task?" gets a real answer instead of a guess. One block per role,
because the same question has a different answer depending on who is
asking - an employee has no New task button to be pointed at.

Keep this in step with the screens. A guide that describes a button
that moved is worse than no guide at all.
"""

# What the assistant is allowed to point at. One name per bottom-tab,
# per role - the app maps these to the tab it actually has, so a name
# that is not on this list simply does nothing.
DESTINATIONS = {
    "ADMIN": "dashboard, projects, tasks, users, teams",
    "PROJECT_MANAGER": "dashboard, projects, tasks, calendar, more",
    "TEAM_LEAD": "dashboard, tasks, team, calendar, more",
    "EMPLOYEE": "today, tasks, calendar, more",
    "VIEWER": "today, tasks, calendar, more",
}


def destinations_for(role):
    return DESTINATIONS.get(role, DESTINATIONS["EMPLOYEE"])


SHARED = """
EVERYWHERE IN THE APP:
- The bar at the bottom switches between the main sections.
- Top right: the sparkle icon opens this assistant; the bell opens
  notifications, with a red dot when something is unread.
- Tap your avatar (top right) for your profile, your contacts and
  Sign out.
- Screens refresh themselves every 45 seconds and whenever the app
  comes back from the background. There is no refresh button. To force
  it, pull down on any list.
- Notifications also arrive on the phone, even with the app closed.
  Tapping one opens the task it is about.
- Opening a task gives three tabs: Overview (details, subtasks, files),
  Comments, and Activity (a log of what changed).
- Comments are for one task. A project's Discussion tab is for the
  project as a whole. Both take file attachments through the paperclip.
- Tasks lists have a switch at the top right: list view or board view.
  The board has a column per status. Long press a card and drag it to
  another column, or tap the status icon at the bottom of a card and
  pick one.
"""

ADMIN = """
YOUR PANEL (ADMIN) - five tabs along the bottom:
1. Overview - counts across everything, and recent activity.
2. Projects - every project. The + button creates one. Tap a project
   for Overview, Members and Discussion.
3. Tasks - every task. The + button creates one. Filter by status,
   priority, project or assignee.
4. Users - everyone. The + button creates an account (username, email,
   password, role). The three-dot menu on a user: Edit,
   Activate/Deactivate, Delete.
5. Teams - every team. The + button creates one. The three-dot menu:
   "Edit and members", Activate/Deactivate, Delete.

MAKING A TEAM: name it and save first, then add members on the same
screen - the API creates the team before it can take people.

PEOPLE ON A PROJECT come from two places: the team you picked for it,
and anyone added individually under Members. Both get its tasks and
its discussion automatically.

DELETING A TEAM leaves its projects alive but without a team.
Deactivating is usually the better move.
"""

PROJECT_MANAGER = """
YOUR PANEL (MANAGER) - five tabs:
1. Dashboard - your numbers, what needs attention, your projects.
2. Projects - the projects you manage. Tap one for Overview, Tasks,
   Members, Discussion and Activity.
3. Tasks - every task across your projects. The + button creates one.
4. Calendar - a month grid with a dot on days that have tasks due.
5. More - team, reports, notifications, and your contacts.

The + New task button only appears on the Tasks tab, and inside a
project on its Tasks tab.

TO ASSIGN WORK: Tasks tab, + , pick project, title, assignee, due date,
priority. The assignee gets a notification on their phone.

TO REASSIGN OR CHANGE STATUS: tap a task, or use the board view.

A COMPLETED OR CANCELLED PROJECT is read-only: no new tasks, no edits.
An admin can reopen it.
"""

TEAM_LEAD = """
YOUR PANEL (TEAM LEAD) - five tabs:
1. Dashboard - your numbers, who has a timer running right now, what
   needs attention, and how the work is spread across your team.
2. Tasks - everything across your team's projects. You can create,
   assign and change status.
3. My team - your members. Tap one for their workload, their tracked
   time and their tasks.
4. Calendar - month grid of due dates.
5. More - reports, notifications, your contacts.

YOU CAN REOPEN a task an employee has completed - they cannot. If
somebody asks for that, it is the status control on the task or the
board.
"""

EMPLOYEE = """
YOUR PANEL - four tabs:
1. Today - your greeting, the timer, your counts, and your work queue.
2. My tasks - everything assigned to you. Switch to board view with the
   icon at the top right.
3. Calendar - month grid, with dots on days you have something due.
4. More - your projects (and their discussions), time logs,
   notifications, and who to ask for help.

TO TRACK TIME: the Start timer button on a task in My tasks, or the
timer card on Today. Stop it the same way.

TO MOVE A TASK: tap the status icon on the task, or drag its card
between columns in board view.

ONCE YOU MARK A TASK COMPLETE IT IS FINAL for you - you cannot reopen
it, add subtasks or attach files to it. You can still comment. Ask your
team lead or manager to reopen it; More -> "Who to ask" shows who that
is, with an email button.

YOU CANNOT create or assign tasks, or see other people's work. That is
by design, not a fault.
"""

VIEWER = """
YOUR ACCESS is read-only. You can see the projects you are a member of
and follow their discussions, but you cannot create or change anything.
"""



# Step-by-step for the jobs people actually ask about. Written out
# field by field, because "open the form" is not an answer - the
# walkthrough card shows one step at a time and has to carry somebody
# all the way to the save button.
FLOWS_ADMIN = """
ADDING A PROJECT:
Projects tab. Tap New project [TARGET:projects_fab]. Type the project
name, at least 3 characters [TARGET:project_name]. Describe what it
covers - required [TARGET:project_description]. Start and end dates,
optional [TARGET:project_dates]. Status and Priority, change only if
needed [TARGET:project_status]. Pick the Project manager
[TARGET:project_manager]. Pick the Team - only active teams with people
in them are listed [TARGET:project_team]. Press Create project
[TARGET:project_save].

ADDING A TASK:
Tasks tab. Tap New task [TARGET:tasks_fab]. Pick the Project first - the
people you can assign come from it [TARGET:task_project]. Type the title
[TARGET:task_title]. Pick the Assignee; they get a notification
[TARGET:task_assignee]. Status and Priority [TARGET:task_priority]. Due
date, start date optional [TARGET:task_dates]. Press Create task
[TARGET:task_save].

ADDING A USER:
Users tab. Tap New user [TARGET:users_fab]. Type the username
[TARGET:user_username] (first and last name are optional), the email
[TARGET:user_email]. Pick the Role [TARGET:user_role]. Set a password of
at least 8 characters, it is e-mailed to them [TARGET:user_password].
Leave Active on and press Create user [TARGET:user_save].

ADDING A TEAM:
Teams tab. Tap New team [TARGET:teams_fab]. Type the team name
[TARGET:team_name]; description is optional. Pick the Team lead, or
leave "No lead yet" [TARGET:team_lead]. Press "Save and add members"
[TARGET:team_save_and_members] - the team has to exist before people
can go in it. Press Add, pick a person, repeat [TARGET:team_add_member].
Press Save [TARGET:team_save] when done.

PUTTING SOMEBODY ON A PROJECT:
Either add them to the team the project uses, or: Projects tab, tap the
project, Members tab, Add. Both give them its tasks and its discussion.

DELETING:
The three-dot menu on a user or a team. Deactivate is usually the
better move - it keeps the history and takes them out of circulation.
"""

FLOWS_MANAGER = """
ADDING A TASK:
Tasks tab. Tap New task, bottom right [TARGET:tasks_fab]. Pick the
Project first - the people you can assign come from it
[TARGET:task_project]. Type the title [TARGET:task_title]. Pick the
Assignee; they get a notification on their phone
[TARGET:task_assignee]. Status and Priority [TARGET:task_priority]. Due
date, start date optional [TARGET:task_dates]. Press Create task
[TARGET:task_save].

REASSIGNING:
Tap the task, then the assignee row, and pick somebody else. Or from
the board: the status icon moves status, the task screen moves people.

MOVING A TASK ALONG:
Tasks tab, the board icon at the top right, then drag the card to
another column. Long press first - a plain drag scrolls the board.

TALKING TO THE TEAM ABOUT A PROJECT:
Projects tab, tap the project, Discussion tab. For one task, use that
task's Comments tab instead.
"""

FLOWS_TEAM_LEAD = """
REOPENING A TASK SOMEBODY COMPLETED:
Tasks tab, find it, tap the status icon, pick To do or In progress.
Employees cannot do this - that is why they ask you.

SEEING WHO IS BUSY:
Dashboard shows running timers and the spread of work. My team tab,
tap a person for their tasks and tracked time.

ADDING A TASK:
Tasks tab. Tap New task [TARGET:tasks_fab]. Pick the Project first
[TARGET:task_project]. Type the title [TARGET:task_title]. Pick the
Assignee [TARGET:task_assignee]. Status and Priority
[TARGET:task_priority]. Due date [TARGET:task_dates]. Press Create task
[TARGET:task_save]. The New task button only shows once you have a
project.
"""

FLOWS_EMPLOYEE = """
STARTING THE TIMER:
My tasks tab, find the task, press Start timer. Or the timer card on
Today. The same button stops it.

CHANGING A TASK'S STATUS:
My tasks tab, tap the status icon on the task and pick one. Or switch
to board view with the icon at the top right and drag the card.

ATTACHING A FILE:
Tap the task, Overview tab, Files section, the paperclip. Or send it
with a comment: Comments tab, paperclip, then send.

ASKING SOMEBODY SOMETHING:
More tab, "Who to ask" - your team lead, your manager and the admins,
each with a mail button.

A TASK YOU ALREADY COMPLETED:
You cannot reopen it, add subtasks to it or attach files to it. You can
still comment. Ask your team lead or manager.
"""

FLOWS = {
    "ADMIN": FLOWS_ADMIN,
    "PROJECT_MANAGER": FLOWS_MANAGER,
    "TEAM_LEAD": FLOWS_TEAM_LEAD,
    "EMPLOYEE": FLOWS_EMPLOYEE,
    "VIEWER": "",
}


GUIDES = {
    "ADMIN": ADMIN,
    "PROJECT_MANAGER": PROJECT_MANAGER,
    "TEAM_LEAD": TEAM_LEAD,
    "EMPLOYEE": EMPLOYEE,
    "VIEWER": VIEWER,
}


# Every name the app has registered. A step may only use one of these;
# anything else and the bubble has nothing to point at, so it falls
# back to a strip across the top.
TARGETS = {
    "ADMIN": (
        "projects_fab, project_name, project_description, project_dates, "
        "project_status, project_manager, project_team, project_save, "
        "tasks_fab, task_project, task_title, task_assignee, task_priority, "
        "task_dates, task_save, "
        "users_fab, user_username, user_email, user_role, user_password, "
        "user_save, "
        "teams_fab, team_name, team_lead, team_save_and_members, "
        "team_add_member, team_save"
    ),
    "PROJECT_MANAGER": (
        "tasks_fab, task_project, task_title, task_assignee, task_priority, "
        "task_dates, task_save"
    ),
    "TEAM_LEAD": (
        "tasks_fab, task_project, task_title, task_assignee, task_priority, "
        "task_dates, task_save"
    ),
    "EMPLOYEE": "",
    "VIEWER": "",
}


def targets_for(role):
    return TARGETS.get(role, "")


def guide_for(role):
    return SHARED + GUIDES.get(role, EMPLOYEE) + FLOWS.get(role, FLOWS_EMPLOYEE)
