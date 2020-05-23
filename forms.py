from django import forms
import datetime


class MovieSearchForm(forms.Form):
    LANGUAGES = [
    ('cn', 'Chinese'),
    ('da', 'Danish'),
    ('nl', 'Dutch'),
    ('en', 'English'),
    ('fi', 'Finish'),
    ('fr', 'French'),
    ('de', 'German'),
    ('it', 'Italian'),
    ('ja', 'Japanese'),
    ('ko', 'Korean'),
    ('no', 'Norwegian'),
    ('pt', 'Portuegese'),
    ('es', 'Spanish'),
    ('sv', 'Swedish'),
]
    lang = forms.ChoiceField(label='Language', choices=LANGUAGES, widget=forms.RadioSelect)

    DOC_FILTERS = [
    ('1', 'Include Documentaries'),
    ('2', 'Exclude Documentaries'),
    ('3', 'Exlusively Documentaries'),
]
    doc = forms.ChoiceField(label='Documentary Filters', choices=DOC_FILTERS, widget=forms.RadioSelect)

    STANDUP_FILTERS = [
    ('1', 'Include Stand-Up'),
    ('2', 'Exclude Stand-Up'),
    ('3', 'Exlusively Stand-Up'),
]
    sup = forms.ChoiceField(label='Stand-Up Filters', choices=STANDUP_FILTERS, widget=forms.RadioSelect)

    rating = forms.IntegerField(label='Rating', min_value=65, max_value=100)
    now = datetime.datetime.now()
    start = forms.IntegerField(label='Start Year', min_value=1900, max_value=now.year)
    end = forms.IntegerField(label='End Year', min_value=1900, max_value=now.year)
