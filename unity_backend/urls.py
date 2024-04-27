from django.contrib import admin
from django.urls import path
from .views import LeaderboardEntryUpdateView, LeaderboardEntryCreateView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Leaderboard URLs
    path('leaderboard/<int:pk>/', LeaderboardEntryUpdateView.as_view(), name='leaderboard-update'),
    path('leaderboard/create/', LeaderboardEntryCreateView.as_view(), name='leaderboard-create'),
    
    # Friend Request URLs
    path('friends/request/', views.FriendRequestCreateView.as_view(), name='friend-request-create'),
    path('friends/request/<int:request_id>/accept/', views.FriendRequestAcceptView.as_view(), name='friend-request-accept'),
    path('friends/request/<int:request_id>/', views.FriendRequestDeclineView.as_view(), name='friend-request-decline'), 
    path('friends/<int:user_id>/', views.FriendListAPIView.as_view(), name='friend-list'),
    
    # Guild URLs
    path('guilds/', views.GuildCreateView.as_view(), name='guild-create'),
    path('guilds/<int:guild_id>/join/', views.GuildJoinView.as_view(), name='guild-join'),
    path('guilds/<int:guild_id>/leave/', views.GuildLeaveView.as_view(), name='guild-leave'),
    path('guilds/<int:guild_id>/manage/', views.GuildManageMembersView.as_view(), name='guild-manage'),

    # Chat URL
    path('messages/', views.MessageCreateView.as_view(), name='message-create'),
    path('messages/one-on-one/<int:user_id>/', views.OneOnOneChatMessageListView.as_view(), name='one-on-one-chat'),
    path('messages/guild/<int:guild_id>/', views.GuildChatMessageListView.as_view(), name='guild-chat'),
    path('messages/global/', views.GlobalChatMessageListView.as_view(), name='global-chat'),
]