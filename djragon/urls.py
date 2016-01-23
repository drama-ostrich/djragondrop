from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView
admin.autodiscover()

from views import ModelList, ModelListAjax, RelateChild, CreateChild, C, R, U, D

urlpatterns = patterns('',

    url(r'^(?P<model>[\w]+)/c/$',               C.as_view(), name='c'),
    url(r'^(?P<model>[\w]+)/r/(?P<pk>[\w]+)/$', R.as_view(), name='r'),
    url(r'^(?P<model>[\w]+)/u/(?P<pk>[\w]+)/$', U.as_view(), name='u'),
    url(r'^(?P<model>[\w]+)/d/(?P<pk>[\w]+)/$', D.as_view(), name='d'),

    url(r'^(?P<model>[\w]+)/relate/(?P<pk>[\w]+)/(?P<child_pk>[\w]+)/$', RelateChild.as_view(), name='relate_child'),
    url(r'^(?P<model>[\w]+)/create/(?P<pk>[\w]+)/$', CreateChild.as_view(), name='create_child'),

    url(r'^(?P<model>[\w]+)/ajax/$', ModelListAjax.as_view(), name='model_list_ajax'), # POST saves the sort order for the whole list
    url(r'^(?P<model>[\w]+)/$', ModelList.as_view(), name='model_list'),

)
