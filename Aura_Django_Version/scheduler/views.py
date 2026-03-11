from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from .models import Task, HealthMetric, HealthPrediction, EmergencyAlert, FamilyContact, MedicalImage, DietPlan
from .forms import TaskForm, UserUpdateForm, HealthMetricForm, FamilyContactForm, MedicalImageForm, DietPlanForm
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
try:
    from twilio.rest import Client
except ImportError:
    Client = None
import json
try:
    import joblib
    import numpy as np
except ImportError:
    joblib = None
    np = None
import os
try:
    from PIL import Image
    import pytesseract
except ImportError:
    pass
import calendar
from datetime import date, timedelta
from django.utils import timezone

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome {user.username}.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'scheduler/landing.html')

@login_required
def dashboard(request):
    tasks = Task.objects.filter(user=request.user)
    
    # --- Search and Filtering ---
    query = request.GET.get('q')
    priority = request.GET.get('priority')
    status = request.GET.get('status')
    sort = request.GET.get('sort', 'due_date') # Default sort

    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if priority:
        tasks = tasks.filter(priority=priority)
    if status:
        completed = True if status == 'completed' else False
        tasks = tasks.filter(completed=completed)
    
    if sort:
        tasks = tasks.order_by(sort)
    # ----------------------------

    # Calculate stats
    total_tasks = tasks.count()
    pending_count = tasks.filter(completed=False).count()
    completed_count = tasks.filter(completed=True).count()
    high_priority_count = tasks.filter(priority='high', completed=False).count()
    
    progress = 0
    if total_tasks > 0:
        progress = int((completed_count / total_tasks) * 100)

    # Get next due task for circular timer
    next_due_task = Task.objects.filter(user=request.user, completed=False, due_date__isnull=False, due_date__gte=timezone.now()).order_by('due_date').first()

    context = {
        'tasks': tasks,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'high_priority_count': high_priority_count,
        'progress': progress,
        'next_due_task': next_due_task,
        'search_query': query,
        # Flags for template selection to avoid '==' issues
        'priority_high': priority == 'high',
        'priority_medium': priority == 'medium',
        'priority_low': priority == 'low',
        'status_pending': status == 'pending',
        'status_completed': status == 'completed',
        'sort_due_date': sort == 'due_date',
        'sort_due_date_desc': sort == '-due_date',
        'sort_priority': sort == 'priority',
    }
    return render(request, 'scheduler/dashboard.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)

    context = {
        'u_form': u_form,
    }
    return render(request, 'scheduler/profile.html', context)

@login_required
def calendar_view(request):
    # Get current year and month from GET params or default to today
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # helper for prev/next navigation
    first = date(year, month, 1)
    prev_month = first - timedelta(days=1)
    next_month = first + timedelta(days=32)
    
    # Get tasks for this month to highlight days
    # Filtering efficiently for the month
    tasks = Task.objects.filter(
        user=request.user, 
        due_date__year=year, 
        due_date__month=month
    )
    
    # Group tasks by day: {1: True, 5: True, ...}
    days_with_tasks = set()
    for t in tasks:
        if t.due_date:
            days_with_tasks.add(t.due_date.day)

    # Create calendar
    cal = calendar.monthcalendar(year, month)
    
    context = {
        'calendar': cal,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'days_with_tasks': days_with_tasks,
        'prev_year': prev_month.year,
        'prev_month': prev_month.month,
        'next_year': next_month.year,
        'next_month': next_month.month,
    }
    return render(request, 'scheduler/calendar.html', context)

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, 'Task created successfully!')
            return redirect('dashboard')
    else:
        form = TaskForm()
    return render(request, 'scheduler/task_form.html', {'form': form, 'title': 'Create Task'})

@login_required
def update_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully!')
            return redirect('dashboard')
    else:
        form = TaskForm(instance=task)
    return render(request, 'scheduler/task_form.html', {'form': form, 'title': 'Update Task'})

@login_required
def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('dashboard')
    return render(request, 'scheduler/task_confirm_delete.html', {'task': task})

@login_required
def toggle_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.completed = not task.completed
    task.save()
    return redirect('dashboard')

@login_required
def health_metrics(request):
    metrics = HealthMetric.objects.filter(user=request.user)
    if request.method == 'POST':
        form = HealthMetricForm(request.POST)
        if form.is_valid():
            metric = form.save(commit=False)
            metric.user = request.user
            metric.save()
            messages.success(request, 'Health metric recorded!')
            return redirect('health_metrics')
    else:
        form = HealthMetricForm()
    
    return render(request, 'scheduler/health_metrics.html', {'metrics': metrics, 'form': form})

@login_required
def ai_assistant(request):
    return render(request, 'scheduler/ai_assistant.html')

