"""hashtagsv2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from hashtagsv2.hashtags.views import (Index,
                                      csv_download,
                                      json_download,
                                      Docs,
                                      top_project_statistics_data,
                                      top_user_statistics_data,
                                      time_statistics_data,
                                      graph)

urlpatterns = [
	path('', Index.as_view(), name='index'),
	path('csv/', csv_download, name='csv_download'),
	path('json/', json_download, name='json_download'),
    path('docs/', Docs.as_view(), name='docs'),
    path('admin/', admin.site.urls, name='admin'),
    path('graph/', graph, name='graph'),
    path('api/top_project_stats/', top_project_statistics_data, name='top_project_statistics_data'),
    path('api/top_user_stats/', top_user_statistics_data, name='top_user_statistics_data'),
    path('api/time_stats/', time_statistics_data, name='time_statistics_data')
]
