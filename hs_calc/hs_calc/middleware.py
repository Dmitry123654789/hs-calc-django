from django.shortcuts import render


class UniversalErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        ignored_codes = [403, 404]

        if response.status_code >= 400 and response.status_code not in ignored_codes:
            return render(
                request,
                "errors/error.html",
                {"status_code": response.status_code},
                status=response.status_code,
            )

        return response
