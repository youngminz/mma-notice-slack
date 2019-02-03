from model_utils.models import TimeStampedModel

from django.db import models


class Notice(TimeStampedModel):
    serial_number = models.CharField(max_length=20, db_index=True)

    title = models.CharField(max_length=100)
    writer = models.CharField(max_length=20)
    date = models.DateField()
    view = models.IntegerField()
    content = models.TextField()


class Attachment(TimeStampedModel):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE)

    file_name = models.CharField(max_length=100)
    file_size = models.IntegerField(null=True)
    file_hash = models.CharField(max_length=64)

    downloaded = models.BooleanField()
