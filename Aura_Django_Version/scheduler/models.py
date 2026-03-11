from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['completed', 'due_date']

    def __str__(self):
        return self.title

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Removing image field to avoid Pillow dependency as we use letter avatars now
    # image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} Profile'
class HealthMetric(models.Model):
    METRIC_CHOICES = [
        ('bp', 'Blood Pressure'),
        ('hr', 'Heart Rate'),
        ('temp', 'Body Temperature'),
        ('spo2', 'SpO2 Level'),
        ('sleep', 'Sleep Duration'),
        ('steps', 'Step Count'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    metric_type = models.CharField(max_length=10, choices=METRIC_CHOICES)
    value = models.CharField(max_length=50)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f'{self.user.username} - {self.get_metric_type_display()}: {self.value}'

class HealthPrediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    risk_score = models.FloatField()  # 0 to 100
    prediction_details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class EmergencyAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, default='Active') # Active, Resolved
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

class FamilyContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.user.username}'s Family)"

class MedicalImage(models.Model):
    IMAGE_TYPE_CHOICES = [
        ('skin', 'Skin/Rash Analysis'),
        ('prescription', 'Prescription Scanning'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='medical_images/')
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPE_CHOICES)
    analysis_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class DietPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    goal = models.CharField(max_length=100) # e.g., Weight Loss, Muscle Gain
    plan_data = models.JSONField() # Stores breakfast, lunch, dinner, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.goal} Diet Plan"
