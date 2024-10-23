from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    path('polls/', views.IndexView.as_view(), name="polls_index"),
    path('polls/<int:pk>/', views.DetailView.as_view(), name="polls_detail"),
    path('polls/<int:question_id>/results/',
         views.ResultsView.as_view(),
         name='results'),
    path('polls/<int:question_id>/vote/', views.vote, name='vote'),
    path('polls/chatbot/', views.chatbot, name='polls_chatbot'),

]
