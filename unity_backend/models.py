from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class PlayerProfile(models.Model):
    app_label = 'unity_backend' 
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    progress = models.TextField()  
    stats = models.JSONField()   
    preferences = models.JSONField() 
    
class LeaderboardEntry(models.Model):
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    gamename = models.CharField(max_length=100)
    score = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
class Friend(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_friends')
    friend = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='friends')
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted')], default='pending')

class Guild(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    leader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='guilds_led')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='guilds')
    MEMBER = 'member'
    OFFICER = 'officer'
    LEADER = 'leader'
    ROLE_CHOICES = [
        (MEMBER, 'Member'),
        (OFFICER, 'Officer'),
        (LEADER, 'Leader')
    ]
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='guilds', through='GuildMembership') # Adding a through model

class GuildMembership(models.Model):
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Guild.ROLE_CHOICES, default=Guild.MEMBER)

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)  # For individual messages
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE, related_name='messages', null=True, blank=True) # For group messages
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    CHAT_TYPE_CHOICES = [
        ('one-on-one', 'One-on-One'),
        ('guild', 'Guild'),
        ('global', 'Global')
    ]
    chat_type = models.CharField(max_length=15, choices=CHAT_TYPE_CHOICES)
    delivered = models.BooleanField(default=False) 
