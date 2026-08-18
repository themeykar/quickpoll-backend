from django.contrib import admin

from .models import Option, Poll, Vote


class OptionInline(admin.TabularInline):
    model = Option
    extra = 2


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_closed', 'created_at')
    list_filter = ('is_closed',)
    readonly_fields = ('admin_token', 'created_at')
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'poll', 'order')
    list_filter = ('poll',)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter_name', 'option', 'poll', 'created_at')
    list_filter = ('poll',)
    readonly_fields = ('created_at',)
