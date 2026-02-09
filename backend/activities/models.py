from django.db import models

class ActivityCode(models.Model):
    """Справочник ГКЭД (ОКЭД) Кыргызстана."""
    code = models.CharField(max_length=20, unique=True, verbose_name="Код (ГКЭД)")
    section = models.CharField(max_length=5, verbose_name="Секция")
    name = models.TextField(verbose_name="Наименование деятельности")

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "Вид деятельности"
        verbose_name_plural = "Виды деятельности"