@login_required
def ai_response(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '').lower()
        
        # Simple AI Symptom Checker / Health Logic
        response = "I'm Aura, your AI health assistant. "
        
        if 'headache' in user_message or 'sir dard' in user_message or 'tala noppi' in user_message:
            response += "A headache can be caused by dehydration, stress, or tension. Ensure you're drinking enough water and resting. (सर दर्द पानी की कमी या तनाव से हो सकता है / తలనొప్పి నీటి కొరత లేదా ఒత్తిడి వల్ల రావచ్చు)"
        elif 'fever' in user_message or 'bukhaar' in user_message or 'jwaram' in user_message:
            response += "A fever often indicates your body is fighting an infection. Rest, stay hydrated, and monitor your temperature carefully. (बुखार संक्रमण का लक्षण है / జ్వరం అలసట లేదా ఇతర ఆరోగ్య సమస్యల వల్ల రావచ్చు)"
        elif 'diet' in user_message or 'food' in user_message or 'khana' in user_message:
            response += "A balanced diet with protein, healthy fats, and lots of vegetables is key. Avoid processed sugars and keep your portions controlled."
        elif 'exercise' in user_message or 'workout' in user_message:
            response += "Try at least 30 minutes of moderate activity daily, like brisk walking or yoga. It significantly reduces health risk scores."
        elif 'hello' in user_message or 'hi' in user_message or 'namaste' in user_message:
            response += "Hello! How can I help you with your health today? I can suggest diets, exercises, or check symptoms. (नमस्ते! मैं आपकी सेहत में कैसे मदद कर सकता हूँ?)"
        else:
            response += "I'm here to help. Could you tell me more about your symptoms or what health metrics you'd like to track?"
            
        return JsonResponse({'response': response})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def trigger_sos(request):
    if request.method == 'POST':
        alert = EmergencyAlert.objects.create(user=request.user)
        # Simulation: Send SMS/Email to Admin
        print(f"!!! EMERGENCY SOS ALERT TRIGGERED BY {request.user.username} !!!")
        return JsonResponse({'status': 'success', 'alert_id': alert.id})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@staff_member_required
def admin_dashboard(request):
    users_count = User.objects.count()
    total_alerts = EmergencyAlert.objects.count()
    active_alerts = EmergencyAlert.objects.filter(status='Active')
    
    # Recent Health Trends across all users
    recent_metrics = HealthMetric.objects.order_by('-recorded_at')[:20]
    
    # AI Predictions overview
    predictions = HealthPrediction.objects.all().order_by('-created_at')[:10]

    # Recent Medical Images
    recent_images = MedicalImage.objects.all().order_by('-created_at')[:5]

    context = {
        'users_count': users_count,
        'total_alerts': total_alerts,
        'active_alerts': active_alerts,
        'recent_metrics': recent_metrics,
        'predictions': predictions,
        'recent_images': recent_images,
    }
    return render(request, 'scheduler/admin_dashboard.html', context)

@login_required
def health_data_api(request):
    # Load AI Model
    model_path = 'scheduler/ml_models/health_risk_model.pkl'
    risk_score = 15.0 # Baseline
    
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        # Get latest metrics for user
        latest_hr = HealthMetric.objects.filter(user=request.user, metric_type='hr').first()
        latest_temp = HealthMetric.objects.filter(user=request.user, metric_type='temp').first()
        
        # Simulated features for prediction if real ones are missing
        hr_val = float(latest_hr.value) if latest_hr else 72.0
        temp_val = float(latest_temp.value) if latest_temp else 98.6
        age_val = 30 # Simulation, usually from profile
        sbp_val = 120
        steps_val = 5000
        
        features = np.array([[age_val, hr_val, sbp_val, temp_val, steps_val]])
        prediction_prob = model.predict_proba(features)[0][1] # Probability of target=1
        risk_score = round(prediction_prob * 100, 2)
        
        # Trigger Family SMS if risk is high
        if risk_score > 70:
            send_family_sms(request.user, risk_score)

        # Save prediction
        HealthPrediction.objects.create(
            user=request.user,
            risk_score=risk_score,
            prediction_details={'hr': hr_val, 'temp': temp_val, 'sbp': sbp_val}
        )

    # Get latest metrics for UI cards
    latest_hr = HealthMetric.objects.filter(user=request.user, metric_type='hr').first()
    latest_temp = HealthMetric.objects.filter(user=request.user, metric_type='temp').first()
    latest_spo2 = HealthMetric.objects.filter(user=request.user, metric_type='spo2').first()
    latest_bp = HealthMetric.objects.filter(user=request.user, metric_type='bp').first()

    # Get trend data for Chart.js
    hr_metrics = HealthMetric.objects.filter(user=request.user, metric_type='hr').order_by('recorded_at')[:10]
    spo2_metrics = HealthMetric.objects.filter(user=request.user, metric_type='spo2').order_by('recorded_at')[:10]
    
    labels = [m.recorded_at.strftime("%a %H:%M") for m in hr_metrics]
    hr_values = [float(m.value) for m in hr_metrics]
    spo2_values = [float(m.value) for m in spo2_metrics]

    return JsonResponse({
        'risk_score': risk_score,
        'latest_vitals': {
            'hr': latest_hr.value if latest_hr else '72',
            'temp': latest_temp.value if latest_temp else '98.6',
            'spo2': latest_spo2.value if latest_spo2 else '98',
            'bp': latest_bp.value if latest_bp else '120/80',
        },
        'labels': labels,
        'hr_values': hr_values,
        'spo2_values': spo2_values,
    })

