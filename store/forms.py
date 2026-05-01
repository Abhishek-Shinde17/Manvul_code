from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'body']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.update({'class': 'form-control mv-input'})
        self.fields['rating'].widget = forms.RadioSelect(choices=[(i, f'{"★"*i}') for i in range(1,6)])
