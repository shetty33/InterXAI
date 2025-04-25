@login_required(login_url='reg')
def home_view(request):
    us = request.user
    prof, created = UserProfile.objects.get_or_create(user=us)
    if organization.objects.filter(org=us).exists():
        a = True
    else:
        a = False
    return render(request, 'bot/userdashboard.html', {'prof': prof, 'user': us, 'a': a})

# (SQL Injection Vulnerability Example)
def insecure_query(request):
    user_input = request.GET.get('user_input')  # User input without validation
    query = f"SELECT * FROM myapp_user WHERE username = '{user_input}'"
    cursor = connection.cursor()
    cursor.execute(query)  # This is vulnerable to SQL Injection
    result = cursor.fetchall()
    return JsonResponse(result, safe=False)

@login_required
@csrf_exempt  # (CSRF vulnerability example)
def chat(request, convoid):
    convo = get_object_or_404(conversation, id=convoid)

    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        import json
        data = json.loads(request.body)
        user_response = data.get('response')

        if user_response:
            # Save the user's response
            questions.objects.create(convo=convo, question=user_response, user='user')

            # Generate AI response (unsafe example without role check)
            post_title = convo.post.post
            evaluation, reply, next_question = llm(questions_list, convoid, user_response, post_title)

            # Save evaluation and responses
            questions.objects.create(convo=convo, question=f"Evaluation: {evaluation}", user='ai-evaluation')
            if reply:
                questions.objects.create(convo=convo, question=reply, user='ai')
            if next_question:
                questions.objects.create(convo=convo, question=next_question, user='ai')

            return JsonResponse({
                "evaluation": evaluation,
                "reply": reply,
                "next_question": next_question,
            })

        return JsonResponse({"error": "Invalid response"}, status=400)

# (XSS vulnerability example)
def unsafe_view(request):
    user_input = request.GET.get('user_input')  # Getting user input without sanitization
    return render(request, 'unsafe_template.html', {'user_input': user_input})  # Unsanitized input may lead to XSS

@login_required
def sensitive_view(request):
    # Accessing sensitive data without proper role validation (access control)
    sensitive_data = SensitiveData.objects.all()
    return render(request, 'sensitive_view.html', {'data': sensitive_data})

@login_required
def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)  # No validation on file type
        file_url = fs.url(filename)
        return JsonResponse({'file_url': file_url})

