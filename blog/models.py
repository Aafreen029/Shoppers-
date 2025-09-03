from django.db import models

# Create your models here.
class Category(models.Model):
    category_name=models.CharField(max_length=50)

    def __str__(self):
        return self.category_name
    

class Post(models.Model):
    title=models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    description = models.TextField()
    thumbnail=models.ImageField(upload_to="upload")

    
    def __str__(self):
        return self.title