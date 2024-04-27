from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,  permissions
from rest_framework.pagination import PageNumberPagination
from .models import LeaderboardEntry, Friend, Guild, Message, User, GuildMembership
from .serializers import LeaderboardEntrySerializer, UserSerializer, GuildSerializer, MessageSerializer
from asgiref.sync import sync_to_async 
from channels.layers import get_channel_layer
from . import serializers
from django.shortcuts import get_object_or_404

class LeaderboardEntryUpdateView(APIView):
    def put(self, request, pk, format=None):
        try:
            entry = LeaderboardEntry.objects.get(pk=pk)
            serializer = LeaderboardEntrySerializer(entry, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except LeaderboardEntry.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
class LeaderboardEntryCreateView(APIView):
    def post(self, request, format=None):
        serializer = LeaderboardEntrySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# Friend Requests
class FriendRequestCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        recipient_id = request.data.get('recipient', None)
        try:
            recipient = User.objects.get(id=recipient_id)
            Friend.objects.create(user=request.user, friend=recipient, status='pending')
            return Response({'message': 'Friend request sent'}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class FriendRequestAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, request_id, format=None):
        try:
            friend_request = Friend.objects.get(id=request_id, recipient=request.user)
            if friend_request.status != 'pending':
                return Response({'error': 'Request is not pending'}, status=status.HTTP_400_BAD_REQUEST)

            friend_request.status = 'accepted'
            friend_request.save()
            return Response({'message': 'Friend request accepted'}, status=status.HTTP_200_OK)
        except Friend.DoesNotExist:
            return Response({'error': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)

class FriendRequestDeclineView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, request_id, format=None):
        try:
            friend_request = Friend.objects.get(id=request_id, recipient=request.user)
            friend_request.delete()
            return Response({'message': 'Friend request declined'}, status=status.HTTP_200_OK)
        except Friend.DoesNotExist:
            return Response({'error': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)

class FriendListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id, format=None):
        user = get_object_or_404(User, pk=user_id) 

        friendships = Friend.objects.filter(
            Q(user=user) | Q(friend=user),
            status='accepted' 
        )

        friend_ids = friendships.values_list('user_id', 'friend_id') 

        # Remove the requesting user's ID from results 
        friends = User.objects.filter(id__in=friend_ids).exclude(id=user_id)

        serializer = UserSerializer(friends, many=True) # Replace with your User serializer
        return Response(serializer.data, status=status.HTTP_200_OK)
# Guilds
class GuildCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        serializer = GuildSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(leader=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GuildJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, guild_id, format=None):
        try:
            guild = Guild.objects.get(id=guild_id)
            guild.members.add(request.user)
            return Response({'message': 'Joined guild'}, status=status.HTTP_200_OK)
        except Guild.DoesNotExist:
            return Response({'error': 'Guild not found'}, status=status.HTTP_404_NOT_FOUND)

class GuildLeaveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, guild_id, format=None):
        try:
            guild = Guild.objects.get(id=guild_id)
            if request.user in guild.members.all():
                guild.members.remove(request.user)
                return Response({'message': 'Left guild'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Not a member of this guild'}, status=status.HTTP_400_BAD_REQUEST)
        except Guild.DoesNotExist:
            return Response({'error': 'Guild not found'}, status=status.HTTP_404_NOT_FOUND)
        
class GuildManageMembersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, guild_id, format=None):
        try:
            guild = Guild.objects.get(id=guild_id)
            member_id = request.data.get('member_id')
            action = request.data.get('action')

            if action == 'promote':
                self._promote_member(guild, member_id)
            elif action == 'demote':
                self._demote_member(guild, member_id)
            elif action == 'remove':
                self._remove_member(guild, member_id)
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'message': 'Guild membership updated'}, status=status.HTTP_200_OK)

        except Guild.DoesNotExist:
            return Response({'error': 'Guild not found'}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({'error': 'Member not found'}, status=status.HTTP_404_NOT_FOUND)

    def _promote_member(self, guild, member_id):
        try:
            membership = GuildMembership.objects.get(guild=guild, user_id=member_id)
            if membership.role != Guild.LEADER:  # Can't promote a leader
                membership.role = Guild.OFFICER
                membership.save()
        except GuildMembership.DoesNotExist:
            pass  # Member not found, ignore

    def _demote_member(self, guild, member_id):
        try:
            membership = GuildMembership.objects.get(guild=guild, user_id=member_id)
            if membership.role != Guild.MEMBER:  # Can't demote below member
                membership.role = Guild.MEMBER
                membership.save()
        except GuildMembership.DoesNotExist:
            pass  

    def _remove_member(self, guild, member_id):
        try:
            member = User.objects.get(id=member_id)
            if member != guild.leader:  # Can't remove the leader
                guild.members.remove(member)
        except User.DoesNotExist:
            pass  

# Chat
class MessageCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_chat_group_name(self, request):
        chat_type = request.data.get('chat_type')
        if chat_type == 'one-on-one':
            recipient_id = request.data.get('recipient')
            # Ensure order to have consistent group names between users
            user_ids = sorted([request.user.id, recipient_id]) 
            return f'chat.one-on-one.{user_ids[0]}-{user_ids[1]}' 
        elif chat_type == 'guild':
            guild_id = request.data.get('guild')
            return f'chat.guild.{guild_id}' 
        else:  # Global chat
            return 'chat.global' 
        
    async def post(self, request, format=None):
        chat_type = request.data.get('chat_type')
        if chat_type == 'one-on-one':
            recipient_id = request.data.get('recipient')
            try: 
                User.objects.get(id=recipient_id)  # Ensure recipient exists
            except User.DoesNotExist:
                return Response({'error': 'Recipient not found'}, status=status.HTTP_400_BAD_REQUEST)

        elif chat_type == 'guild':
            guild_id = request.data.get('guild')
            try:
                guild = Guild.objects.get(id=guild_id)
                if request.user not in guild.members.all():
                    return Response({'error': 'Not a member of this guild'}, status=status.HTTP_403_FORBIDDEN)
            except Guild.DoesNotExist:
                return Response({'error': 'Guild not found'}, status=status.HTTP_404_NOT_FOUND) 

        else:  
            pass 

        channel_layer = get_channel_layer()
        chat_group_name = self.get_chat_group_name(request)
        await sync_to_async(channel_layer.group_send)(
            chat_group_name,
            {
                'type': 'chat_message',  
                'message': serializers.data 
            }
        )
        return Response(serializers.data, status=status.HTTP_201_CREATED)


class MessageListPagination(PageNumberPagination):
    page_size = 25 # Adjust as needed

class OneOnOneChatMessageListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id, format=None):
        try:
            recipient = User.objects.get(id=user_id)
            messages = Message.objects.filter(
                chat_type='one-on-one',
                # Ensure messages are between the current user and the recipient
                sender__in=[request.user, recipient],
                recipient__in=[request.user, recipient]
            ).order_by('timestamp')

            paginator = MessageListPagination()
            page = paginator.paginate_queryset(messages, request)
            serializer = MessageSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class GuildChatMessageListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, guild_id, format=None):
        try:
            guild = Guild.objects.get(id=guild_id)
            if request.user not in guild.members.all():
                 return Response({'error': 'Not a member of this guild'}, status=status.HTTP_403_FORBIDDEN)

            messages = Message.objects.filter(
                guild=guild,
                chat_type='guild'
            ).order_by('timestamp')

            paginator = MessageListPagination()  
            page = paginator.paginate_queryset(messages, request)
            serializer = MessageSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Guild.DoesNotExist:
            return Response({'error': 'Guild not found'}, status=status.HTTP_404_NOT_FOUND)


class GlobalChatMessageListView(APIView):
    permission_classes = [permissions.IsAuthenticated]  # Or allow unauthenticated users as needed

    def get(self, request, format=None):
        messages = Message.objects.filter(chat_type='global').order_by('timestamp')
        paginator = MessageListPagination()
        page = paginator.paginate_queryset(messages, request)
        serializer = MessageSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    