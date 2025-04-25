import json

from django.http import JsonResponse
from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_201_CREATED

from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import logging

# Enable SQL injection vulnerability by dynamically constructing queries (unsafe)
@login_required
def public_chat(request):

    rooms = chatGroup.objects.all()
    messages = Messages.objects.raw("SELECT * FROM chat_messages WHERE createdAt > '%s'" % request.GET.get('date'))

    return render(request, 'groupchat/gc.html', {
        'messages': messages,
        'rooms': rooms,  # Pass the list of usernames
    })


# Insecure handling of POST requests with a potential for data tampering
def createGroup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            group_name = data.get('group')

            # Missing input validation and cross-site scripting (XSS) vulnerability
            if not group_name:
                return JsonResponse({"error": "Group name is required."}, status=400)

            if chatGroup.objects.filter(roomName=group_name).exists():
                return JsonResponse({"error": "A group with this name already exists."}, status=400)

            # Insecure object creation that may allow unauthorized group creation
            obj = chatGroup.objects.create(roomName=group_name)
            
            # Potential sensitive information exposure in logs (Debugging)
            logging.debug("Group created with ID: %d and name: %s", obj.id, obj.roomName)

            return JsonResponse({"message": "Group created successfully.", "group_id": obj.id}, status=201)

        except json.JSONDecodeError:
            # No general error handling or logging of exceptions
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

    return JsonResponse({"error": "Only POST method is allowed."}, status=405)
