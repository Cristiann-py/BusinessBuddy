from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.http import JsonResponse

from openai import OpenAI
from django.conf import settings
from .models import Choice, Question

from .models import Quiz, QuizQuestion
from django.views import View


# Polls Index View
class IndexView(generic.ListView):
    template_name = "index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(
            pub_date__lte=timezone.now()).order_by("-pub_date")[:5]


def index(request):
    latest_question_list = Question.objects.filter(
        pub_date__lte=timezone.now()).order_by('-pub_date')[:5]
    latest_quiz_list = Quiz.objects.filter(
        pub_date__lte=timezone.now()).order_by('-pub_date')[:5]

    context = {
        'latest_question_list': latest_question_list,
        'latest_quiz_list': latest_quiz_list,
    }
    return render(request, 'index.html', context)


class DetailView(generic.DetailView):
    model = Question
    template_name = "detail.html"

    def get_queryset(self):
        """
    Excludes any questions that aren't published yet.
    """
        return Question.objects.filter(pub_date__lte=timezone.now())


def chatbot(request):
    if request.method == 'POST':
        question_id = request.POST.get(
            'question_id')  # Ensure you pass the question_id
        user_message = request.POST.get('message')
        user_choice = request.POST.get('user_choice')
        conversation = request.session.get('conversation', [])

        # Fetch the question and its choices from the database
        question = get_object_or_404(Question, pk=question_id)
        poll_choices = list(
            question.choice_set.values_list(
                'choice_text', flat=True))  # Get choices as a list
        poll_question = question.question_text

        if user_message:
            # Append user message to conversation
            conversation.append({"role": "user", "content": user_message})

            # Prepare prompt for the OpenAI API
            system_data = [{
                "role":
                "system",
                "content":
                (f"You are a chatbot specializing in Financial Information. "
                 f"The user will ask you questions about the poll they just responded to. "
                 f"The poll question is '{poll_question}' and the possible choices are {poll_choices}. "
                 f"The user has selected '{user_choice}'. "
                 f"Use the user's response, the choices, and the question to continue the conversation and provide relevant information."
                 f"You are a high school student talking to other high school students. Talk in a more human tone but still present information clearly."
                 f"Have a short and to the point answer with statistical and mathematical points."
                 f"Don't use exclamation marks in order to keep the conversation on topic and have shorter responses."
                 )
            }] + conversation

            try:
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.chat.completions.create(model="gpt-4o-mini",
                                                          messages=system_data)
                chatbot_reply = response.choices[0].message.content

                # Append bot response to conversation
                conversation.append({
                    "role": "assistant",
                    "content": chatbot_reply
                })

                # Save conversation back to session
                request.session['conversation'] = conversation

                return JsonResponse({
                    'response': chatbot_reply,
                    'conversation': conversation
                })
            except Exception as e:
                return JsonResponse({'response': f'Error: {str(e)}'},
                                    status=500)
    return JsonResponse({'response': 'No message received'}, status=400)


class ResultsView(generic.DetailView):
    model = Question
    template_name = "results.html"

    def get_object(self):
        # Here, we're overriding the get_object to fetch the object using question_id
        question_id = self.kwargs.get('question_id')
        return get_object_or_404(Question, pk=question_id)

    def get(self, request, *args, **kwargs):
        # Reset the conversation on page load
        if 'conversation' in request.session:
            del request.session['conversation']
        return super().get(request, *args, **kwargs)


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(
            request,
            "detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        return HttpResponseRedirect(
            reverse("polls:results", args=(question.id, )) +
            f"?choice={selected_choice.choice_text}")


# Quiz Views


# Quiz Views
class QuizIndexView(generic.ListView):
    template_name = 'quiz_index.html'
    context_object_name = 'latest_quiz_list'

    def get_queryset(self):
        return Quiz.objects.filter(
            pub_date__lte=timezone.now()).order_by('-pub_date')[:5]


class QuizDetailView(View):

    def get(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        questions = quiz.questions.prefetch_related('choices')
        return render(request, 'quiz_detail.html', {
            'quiz': quiz,
            'questions': questions
        })

    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        questions = quiz.questions.prefetch_related('choices')
        user_answers = {}
        correct_answers = 0

        for question in questions:
            user_choice_id = request.POST.get(f'question_{question.id}')
            if user_choice_id:
                user_choice = get_object_or_404(QuizChoice, id=user_choice_id)
                user_answers[question.id] = user_choice
                if user_choice.is_correct:
                    correct_answers += 1

        total_questions = questions.count()
        score = (correct_answers / total_questions) * 100

        return render(
            request, 'quiz_results.html', {
                'quiz': quiz,
                'questions': questions,
                'user_answers': user_answers,
                'score': score,
                'correct_answers': correct_answers,
                'total_questions': total_questions
            })


def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'results.html', {'question': question})


def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/detail.html', {'question': question})
