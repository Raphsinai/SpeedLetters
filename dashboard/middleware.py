from django.shortcuts import render

def IsAuthMiddleware(get_response):

    def middleware(request):
        if (request.path.startswith('/dashboard') or 'account' in request.path) and not request.user.is_authenticated:
            context = {
                "title": "Not logged in",
                "message": "- You are not logged in."
            }
            return render(request, '403.html', context)

        response = get_response(request)

        if response.status_code == 403:
            res = render(request, '403.html', {'message': response.content.decode()})
            res.status_code = 403
            return res
        if response.status_code == 404:
            res = render(request, '404.html', {'message': response.content.decode()})
            res.status_code = 404
            return res

        return response

    return middleware