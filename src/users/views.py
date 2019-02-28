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
from django.db.models import Q
from django.http import HttpResponse
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.functions import Greatest


from .models import Profile, Major, Minor, Mentor, Course
from .serializers import (
    UserSerializer, GroupSerializer, ProfileSerializer, MajorSerializer, 
    MinorSerializer, MentorSerializer, CourseSerializer,
)

import sendgrid
from sendgrid.helpers.mail import Email, Content, Substitution, Mail
from pickmybruin.settings import USER_VERIFICATION_TEMPLATE, PASSWORD_RESET_TEMPLATE
from data_collection.helpers import log

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

class MinorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows minors to be viewed or edited.
    """
    queryset = Minor.objects.all()
    serializer_class = MinorSerializer

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


class ResendVerifyUser(APIView):
    def post (self, request):
        email = self.request.user.email
        verification_code = self.request.user.profile.verification_code

        url = 'https://bquest.ucladevx.com/verify?code='
        if settings.DEBUG:
            url = 'http://localhost:8000/verify?code='
        from_email =  Email('noreply@bquest.ucladevx.com')
        to_email = Email(email)
        subject = 'BQuest User Verification'
        verification_link = url + verification_code 
        content = Content('text/html', 'N/A')
        mail = Mail(from_email, subject, to_email, content)
        mail.personalizations[0].add_substitution(Substitution('-link-', verification_link))
        mail.template_id = USER_VERIFICATION_TEMPLATE
        sg = sendgrid.SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
        response = sg.client.mail.send.post(request_body=mail.get())
        if not (200 <= response.status_code < 300):
            raise ValidationError({'sendgrid_status_code': response.status_code})
        return Response(ProfileSerializer(self.request.user.profile).data)

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

class SendPasswordReset(APIView):
    permission_classes = tuple()
    def post (self, request):
        email = request.data['username']
        user = User.objects.get(username=email)

        profile_id = user.profile.id
        profile = Profile.objects.get(id=profile_id)
        profile.password_reset_code = Profile.generate_password_reset_code()
        profile.save()
        url = 'https://bquest.ucladevx.com/password'
        if settings.DEBUG:
            url = 'http://localhost:8000/password'
        
        from_email =  Email('noreply@bquest.ucladevx.com')
        to_email = Email(email)
        subject = 'BQuest User Password Reset'
        reset_link = "{}?code={}&userid={}".format(url, profile.password_reset_code, user.id)
        content = Content('text/html', 'N/A')
        mail = Mail(from_email, subject, to_email, content)
        mail.personalizations[0].add_substitution(Substitution('password_reset_link', reset_link))
        mail.template_id = PASSWORD_RESET_TEMPLATE

        sg = sendgrid.SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
        response = sg.client.mail.send.post(request_body=mail.get())
        if not (200 <= response.status_code < 300):
            raise ValidationError({'sendgrid_status_code': response.status_code})
        return HttpResponse(status=200)

class PasswordReset(APIView):
    permission_classes = tuple()
    def post(self, request):
        code = request.data['code']
        userid = request.data['userid']
        profile = Profile.objects.get(password_reset_code=code)
        user = User.objects.get(profile=profile)
        if userid != str(user.id):
            return HttpResponse(status=400)
        user.set_password(request.data['password'])
        profile.password_reset_code = None
        user.save()
        profile.save()
        return HttpResponse(status=200)
        


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
    View for finding a mentor by major, year
    """
    queryset = Mentor.objects.all().filter(active=True)
    serializer_class = MentorSerializer


    def filter_queryset(self, queryset):
        queryset = queryset.exclude(profile__user=self.request.user) 

        trans_dict = {
            'first' : '1st', 
            'second' : '2nd',
            'third' : '3rd', 
            'fourth' : '4th',
            'freshman' : '1st', 
            'sophomore' : '2nd',
            'junior' : '3rd', 
            'senior' : '4th',
            'cs' : 'computer science',
            'computer science' : 'CS',
        }  

        major_dict = {

                'cs' : 'computer science',
                'bio' : 'biology'
        }

        if 'query' in self.request.GET:
            query = self.request.GET['query']
            query = query.split(' ')

            for item in query:
                item_alias = trans_dict.get(item.lower(),item)
                queryset = queryset.annotate( 
                    similarity=Greatest(
                        TrigramSimilarity('major__name', item),
                        TrigramSimilarity('bio', item),
                        TrigramSimilarity('profile__year', item),
                        TrigramSimilarity('profile__user__first_name', item),
                        TrigramSimilarity('profile__user__last_name', item),
                        TrigramSimilarity('minor__name', item),
                        TrigramSimilarity('profile__year', item),
                        TrigramSimilarity('courses__name', item),
                        TrigramSimilarity('major__name', item_alias),
                        TrigramSimilarity('bio', item_alias),
                        TrigramSimilarity('profile__year', item_alias),
                        TrigramSimilarity('profile__user__first_name', item_alias),
                        TrigramSimilarity('profile__user__last_name', item_alias),
                        TrigramSimilarity('minor__name', item_alias),
                        TrigramSimilarity('profile__year', item_alias),
                        TrigramSimilarity('courses__name', item_alias),
                    )
                ).filter(similarity__gte=0.10).order_by('-similarity')


        if 'random' in self.request.GET:
            num_random = self.request.GET['random']
            if num_random.isdigit():
                num_random = int(num_random)
            else:
                num_random = queryset.count()
            queryset = queryset.order_by('?')[:num_random]
        return queryset

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

class ReportUser(APIView):
    def post (self, request):
        email = self.request.user.email

        reported_id = int(request.data['reported_id'])
        reason = request.data['reason']
        reported_profile = get_object_or_404(Profile, id=reported_id)
        
        message = 'User {} {} ({}) has reported {} {} ({}) for the following reason:\n{}'.format(
            self.request.user.first_name,
            self.request.user.last_name,
            self.request.user.email,
            reported_profile.user.first_name,
            reported_profile.user.last_name,
            reported_profile.user.email,
            reason)
        from_email =  Email(email)
        to_email = Email('bquest.ucla@gmail.com')
        subject = '[URGENT] BQuest Reported User'
        content = Content('text/html', message)
        mail = Mail(from_email, subject, to_email, content)

        sg = sendgrid.SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
        response = sg.client.mail.send.post(request_body=mail.get())
        if not (200 <= response.status_code < 300):
            raise ValidationError({'sendgrid_status_code': response.status_code})
        return HttpResponse(status=200)
        
