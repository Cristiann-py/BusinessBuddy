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

def index(request):
    # Fetch the latest polls and quizzes
    latest_question_list = Question.objects.filter(
        pub_date__lte=now()).order_by('-pub_date')[:5]
    

    context = {
        'latest_question_list': latest_question_list,
    }
    return render(request, 'index.html', context)

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
            'question_id')  
        user_message = request.POST.get('message')
        user_choice = request.POST.get('user_choice')
        conversation = request.session.get('conversation', [])

        question = get_object_or_404(Question, pk=question_id)
        poll_choices = list(
            question.choice_set.values_list(
                'choice_text', flat=True))  
        poll_question = question.question_text

        if user_message:
            conversation.append({"role": "user", "content": user_message})

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

                conversation.append({
                    "role": "assistant",
                    "content": chatbot_reply
                })

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





def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'results.html', {'question': question})


def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/detail.html', {'question': question})
