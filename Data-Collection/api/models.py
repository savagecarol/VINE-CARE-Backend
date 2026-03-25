from django.db import models

# Create your models here.
from django.db import models

class DataCollection(models.Model):
    block         = models.CharField(max_length=255)
    meters        = models.IntegerField()
    image_url     = models.URLField(max_length=500)
    original_name = models.CharField(max_length=255)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Block {self.block} — {self.meters}m — {self.original_name}"