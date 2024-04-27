from rest_framework import serializers
from .models import LeaderboardEntry, Friend, Guild, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')  
        # Adjust the 'fields' as needed
        
class LeaderboardEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaderboardEntry
        fields = ('player', 'gamename', 'score')

class FriendSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='friend.username') # Fetch friend's username

    class Meta:
        model = Friend
        fields = ('id', 'user', 'username', 'status')  
        read_only_fields = ('status',) 

class GuildSerializer(serializers.ModelSerializer):
    leader_username = serializers.ReadOnlyField(source='leader.username') 
    members_count = serializers.SerializerMethodField()  # Count of guild members

    class Meta:
        model = Guild
        fields = ('id', 'name', 'description', 'leader', 'leader_username', 'members_count')

    def get_members_count(self, obj):
        return obj.members.count()

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='sender.username') 
    recipient_username = serializers.ReadOnlyField(source='recipient.username', allow_null=True) 

    class Meta:
        model = Message
        fields = ('id', 'sender', 'sender_username', 'recipient', 'recipient_username', 'chat_type', 'content', 'timestamp', 'delivered')