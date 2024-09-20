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
        question_id = request.POST.get('question_id')  # Ensure you pass the question_id
        user_message = request.POST.get('message')
        user_choice = request.POST.get('user_choice')
        conversation = request.session.get('conversation', [])

        # Fetch the question and its choices from the database
        question = get_object_or_404(Question, pk=question_id)
        poll_choices = list(question.choice_set.values_list('choice_text', flat=True))  # Get choices as a list
        poll_question = question.question_text

        if user_message:
            # Append user message to conversation
            conversation.append({"role": "user", "content": user_message})

            # Prepare prompt for the OpenAI API
            system_data = [{"role": "system", "content": f"You are a chatbot specializing in Financial Information. The user will ask you questions about the poll they just responded to. You have their response as {user_choice}. Further, you have the poll's choices as {poll_choices}. Give as much information based on your database of the choices and the question {poll_question}. Take previous response and continue to build on what the user says. Give specific information and be as helpfull as possible. The user's choice: {user_choice}"}] + conversation

            try:
                client = OpenAI(api_key=settings.OPENAI_API_KEY) 
                response = client.chat.completions.create(model="gpt-4o-mini", messages=system_data)
                chatbot_reply = response.choices[0].message.content

                # Append bot response to conversation
                conversation.append({"role": "assistant", "content": chatbot_reply})

                # Save conversation back to session
                request.session['conversation'] = conversation

                return JsonResponse({'response': chatbot_reply, 'conversation': conversation})
            except Exception as e:
                return JsonResponse({'response': f'Error: {str(e)}'}, status=500)
    return JsonResponse({'response': 'No message received'}, status=400)




class ResultsView(generic.DetailView):
    model = Question
    template_name = "results.html"

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
            reverse("polls:results", args=(question.id,)) + f"?choice={selected_choice.choice_text}"
        )