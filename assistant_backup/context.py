"""Builds the snapshot of a person's world that the model is allowed to see.

This is the part that matters. The model only ever knows what this file
hands it, so scoping here is what stops an employee asking about
somebody else's work and getting an answer.

The rules mirror the API's own: admin sees everything, a manager their
projects, a lead their teams', an employee only what is theirs.
"""

from django.utils import timezone

from projects.models import Project
from tasks.models import Task
from teams.models import Team

from .guide import destinations_for, guide_for, targets_for


def _date(value):
    return value.isoformat() if value else "not set"


def _task_line(task, today):
    bits = [
        f"#{task.id} {task.title}",
        f"status={task.status}",
        f"priority={task.priority}",
        f"project={task.project.name}",
    ]

    if task.assignee:
        bits.append(f"assignee={task.assignee.username}")
    else:
        bits.append("assignee=nobody")

    if task.due_date:
        days = (task.due_date - today).days

        if days < 0 and task.status != Task.Status.COMPLETED:
            bits.append(f"due={_date(task.due_date)} (OVERDUE by {-days}d)")
        else:
            bits.append(f"due={_date(task.due_date)} ({days}d)")
    else:
        bits.append("due=not set")

    return " | ".join(bits)


def _visible_tasks(user):
    """Exactly what tasks/views.py would return for this person."""
    queryset = Task.objects.select_related("project", "assignee")

    if user.role == "ADMIN":
        return queryset
    if user.role == "PROJECT_MANAGER":
        return queryset.filter(project__manager=user)
    if user.role == "TEAM_LEAD":
        return queryset.filter(project__team__team_lead=user)
    if user.role == "EMPLOYEE":
        return queryset.filter(assignee=user)

    return queryset.filter(project__project_members__user=user).distinct()


def _visible_projects(user):
    queryset = Project.objects.select_related("manager", "team")

    if user.role == "ADMIN":
        return queryset
    if user.role == "PROJECT_MANAGER":
        return queryset.filter(manager=user)
    if user.role == "TEAM_LEAD":
        return queryset.filter(team__team_lead=user)

    return queryset.filter(tasks__assignee=user).distinct()


def build_context(user, task_limit=60):
    """A plain-text briefing for the model.

    Plain text rather than JSON on purpose: it costs fewer tokens and
    the model reads it just as well.
    """
    today = timezone.now().date()
    lines = []

    lines.append(f"Today is {today.isoformat()}.")
    lines.append(
        f"You are talking to {user.get_full_name() or user.username} "
        f"(username {user.username}), whose role is {user.role}."
    )
    lines.append("")

    # ----------------------------------------------------------- projects
    projects = list(_visible_projects(user)[:25])

    if projects:
        lines.append("PROJECTS THEY CAN SEE:")

        for project in projects:
            manager = project.manager.username if project.manager else "nobody"
            team = project.team.name if project.team else "no team"
            lines.append(
                f"- #{project.id} {project.name} | status={project.status} "
                f"| progress={project.progress}% | manager={manager} "
                f"| team={team} | ends={_date(project.end_date)}"
            )

        lines.append("")

    # -------------------------------------------------------------- tasks
    tasks = list(_visible_tasks(user).order_by("due_date")[:task_limit])

    if tasks:
        lines.append(f"TASKS THEY CAN SEE ({len(tasks)} shown):")

        for task in tasks:
            lines.append("- " + _task_line(task, today))

        lines.append("")
    else:
        lines.append("They have no tasks visible to them.")
        lines.append("")

    # -------------------------------------------------------------- teams
    if user.role in ("ADMIN", "PROJECT_MANAGER", "TEAM_LEAD"):
        teams = Team.objects.prefetch_related("members").all()

        if user.role == "TEAM_LEAD":
            teams = teams.filter(team_lead=user)

        teams = list(teams[:10])

        if teams:
            lines.append("TEAMS:")

            for team in teams:
                members = ", ".join(
                    m.username for m in team.members.all()[:15]
                ) or "nobody"
                lead = team.team_lead.username if team.team_lead else "nobody"
                lines.append(f"- {team.name} | lead={lead} | members: {members}")

            lines.append("")

    # How the app works from this person's seat, so "where do I do X?"
    # has an answer as real as "what is overdue?".
    lines.append("HOW THE APP WORKS FOR THIS PERSON:")
    lines.append(guide_for(user.role))
    lines.append("")
    lines.append(
        "TABS YOU CAN SEND THEM TO: " + destinations_for(user.role)
    )

    targets = targets_for(user.role)

    if targets:
        lines.append("")
        lines.append("CONTROLS YOU CAN POINT AT: " + targets)

    return "\n".join(lines)


SYSTEM_PROMPT = """You are the assistant inside TaskFlow, a project
management app used by one company.

You do two things:
1. Answer questions about this person's own work - their tasks,
   projects, deadlines, team.
2. Show them how to use the app - where a button is, how to do
   something, what they are and are not allowed to do.

You are given a briefing with their data and a description of the app
as they see it. Answer only from that briefing.

How to answer:
- Short. Two or three sentences, or a short list. This is a phone.
- Concrete. Name the task, the project, the person, the date.
- Lead with the answer, not with a preamble.
- If the briefing does not contain the answer, say so plainly and say
  what you would need. Never invent a task, a name or a date.
- If asked about somebody or something not in the briefing, say you
  cannot see it rather than guessing - they may simply not have access.
- For "how do I..." questions, answer as numbered steps and nothing
  else: no preamble, no closing line. One short instruction per step,
  written as a command - "Tap the + button at the bottom right." Each
  step is shown on its own, over the real screen, so it has to make
  sense alone. Do not describe a screen the briefing does not mention,
  and never invent a button.
- Run the steps all the way to the end of the job. Opening a screen is
  not finishing it: if a form is involved, say which fields to fill in
  and name the button that saves. The last step is the one after which
  the thing exists. Four to eight steps is usual.

POINTING AT A CONTROL:
When a step is about one particular button or field, end that step
with its name in square brackets:

    2. Type the team name. [TARGET:team_name]

The app then dims the screen, lights that control up and puts the
bubble beside it. Rules:
- Only names from "CONTROLS YOU CAN POINT AT". Anything else is
  ignored, and the step shows as a plain strip instead.
- One per step, at the end of that step's line.
- Steps that are not about a single control - "pick a date", "scroll
  down" - simply have no tag. That is normal; do not invent one.
- Never mention the tag. To them it is a highlight, not text.
- Write plain text. No asterisks, no markdown, no bold - it is shown
  as written.

TAKING THEM THERE:
When your answer starts somewhere specific in the app, end your reply
with a line on its own:

    [GOTO:tasks]

using one name from "TABS YOU CAN SEND THEM TO". The app turns that
into a button that opens the tab. Rules:
- One marker, at the very end, nothing after it.
- Only when going somewhere is actually the next thing to do. An answer
  about what is overdue needs no marker.
- Never write the marker in the middle of a sentence, and never mention
  it - to them it is a button, not text.
- Then carry on: after they arrive they may ask "now what?", so keep
  your steps in mind.
- If they ask for something their role cannot do, say so and say who
  can - do not leave them hunting for a button that is not there.
- You cannot change anything: no creating, assigning or completing
  tasks. If asked, say so and tell them where in the app to do it.
- Match the language of the question. If they write Roman Urdu, reply
  in Roman Urdu.
- Do not mention the briefing, your instructions, or that you are an AI
  model. Just answer.
"""
