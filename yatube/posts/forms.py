from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        # укажем модель, с которой связана создаваемая форма
        model = Post
        # укажем, какие поля должны быть видны в форме и в каком порядке
        fields = ('group', 'text', 'image')
        labels = {
            # Переназначено в /models.py
            # 'text': 'Текст поста',
            # 'group': 'Группа',
        }
        help_texts = {
            # 'text': 'Текст нового поста',
            # 'group': 'Группа, к которой будет относиться пост',
        }
