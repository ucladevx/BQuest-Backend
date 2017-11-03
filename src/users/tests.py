# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework.test import APIClient, APITestCase

from django.contrib.auth.models import User
from .models import Profile, Mentor, Major
from . import factories

# Create your tests here.

class CreateUserTest(APITestCase):
    create_url = reverse('users:create')

    def tearDown(self):
        User.objects.all().delete()
        Profile.objects.all().delete()

    def test_create_user_has_profile_and_user(self):
        user_params = {
            'email': 'test@test.com',
            'password': 'password',
            'first_name': 'first',
            'last_name': 'last',
        }

        resp = self.client.post(
            self.create_url,
            data=user_params,
        )

        user = User.objects.get(email=user_params['email'])
        profile = Profile.objects.get(user=user)

        self.assertEqual(user.email, user_params['email'])
        self.assertEqual(user.first_name, user_params['first_name'])
        self.assertEqual(user.last_name, user_params['last_name'])

    def test_user_username_and_email_equal(self):
        user_params = {
            'email': 'test2@test.com',
            'password': 'password',
            'first_name': 'first',
            'last_name': 'last',
        }

        resp = self.client.post(
            self.create_url,
            data=user_params,
        )

        user = User.objects.get(email=user_params['email'])
        self.assertEqual(user.email, user.username)

class OwnProfileViewTest(APITestCase):
    own_profile_url = reverse('users:me')
    def setUp(self):
        self.profile = factories.ProfileFactory()
        self.client.force_authenticate(user=self.profile.user)

    def tearDown(self):
        User.objects.all().delete()
        Profile.objects.all().delete()

    def test_own_profile_returns_own_profile(self):
        resp = self.client.get(self.own_profile_url)
        self.assertEqual(self.profile.user.email, resp.data['user']['email'])

class MentorsSearchTest(APITestCase):
    mentors_search_url = reverse('users:mentors_search')
    def setUp(self):
        self.major = factories.MajorFactory(name='Test Major')
        self.mentor = factories.MentorFactory(major=self.major)
        self.client.force_authenticate(user=self.mentor.profile.user)

    def tearDown(self):
        User.objects.all().delete()
        Major.objects.all().delete()

    def test_correct_major_name_filtering(self):
        resp = self.client.get(
            self.mentors_search_url,
            data={
                'major': self.major.name,
            },
        )

        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['major']['name'], self.mentor.major.name)

    def test_incorrect_major_name_filtering(self):
        resp = self.client.get(
            self.mentors_search_url,
            data={
                'major': self.mentor.major.name + 'wonrg',
            },
        )

        self.assertEqual(resp.data['count'], 0)

