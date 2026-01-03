from django.http import HttpResponse

def welcome_view(request):
    return HttpResponse("<h1>Welcome to the Panchang API!</h1><p>Access API endpoints at /api/</p>")

























