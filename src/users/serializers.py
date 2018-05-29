from rest_framework import serializers
from rest_framework.fields import ListField
from drf_writable_nested import WritableNestedModelSerializer
from django.shortcuts import render, get_object_or_404

from django.contrib.auth.models import User, Group
from .models import Profile, Major, Minor, Mentor, Course


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def save(self, *args, **kwargs):
        if 'email' in self.validated_data:
            self.validated_data['username'] = self.validated_data['email']
        super().save(*args, **kwargs)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.CharField(source='user.email')

    class Meta:
        model = Profile
        fields = ('id', 'first_name', 'last_name', 'email', 'year', 'verified', 'picture', 'notifications_enabled', 'phone_number')
        read_only_fields = ('id', 'verified')

    def update(self, instance, validated_data):
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
            for field, val in user_data.items():
                setattr(instance.user, field, val)
            instance.user.save()
        return super().update(instance, validated_data)


class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Major
        fields = ('id', 'name')
        read_only_fields = ('id',)

class MinorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Minor
        fields = ('id', 'name')
        read_only_fields = ('id',)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'name')
        read_only_fields = ('id',)

class MentorSerializer(WritableNestedModelSerializer):
    profile = ProfileSerializer()
    major = MajorSerializer(many=True)
    minor = MinorSerializer(many=True)
    courses = CourseSerializer(many=True)
    class Meta:
        model = Mentor
        fields = ('id', 'profile', 'active', 'major', 'minor', 'bio', 'gpa', 'clubs', 'courses', 'pros', 'cons',)
        read_only_fields = ('id',)


    def update(self, instance, validated_data):
        if 'courses' in validated_data:
            instance.courses.clear()
            courses_obj = validated_data.pop('courses')
            for crs in courses_obj:
                co, _ = Course.objects.get_or_create(name=crs['name'])
                instance.courses.add(co)
                instance.save()

        if 'minor' in validated_data:
            instance.minor.clear()
            minor_obj = validated_data.pop('minor')
            for mnr in minor_obj:
                mi, _ = Minor.objects.get_or_create(name=mnr['name'])
                instance.minor.add(mi)
                instance.save()

        if 'major' in validated_data:
            instance.major.clear()
            major_obj = validated_data.pop('major')
            for mjr in major_obj:
                ma, _ = Major.objects.get_or_create(name=mjr['name'])
                instance.major.add(ma)
                instance.save()


        return super().update(instance, validated_data)


