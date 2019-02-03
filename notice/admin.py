from django.contrib import admin

from .models import Attachment, Notice


class AttachmentInline(admin.StackedInline):
    model = Attachment
    extra = 0


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("pk", "serial_number", "title", "writer", "date", "view")
    inlines = (AttachmentInline,)
    ordering = ("-date",)
