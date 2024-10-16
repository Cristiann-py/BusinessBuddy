import datetime
from django.db import models
from django.utils import timezone
from django.contrib import admin


# Poll-related models
class Question(models.Model):
  question_text = models.CharField(max_length=200)
  pub_date = models.DateTimeField("date published")

  def __str__(self):
    return self.question_text

  @admin.display(boolean=True,
                 ordering="pub_date",
                 description="Published recently?")
  def was_published_recently(self):
    now = timezone.now()
    return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):
  question = models.ForeignKey(Question, on_delete=models.CASCADE)
  choice_text = models.CharField(max_length=200)
  votes = models.IntegerField(default=0)

  def __str__(self):
    return self.choice_text


class Quiz(models.Model):
  quiz_title = models.CharField(max_length=200)
  pub_date = models.DateTimeField('date published')

  def __str__(self):
    return self.quiz_title


class QuizQuestion(models.Model):
  quiz = models.ForeignKey(Quiz,
                           on_delete=models.CASCADE,
                           related_name='questions')
  question_text = models.CharField(max_length=200)

  def __str__(self):
    return self.question_text


class QuizChoice(models.Model):
  question = models.ForeignKey(QuizQuestion,
                               on_delete=models.CASCADE,
                               related_name='choices')
  choice_text = models.CharField(max_length=200)
  is_correct = models.BooleanField(default=False)

  def __str__(self):
    return self.choice_text
