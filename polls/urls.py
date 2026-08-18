from django.urls import path

from . import views

app_name = 'polls'

urlpatterns = [
    path('', views.PollListCreateView.as_view(), name='poll-create'),
    path('<int:pk>/', views.PollDetailView.as_view(), name='poll-detail'),
    path('<int:pk>/vote/', views.PollVoteView.as_view(), name='poll-vote'),
    path('<int:pk>/close/', views.PollCloseView.as_view(), name='poll-close'),
]
