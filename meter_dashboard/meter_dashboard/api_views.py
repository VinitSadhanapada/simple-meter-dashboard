from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def api_root(request):
    return JsonResponse({
        "message": "API root. Available endpoints: /api/set_failure_mode/ ...",
        "method": request.method,
        "path": request.path,
        "body": request.body.decode('utf-8') if request.body else None
    })
