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

    # Quizzes URLs
    path('quizzes/', views.QuizIndexView.as_view(), name="quizzes_index"),
    path('quizzes/<int:pk>/',
         views.QuizDetailView.as_view(),
         name="quizzes_detail"),
]
