from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.core import mail
from taggit.models import Tag

from .models import Post, Comment
from .forms import EmailPostForm, CommentForm, SearchForm

class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            body='Test content for the post',
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )
        self.draft_post = Post.objects.create(
            title='Draft Post',
            slug='draft-post',
            author=self.user,
            body='Draft content',
            status=Post.Status.DRAFT,
            publish=timezone.now()
        )
    
    def test_post_creation(self):
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.status, Post.Status.PUBLISHED)
        self.assertEqual(self.post.author.username, 'testuser')
    
    def test_post_absolute_url(self):
        url = self.post.get_absolute_url()
        self.assertTrue(url.startswith('/'))
        self.assertIn(str(self.post.publish.year), url)
        self.assertIn(self.post.slug, url)
    
    def test_published_manager(self):
        published_count = Post.published.count()
        all_count = Post.objects.count()
        self.assertEqual(published_count, 1)
        self.assertEqual(all_count, 2)
    
    def test_string_representation(self):
        self.assertEqual(str(self.post), 'Test Post')

class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            body='Test content',
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )
        self.comment = Comment.objects.create(
            post=self.post,
            name='Test User',
            email='test@example.com',
            body='Test comment body',
            active=True
        )
    
    def test_comment_creation(self):
        self.assertEqual(self.comment.name, 'Test User')
        self.assertEqual(self.comment.post.title, 'Test Post')
        self.assertTrue(self.comment.active)

class ViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            body='Test content for the post',
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )
        self.tag = Tag.objects.create(name='django', slug='django')
        self.post.tags.add(self.tag)
        self.comment = Comment.objects.create(
            post=self.post,
            name='Test User',
            email='test@example.com',
            body='Test comment',
            active=True
        )
    
    def test_post_list_view(self):
        response = self.client.get(reverse('blogs:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
        self.assertTemplateUsed(response, 'blogs/post_list.html')
    
    def test_post_list_view_with_tag(self):
        response = self.client.get(
            reverse('blogs:post_list_by_tag', args=['django'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
    
    def test_post_list_view_pagination(self):
        for i in range(5):
            Post.objects.create(
                title=f'Test Post {i}',
                slug=f'test-post-{i}',
                author=self.user,
                body=f'Test content {i}',
                status=Post.Status.PUBLISHED,
                publish=timezone.now()
            )
        response = self.client.get(reverse('blogs:post_list') + '?page=2')
        self.assertEqual(response.status_code, 200)
    
    def test_post_detail_view(self):
        url = reverse('blogs:post_detail', args=[
            self.post.publish.year,
            self.post.publish.month,
            self.post.publish.day,
            self.post.slug
        ])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
        self.assertContains(response, 'Test comment')
        self.assertTemplateUsed(response, 'blogs/post_detail.html')
    
    def test_post_share_view_get(self):
        url = reverse('blogs:post_share', args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], EmailPostForm)
    
    def test_post_share_view_post(self):
        url = reverse('blogs:post_share', args=[self.post.id])
        data = {
            'name': 'Test User',
            'email': 'from@example.com',
            'to': 'to@example.com',
            'comments': 'Check out this post!'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        
        subject = mail.outbox[0].subject
        self.assertIn('Test User', subject)
        self.assertIn('from@example.com', subject)
        self.assertIn('recommends you read Test Post', subject)
    
    def test_post_comment_view(self):
        url = reverse('blogs:post_comment', args=[self.post.id])
        data = {
            'name': 'New Commenter',
            'email': 'new@example.com',
            'body': 'New test comment'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        
        new_comment = Comment.objects.filter(name='New Commenter').first()
        self.assertIsNotNone(new_comment)
        self.assertEqual(new_comment.body, 'New test comment')
    
    def test_post_search_view(self):
        url = reverse('blogs:post_search')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url, {'query': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

class FormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            body='Test content',
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )
    
    def test_email_post_form_valid(self):
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'to': 'recipient@example.com',
            'comments': 'Check this out!'
        }
        form = EmailPostForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_email_post_form_invalid(self):
        form_data = {
            'name': 'Test User',
            'email': 'invalid-email',
            'to': 'invalid-recipient',
            'comments': ''
        }
        form = EmailPostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('to', form.errors)
    
    def test_comment_form_valid(self):
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'body': 'Test comment body'
        }
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_comment_form_invalid(self):
        form_data = {
            'name': '',
            'email': 'invalid-email',
            'body': ''
        }
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('body', form.errors)
    
    def test_search_form_valid(self):
        form_data = {'query': 'django'}
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_search_form_invalid(self):
        form_data = {'query': ''}
        form = SearchForm(data=form_data)
        self.assertFalse(form.is_valid())

class TagTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.post1 = Post.objects.create(
            title='Django Post',
            slug='django-post',
            author=self.user,
            body='Post about Django',
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )
        self.post2 = Post.objects.create(
            title='Python Post',
            slug='python-post',
            author=self.user,
            body='Post about Python',
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )
        
        self.django_tag = Tag.objects.create(name='django', slug='django')
        self.python_tag = Tag.objects.create(name='python', slug='python')
        
        self.post1.tags.add(self.django_tag)
        self.post2.tags.add(self.python_tag)
    
    def test_tag_filtering(self):
        self.post1.tags.remove(self.python_tag) if self.python_tag in self.post1.tags.all() else None
        self.post2.tags.remove(self.django_tag) if self.django_tag in self.post2.tags.all() else None
        
        response = self.client.get(
            reverse('blogs:post_list_by_tag', args=['django'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Post')
        
        response = self.client.get(
            reverse('blogs:post_list_by_tag', args=['python'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Post')
    
    def test_similar_posts(self):
        post3 = Post.objects.create(
            title='Another Django Post',
            slug='another-django-post',
            author=self.user,
            body='Another post about Django',
            status=Post.Status.PUBLISHED,
            publish=timezone.now()
        )
        post3.tags.add(self.django_tag)
        
        url = reverse('blogs:post_detail', args=[
            self.post1.publish.year,
            self.post1.publish.month,
            self.post1.publish.day,
            self.post1.slug
        ])
        response = self.client.get(url)
        
        self.assertIn('similar_posts', response.context)
        similar_posts = response.context['similar_posts']
        self.assertEqual(len(similar_posts), 1)
        self.assertEqual(similar_posts[0].title, 'Another Django Post')