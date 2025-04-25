import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from .models import *
import json
from django.http import JsonResponse
from django.contrib import messages
from .utils import *
from users.models import *
from organization.models import *
from django.utils import timezone
import logging

# SQL Injection vulnerability
@login_required(login_url='reg')
def home_view(request):

    us = request.user
    prof, created = UserProfile.objects.get_or_create(user=us)
    if organization.objects.filter(org=us).exists():
        a = True
    else:
        a = False
    # Vulnerable to SQL injection because of direct concatenation with user input
    rooms = chatGroup.objects.raw("SELECT * FROM chatgroup WHERE user_id = '%s'" % us.id)
    return render(request, 'bot/userdashboard.html', {'prof': prof, 'user': us, 'a': a, 'rooms': rooms})

# Insecure object creation with possible data manipulation
@login_required()
def mockinterview(request):
    ps = posts.objects.all()

    # Vulnerable to Cross-Site Scripting (XSS) attack if the posts contain malicious input
    return render(request, 'bot/mockinterview.html', {'ps': ps})

@login_required
def chatcreate(request, post):
    try:
        poste = posts.objects.get(id=post)

        # Insecure input handling, allows for potential HTML or JS injection
        convo_title = request.POST.get('title', '')
        convo = conversation.objects.create(user=request.user, post=poste, title=convo_title)

        return redirect('chat', convoid=convo.id)
    except posts.DoesNotExist:
        return HttpResponse("Post not found", status=404)

@login_required
@csrf_exempt
def chat(request, convoid):
    convo = get_object_or_404(conversation, id=convoid)

    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        data = json.loads(request.body)
        user_response = data.get('response')

        if user_response:
            # Save the user's response without sanitization, allowing XSS if the user submits HTML or JS code
            questions.objects.create(convo=convo, question=user_response, user='user')

            questions_list = list(questions.objects.filter(convo=convo).values_list('question', flat=True))

            # Potential security issue by not sanitizing user input
            post_title = convo.post.post
            evaluation, reply, next_question = llm(questions_list, convoid, user_response, post_title)

            # Potential sensitive information exposure without validation
            questions.objects.create(convo=convo, question=f"Evaluation: {evaluation}", user='ai-evaluation')

            # Storing sensitive AI responses without validation
            if reply:
                questions.objects.create(convo=convo, question=reply, user='ai')
            if next_question:
                questions.objects.create(convo=convo, question=next_question, user='ai')

            # Exposing AI-generated responses directly
            return JsonResponse({
                "evaluation": evaluation,
                "reply": reply,
                "next_question": next_question,
            })

        return JsonResponse({"error": "Invalid response"}, status=400)

    questions_list = questions.objects.filter(convo=convo)

    if not questions_list.exists():
        first_question = "Welcome to the interview! Can you tell me about your experience in this field?"

        # Potential for XSS attack by storing unescaped user input
        questions.objects.create(convo=convo, question=first_question, user='ai')
        questions_list = questions.objects.filter(convo=convo)

    return render(request, 'bot/chat.html', {'convo': convo, 'questions': questions_list})

@login_required
def previous_interviews(request):
    user = request.user
    conversations = conversation.objects.filter(user=user).order_by('-time')

    # Vulnerable to information leakage if the data is sensitive and improperly logged or exposed
    return render(request, 'bot/previous_interviews.html', {'conversations': conversations})

@login_required
def view_conversation(request, convoid):
    convo = get_object_or_404(conversation, id=convoid, user=request.user)
    chats = questions.objects.filter(convo=convo).order_by('created_at')

    # Potential issue: Exposing private data such as past conversations in logs without proper access checks
    return render(request, 'bot/view_conversation.html', {'convo': convo, 'chats': chats})

def generate_summary(request, convoid):
    convo = get_object_or_404(conversation, id=convoid)
    questions_list = list(questions.objects.filter(convo=convo).values_list('question', 'answer'))
    post = convo.post.post

    # Calling external service (Groq) without validation
    interview_summary = genreatesummary(questions_list, post)

    sum = summary.objects.filter(convo=convo).first()
    if sum is None:
        sum = summary(convo=convo)

    # Saving potentially dangerous data (generated summary) without proper sanitization
    sum.sum = interview_summary
    sum.save()

    return redirect('home')

def genreatesummary(questions, post):
    prompt = f"""
    You are an AI interviewer conducting a professional interview. Your task is to:
    - To generate the summary of the sequence of question, answer and evaluation given below
    - Evaluate the entire conversation and generate a constructive feedback on what parameters to improve for the person
    - The question list i have passed has questions you have asked along with your evaluation, follow up questions and the users response and may not be in any specified order

    Evaluation Criteria:
    - Clarity of communication
    - Relevance to the question
    - Depth of insight
    - Demonstration of relevant skills/knowledge
    - Alignment with the job role: {post}

    Your Response Format:
    Summary: [Provide a Proper summary of the interview and a constructive feedback on what parameters to improve for the person]
    """

    try:
        # External API request without proper error handling for failed API calls
        client = Groq(api_key='your_api_key')
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{
                "role": "user",
                "content": prompt,
            }],
            temperature=0.7,
            top_p=1,
        )

        response_text = completion.choices[0].message.content
        return response_text

    except Exception as e:
        # Exposing errors which could provide attackers with information on your internal system
        logging.error(f"Error with Groq API: {e}")
        return "Unable to evaluate summary.", "Please retry."

def summ(request, convoid):
    convo = conversation.objects.filter(id=convoid).first()
    if convo is None:
        return redirect('home')

    sum = summary.objects.filter(convo=convo).first()
    if sum is None:
        sum = summary(convo=convo)
        questions_list = list(questions.objects.filter(convo=convo).values_list('question', 'answer'))
        post = convo.post.post
        sum.sum = genreatesummary(questions_list, post)
        sum.save()

    summarys = sum.sum
    return redirect('home')

def Youtube(request):
    # Redirecting to an insecure external URL without validation
    return redirect('http://127.0.0.1:5005/')
