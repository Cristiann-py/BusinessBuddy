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
        user_message = request.POST.get('message')
        user_choice = request.POST.get('user_choice')
        conversation = request.session.get('conversation', [])

        if user_message:
            # Append user message to conversation
            conversation.append({"role": "user", "content": user_message})

            # Prepare prompt for the OpenAI API
            system_data = [ {"role": "system", "content": f"You are an argumentative chatbot who is very sassy and talks back to the user on whatever their opinion is. Clown on the users choice and be mean argue and never back down. Be firm in your abilities to shut down whatever the users opinion is. Make your responses short and simple. Take previous reponses and make a cohesive argument based off of what the user says back and what you have said previously. The user's choice: {user_choice}"} ] + conversation

            try:
                client = OpenAI(api_key=settings.OPENAI_API_KEY) 
                response = client.chat.completions.create(model="gpt-3.5-turbo", messages=system_data)
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