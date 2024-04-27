from django.contrib import admin
from .models import LeaderboardEntry, Friend, Guild, Message, GuildMembership

admin.site.register(LeaderboardEntry)
admin.site.register(Friend)
admin.site.register(Guild)
admin.site.register(GuildMembership)
admin.site.register(Message)