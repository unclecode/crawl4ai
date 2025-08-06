<!-- ---
!-- Timestamp: 2025-05-21 03:55:50
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/guidelines-programming-Python-Django-Rules.md
!-- --- -->


# Python Django Guidelines

## Project Structure

Django projects should follow this structure to maintain consistency and organization:

```
project-name/
├── apps/                  # All Django applications
│   ├── about_app/         # Example app for about/legal pages
│   │   ├── admin.py       # Admin configuration
│   │   ├── apps.py        # App configuration
│   │   ├── __init__.py
│   │   ├── migrations/    # Database migrations
│   │   ├── models.py      # Data models
│   │   ├── templates/     # App-specific templates
│   │   │   └── about_app/
│   │   │       ├── contact.html
│   │   │       ├── privacy_policy.html
│   │   │       └── terms_of_use.html
│   │   ├── tests.py       # Unit tests
│   │   ├── urls.py        # URL routing for this app
│   │   └── views.py       # View functions/classes
│   ├── auth_app/          # Authentication related functionality
│   └── api_app/           # API functionality
├── config/                # Project configuration
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py        # Base settings shared across environments
│   │   ├── development.py # Development-specific settings
│   │   └── production.py  # Production-specific settings
│   ├── urls.py            # Project-level URL routing
│   └── wsgi.py            # WSGI configuration
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── media/                 # User-uploaded files
├── templates/             # Project-wide templates
│   └── base.html          # Base template for inheritance
├── manage.py              # Django management script
├── requirements/
│   ├── base.txt           # Base requirements
│   ├── development.txt    # Development requirements
│   └── production.txt     # Production requirements
└── .env.example           # Example environment variables
```

## App Organization

1. Create focused apps with specific responsibilities
2. Keep apps small and modular (single responsibility principle)
3. Use descriptive names for apps that reflect their purpose

## Models

1. Define proper relationships (ForeignKey, ManyToMany, OneToOne)
2. Include docstrings for all models
3. Define `__str__` methods for all models
4. Use appropriate field types
5. Set reasonable defaults and constraints

```python
class Article(models.Model):
    """Represents a blog article with metadata."""
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
        
    def get_absolute_url(self):
        return reverse('article_detail', kwargs={'slug': self.slug})
```

## Views

1. Use class-based views when possible
2. Keep views focused on a single task
3. Move business logic to models or services
4. Implement proper permission handling

```python
class ArticleDetailView(DetailView):
    model = Article
    template_name = 'blog/article_detail.html'
    context_object_name = 'article'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_articles'] = self.object.get_related_articles()
        return context
```

## Templates

1. Use template inheritance to reduce duplication
2. Keep templates focused on presentation
3. Minimize template logic
4. Use template tags and filters for complex presentation logic

```html
{% extends "base.html" %}

{% block title %}{{ article.title }}{% endblock %}

{% block content %}
<article>
    <h1>{{ article.title }}</h1>
    <div class="meta">
        Published {{ article.created_at|date:"F j, Y" }} by {{ article.author.username }}
    </div>
    <div class="content">
        {{ article.content|safe }}
    </div>
</article>
{% endblock %}
```

## URLs

1. Use named URL patterns
2. Group related URLs under namespaces
3. Keep URL patterns clean and readable

```python
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='article_list'),
    path('<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('tag/<slug:tag_slug>/', views.TaggedArticleListView.as_view(), name='tag_detail'),
]
```

## Testing

1. Write tests for all models, views, and forms
2. Use Django's testing utilities
3. Aim for high test coverage
4. Test edge cases and failure scenarios

```python
from django.test import TestCase
from django.urls import reverse
from .models import Article

class ArticleModelTest(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title="Test Article",
            slug="test-article",
            content="Test content",
            author_id=1
        )
    
    def test_article_creation(self):
        self.assertEqual(self.article.title, "Test Article")
        self.assertEqual(self.article.slug, "test-article")
    
    def test_get_absolute_url(self):
        self.assertEqual(
            self.article.get_absolute_url(),
            reverse('blog:article_detail', kwargs={'slug': 'test-article'})
        )
```

## Settings

1. Split settings into base, development, and production
2. Use environment variables for sensitive information
3. Keep secrets out of version control
4. Configure proper logging

## Security

1. Validate all user input
2. Use Django's CSRF protection
3. Implement proper authentication and authorization
4. Keep dependencies updated
5. Follow the principle of least privilege

## Performance

1. Use Django's caching framework
2. Optimize database queries with select_related and prefetch_related
3. Use pagination for large datasets
4. Monitor query performance with Django Debug Toolbar

## Deployment

1. Use a proper WSGI/ASGI server (Gunicorn, uWSGI)
2. Configure a reverse proxy (Nginx, Apache)
3. Set DEBUG=False in production
4. Serve static files efficiently
5. Use a CDN where appropriate
6. Implement proper error handling and monitoring

<!-- EOF -->