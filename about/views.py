from django.shortcuts import render


def about(request):
    """ a view to return the about page """
    
    return render(request, 'about/about.html')