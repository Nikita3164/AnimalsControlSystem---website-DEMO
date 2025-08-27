import random
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.db import connections
from .apps import get_rabbits 
from .models import Rabbit
from django.views.decorators.csrf import csrf_exempt
import json
#from .Bot.main import sending


def index(request):
    return render(request, 'main/main.html')


def setup(request):
    return render(request, 'main/setup.html')


def monitoring(request):
    if request.user.is_authenticated:
        rabbits = Rabbit.objects.all()
        #print(rabbits)
        return render(request, 'main/monitoring.html', { 'rabbits': rabbits })
    else:
        return HttpResponseRedirect('authorization/login/')
    

@csrf_exempt
def sensor_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Received data:", data)
            # Обработка данных (например, сохранение в БД)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})


def get_rabbits_data(request):
    rabbits = Rabbit.objects.all()
    data = [{'rabbit_id': rabbit.rabbit_id,
             'rabbit_name': rabbit.rabbit_name,
             'rabbit_temp': rabbit.rabbit_temp,
             'rabbit_temp_med': rabbit.rabbit_temp_med,
             'rabbit_pulse': rabbit.rabbit_pulse,
             'rabbit_pulse_med': rabbit.rabbit_pulse_med,
             'risk': rabbit.risk} for rabbit in rabbits]
    return JsonResponse(data, safe=False)


def post_test_data(request):
    rbt_connection = connections['rabbits']
    updates = []
    
    # Fetch all rabbit data
    with rbt_connection.cursor() as cursor:
        cursor.execute("SELECT rabbit_temp_med, rabbit_pulse_med, rabbit_id, rabbit_name FROM rabbits_group_1")
        rows = cursor.fetchall()
        
        # Process each rabbit's data
        for i, row in enumerate(rows):
            rabbit_temp_med, rabbit_pulse_med, rabbit_id, rabbit_name = row
            get_temp = random.uniform(35, 44)
            med_temp = (rabbit_temp_med + get_temp) / 2
            get_pulse = random.uniform(80, 140)
            med_pulse = (rabbit_pulse_med + get_pulse) / 2
            
            # Determine risk based on conditions
            if abs(med_temp - get_temp) >= 3 and abs(med_pulse - get_pulse) >= 5:
                if (med_temp - get_temp) > 0 and (med_pulse - get_pulse) > 0:
                    risk = 'Пониженные температура и пульс'
                elif (med_temp - get_temp) < 0 and (med_pulse - get_pulse) < 0:
                    risk = 'Повышенные температура и пульс'
                elif (med_temp - get_temp) > 0 and (med_pulse - get_pulse) < 0:
                    risk = 'Пониженная температура и повышенный пульс'
                else:  # (med_temp - get_temp) < 0 and (med_pulse - get_pulse) > 0
                    risk = 'Повышенная температура и пониженный пульс'
            elif abs(med_temp - get_temp) >= 3:
                risk = 'Повышенная температура' if (med_temp - get_temp) < 0 else 'Пониженная температура'
            elif abs(med_pulse - get_pulse) >= 5:
                risk = 'Повышенный пульс' if (med_pulse - get_pulse) < 0 else 'Пониженный пульс'
            else:
                risk = 'Нет'
            
            # Collect update data
            updates.append((get_temp, med_temp, get_pulse, med_pulse, risk, rabbit_id))
        
        # Perform bulk update with a single query
        if updates:
            query = """
                UPDATE rabbits_group_1
                SET rabbit_temp = %s,
                    rabbit_temp_med = %s,
                    rabbit_pulse = %s,
                    rabbit_pulse_med = %s,
                    risk = %s
                WHERE rabbit_id = %s
            """
            cursor.executemany(query, updates)


def profile(request):
    return render(request, 'main/profile.html')
        