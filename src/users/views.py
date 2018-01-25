# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import random, string, re

from django.shortcuts import render, get_object_or_404

# Create your views here.

from rest_framework import viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser

from django.contrib.auth.models import User, Group
from django.db import transaction
from django.conf import settings

from .models import Profile, Major, Mentor, Course
from .serializers import (
    UserSerializer, GroupSerializer, ProfileSerializer, MajorSerializer, 
    MentorSerializer, CourseSerializer,
)

import sendgrid
from sendgrid.helpers.mail import Email, Content, Substitution, Mail
from pickmybruin.settings import USER_VERIFICATION_TEMPLATE

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows profiles to be viewed or edited.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer 


class MajorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows majors to be viewed or edited.
    """
    queryset = Major.objects.all()
    serializer_class = MajorSerializer

class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows courses to be viewed or edited.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class MentorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows mentors to be viewed or edited.
    """
    queryset = Mentor.objects.all()
    serializer_class = MentorSerializer

class CreateUser(generics.CreateAPIView):
    """
    API endpoint that allows a user to be created.
    """
    permission_classes = tuple()
    
    @transaction.atomic
    def post(self, request):
        if User.objects.filter(email__iexact=request.data['email']).exists():
            raise ValidationError({'error': 'Email already registered'})

        new_user = User.objects.create_user(
            username=request.data['email'],
            email=request.data['email'],
            password=request.data['password'],
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', ''),
        )

        check = re.search(r'^[\w\.]+\@g.ucla.edu$', new_user.email)
        if check is None:
            raise ValidationError({'error': 'Invalid UCLA email'})

        new_profile = Profile(
            user=new_user,
            verification_code = Profile.generate_verification_code(),
        )

        new_profile.save()
        
        url = 'https://bquest.ucladevx.com/verify?code='
        if settings.DEBUG:
            url = 'http://localhost:8000/verify?code='

        from_email =  Email('noreply@bquest.ucladevx.com')
        to_email = Email(new_user.email)
        subject = 'BQuest User Verification'
        verification_link = url + new_profile.verification_code
        content = Content('text/html', 'N/A')
        mail = Mail(from_email, subject, to_email, content)
        mail.personalizations[0].add_substitution(Substitution('-link-', verification_link))
        mail.template_id = USER_VERIFICATION_TEMPLATE
        sg = sendgrid.SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
        response = sg.client.mail.send.post(request_body=mail.get())
        if not (200 <= response.status_code < 300):
            raise ValidationError({'status_code': response.status_code})
        return Response(ProfileSerializer(new_profile).data)
        
class VerifyUser(APIView):
    """
    API endpoint that verifies a user based on profile_id and associated verification code.
    """
    def post(self, request):
        profile_id = self.request.user.profile.id
        profile = get_object_or_404(Profile, id=profile_id)
        if request.data['verification_code'] != profile.verification_code:
            raise ValidationError('Incorrect verification code')

        profile.verified = True
        profile.save()
        return Response({'profile_id': profile_id})


class OwnProfileView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, or destroy the logged in user
    """
    parser_classes = generics.RetrieveUpdateDestroyAPIView.parser_classes + [MultiPartParser]
    serializer_class = ProfileSerializer
    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)


class MentorsSearchView(generics.ListAPIView):
    """
    View for finding a mentor by major
    """
    queryset = Mentor.objects.all().filter(active=True)
    serializer_class = MentorSerializer

    def filter_queryset(self, queryset):
        major = self.request.query_params['major']
        return queryset.filter(major__name=major)


class MentorView(generics.RetrieveAPIView):
    """
    View for getting mentor data by mentor id
    """
    serializer_class = MentorSerializer
    def get_object(self):
        return get_object_or_404(Mentor, id=int(self.kwargs['mentor_id']))


class OwnMentorView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for turning mentor status on (post) and modifying all mentor fields
    """
    serializer_class = MentorSerializer
    def get_object(self):
        return get_object_or_404(Mentor, profile__user=self.request.user)
    serializer_class = MentorSerializer
    def post (self,request):

        profile_id = self.request.user.profile.id
        profile = Profile.objects.get(id=profile_id)
        mentor_request = Mentor.objects.filter(profile__user=self.request.user)
        if not mentor_request.exists():
            mentor = Mentor(profile=profile, active=True)
        else:
            mentor = mentor_request.first()
            mentor.active = True
        mentor.save()

        return Response(MentorSerializer(mentor).data)
