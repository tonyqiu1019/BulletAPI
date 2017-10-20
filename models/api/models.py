from django.db import models

# the bullet object
class Bullet(models.Model):
    # required fields
    content = models.CharField(max_length=512)
    ret_time = models.DateTimeField(blank=True, null=True)
    post_time = models.DateTimeField(blank=True, null=True)

    # optional fields
    info = models.ForeignKey('Info', on_delete=models.SET_NULL,
        blank=True, null=True)
    color = models.CharField(max_length=6, blank=True, default="000000")
    font_size = models.PositiveSmallIntegerField(blank=True, default=12)
    display_mode = models.CharField(max_length=1, blank=True, choices=(
        ('f', 'fixed'),
        ('s', 'scroll'),
    ), default='s')

    def __str__(self):
        if len(self.content) >= 13: return self.content[:10] + '...'
        else: return self.content

    class Meta:
        ordering = ['ret_time', 'post_time']

# the user info about a bullet
class Info(models.Model):
    fingerprint = models.BigIntegerField(unique=True)
    user_agent = models.CharField(max_length=1024, blank=True)
