def imageToURL(image, request):
    return f"{request.scheme}://{request.get_host()}{image.url}"