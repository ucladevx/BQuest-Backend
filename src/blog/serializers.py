#Django Files
from django.contrib.auth.models import User

#DRF files
from rest_framework import serializers

#Source files
from .models import BlogPost, BlogPicture, Comment

class BlogPictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPicture
        fields = ('id','filename','blog', 'picture')


class BlogPostSerializer(serializers.ModelSerializer):
    comments = serializers.IntegerField(source='getComments')
    images = BlogPictureSerializer(many=True)
    class Meta:
        model = BlogPost
        fields = ('id','author','user','body','title','images','publish','anonymous','created','published','updated','comments')
        read_only_fields = ('id','anonymous','created','updated')


class CommentSerializer(serializers.ModelSerializer):
    likes = serializers.IntegerField(source='getLikes')
    user = serializers.IntegerField(source='getUser')
    blog = serializers.IntegerField(source='getBlog')
    comments = serializers.IntegerField(source='getComments')

    class Meta:
        model = Comment
        fields = ('id', 'user','author', 'blog','published','body','likes','comments')

    def get_fields(self):
        fields = super(CommentSerializer, self).get_fields()
        if(self.context.get('depth') is None or self.context.get('depth') == 0):
            return fields
        elif (self.context.get('depth') > 0):
            self.context['depth'] = self.context['depth'] - 1
            fields['comments'] = CommentSerializer(many=True)
            return fields
        else:
            return fields



