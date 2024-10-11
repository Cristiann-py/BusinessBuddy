from django.contrib import admin
from .models import Choice, Question, Quiz, QuizQuestion, QuizChoice


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {
            "fields": ["question_text"]
        }),
        ("Date information", {
            "fields": ["pub_date"],
            "classes": ["collapse"]
        }),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "pub_date", "was_published_recently"]
    list_filter = ["pub_date"]
    search_fields = ["question_text"]


admin.site.register(Question, QuestionAdmin)


# Admin interface for quizzes
class QuizChoiceInline(admin.TabularInline):
    model = QuizChoice
    extra = 3  # Number of blank choices that appear by default in the admin interface


class QuizQuestionAdmin(admin.ModelAdmin):
    inlines = [QuizChoiceInline]  # Add choices when editing a question


class QuizAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {
            "fields": ["quiz_title"]
        }),
        ("Date information", {
            "fields": ["pub_date"],
            "classes": ["collapse"]
        }),
    ]
    list_display = ['quiz_title', 'pub_date']
    list_filter = ['pub_date']
    search_fields = ['quiz_title']


# Register the models with the Django admin
admin.site.register(Quiz, QuizAdmin)
admin.site.register(QuizQuestion, QuizQuestionAdmin)
admin.site.register(QuizChoice)