@login_required
def manage_family(request):
    contacts = FamilyContact.objects.filter(user=request.user)
    if request.method == 'POST':
        form = FamilyContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            messages.success(request, 'Family contact added!')
            return redirect('manage_family')
    else:
        form = FamilyContactForm()
    return render(request, 'scheduler/family_sync.html', {'contacts': contacts, 'form': form})

def send_family_sms(user, risk_score):
    # Twilio Configuration (Simulated with placeholders)
    # account_sid = 'your_sid'
    # auth_token = 'your_token'
    # client = Client(account_sid, auth_token)
    
    contacts = FamilyContact.objects.filter(user=user)
    for contact in contacts:
        message_body = f"AuraHealth Alert: {user.username}'s health risk score is elevated ({risk_score}%). Please check in on them."
        print(f"--- SIMULATED SMS TO {contact.phone_number} ---")
        print(f"Message: {message_body}")
        # client.messages.create(body=message_body, from_='+1234567890', to=contact.phone_number)

@login_required
def medical_image_analysis(request):
    images = MedicalImage.objects.filter(user=request.user)
    if request.method == 'POST' and request.FILES.get('image'):
        form = MedicalImageForm(request.POST, request.FILES)
        if form.is_valid():
            med_image = form.save(commit=False)
            med_image.user = request.user
            
            # Simulate AI Analysis
            img_type = request.POST.get('image_type')
            result = {}
            
            if img_type == 'skin':
                # Simulated Skin Analysis
                result = {
                    'diagnosis': 'Potential Contact Dermatitis',
                    'confidence': '85%',
                    'suggestion': 'Wash the area with mild soap. Apply hydrocortisone cream. Avoid scratching.',
                    'care': 'Keep the skin hydrated. If redness spreads or itching intensifies, consult a dermatologist.'
                }
            elif img_type == 'prescription':
                # Simulated Prescription OCR & Analysis
                result = {
                    'medicines': ['Amoxicillin 500mg', 'Paracetamol 650mg'],
                    'instruction': 'Take Amoxicillin twice a day after meals. Paracetamol as needed for fever.',
                    'care': 'Complete the full course of antibiotics even if you feel better.'
                }
                
            med_image.analysis_result = result
            med_image.save()
            messages.success(request, 'Medical image analyzed successfully!')
            return redirect('image_analysis')
    else:
        form = MedicalImageForm()
    
    return render(request, 'scheduler/image_analysis.html', {'images': images, 'form': form})

@login_required
def diet_plans(request):
    latest_plan = DietPlan.objects.filter(user=request.user).order_by('-created_at').first()
    
    if request.method == 'POST':
        form = DietPlanForm(request.POST)
        if form.is_valid():
            goal = form.cleaned_data['goal']
            
            # Simple Automated Diet Generation Logic
            plan_data = {}
            if goal == 'weight_loss':
                plan_data = {
                    'breakfast': 'Oatmeal with berries and a handful of almonds.',
                    'lunch': 'Grilled chicken salad with plenty of leafy greens and olive oil dressing.',
                    'dinner': 'Baked salmon with steamed broccoli and a small portion of quinoa.',
                    'snack': 'Greek yogurt or an apple.',
                    'tip': 'Drink at least 3 liters of water today.'
                }
            elif goal == 'muscle_gain':
                plan_data = {
                    'breakfast': 'Scrambled eggs (3) with whole-grain toast and avocado.',
                    'lunch': 'Turkey breast with brown rice and roasted sweet potatoes.',
                    'dinner': 'Lean beef stir-fry with mixed vegetables and noodles.',
                    'snack': 'Protein shake and a banana.',
                    'tip': 'Ensure you get 8 hours of sleep for muscle recovery.'
                }
            elif goal == 'diabetes_friendly':
                plan_data = {
                    'breakfast': 'Chia seed pudding with unsweetened almond milk.',
                    'lunch': 'Lentil soup with a side of sautéed spinach.',
                    'dinner': 'Grilled tofu or fish with cauliflower rice.',
                    'snack': 'Raw walnuts or cucumber slices with hummus.',
                    'tip': 'Monitor your glucose levels before and after meals.'
                }
            else: # Balanced
                plan_data = {
                    'breakfast': 'Whole grain cereal with low-fat milk and fruit.',
                    'lunch': 'Whole wheat wrap with tuna and vegetables.',
                    'dinner': 'Chicken korma with small portion of basmati rice.',
                    'snack': 'A handful of trail mix.',
                    'tip': 'Try to stay active for 30 minutes today.'
                }
                
            DietPlan.objects.create(
                user=request.user,
                goal=goal.replace('_', ' ').title(),
                plan_data=plan_data
            )
            messages.success(request, 'Personalized Diet Plan Generated!')
            return redirect('diet_plans')
    else:
        form = DietPlanForm()
        
    return render(request, 'scheduler/diet_plans.html', {
        'form': form,
        'latest_plan': latest_plan
    })
