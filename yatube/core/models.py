from django.db import models


class AbstractModel(models.Model):
    """Служит для наследования поля pub_date"""

    pub_date = models.DateTimeField(
        verbose_name='Дата публикации', auto_now_add=True
    )

    class Meta:
        abstract = True
