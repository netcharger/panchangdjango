import os
import random
import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.utils import timezone # Import timezone
from datetime import datetime # Import datetime

from posts.models import Category, Tag, Post, PostImage

User = get_user_model()

class Command(BaseCommand):
    help = 'Generates dummy data for the posts app (Categories, Tags, Posts).'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Generating dummy data for posts...'))

        # 1. Create Dummy Users (if none exist)
        if not User.objects.exists():
            self.stdout.write('Creating a dummy superuser...')
            User.objects.create_superuser(
                'dummyadmin', 'dummy@example.com', 'password123'
            )
            User.objects.create_user(
                'dummynormal', 'normal@example.com', 'password123'
            )
        users = list(User.objects.all())

        # 2. Create Dummy Categories
        self.stdout.write('Creating dummy categories...')
        categories_data = [
            {'name': 'Festivals', 'description': 'Articles about various festivals.'},
            {'name': 'Traditions', 'description': 'Insights into cultural traditions.'},
            {'name': 'Spirituality', 'description': 'Content on spiritual practices.'},
            {'name': 'Lifestyle', 'description': 'Modern lifestyle articles.'},
            {'name': 'Food', 'description': 'Recipes and culinary traditions.'},
        ]
        parent_categories = []
        for i, data in enumerate(categories_data):
            category, created = Category.objects.get_or_create(
                name=data['name'],
                defaults={'slug': slugify(data['name']), 'description': data['description'], 'order': i + 1}
            )
            parent_categories.append(category)
            if created:
                self.stdout.write(f'  Created category: {category.name}')
        
        # Create subcategories
        subcategories_data = [
            {'name': 'Diwali', 'parent': 'Festivals'},
            {'name': 'Holi', 'parent': 'Festivals'},
            {'name': 'Wedding Rituals', 'parent': 'Traditions'},
            {'name': 'Meditation', 'parent': 'Spirituality'},
            {'name': 'Healthy Living', 'parent': 'Lifestyle'},
            {'name': 'Indian Cuisine', 'parent': 'Food'},
        ]
        for i, data in enumerate(subcategories_data):
            parent_cat = next((pc for pc in parent_categories if pc.name == data['parent']), None)
            if parent_cat:
                category, created = Category.objects.get_or_create(
                    name=data['name'],
                    defaults={'slug': slugify(data['name']), 'parent': parent_cat, 'order': i + 1}
                )
                if created:
                    self.stdout.write(f'  Created subcategory: {category.name} under {parent_cat.name}')

        all_categories = list(Category.objects.all())

        # 3. Create Dummy Tags
        self.stdout.write('Creating dummy tags...')
        tag_names = ["Hindu Festival", "Lights", "Traditions", "Yoga", "Wellness", "Recipes", "Culture", "Celebration"]
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name, defaults={'slug': slugify(name)})
            if created:
                self.stdout.write(f'  Created tag: {tag.name}')
        all_tags = list(Tag.objects.all())

        # 4. Create Dummy Posts
        self.stdout.write('Creating dummy posts...')
        for i in range(1, 21):  # Create 20 posts
            title = f"Dummy Post Title {i}"
            slug = slugify(title)
            
            # Check if post already exists to make it idempotent
            if Post.objects.filter(slug=slug).exists():
                self.stdout.write(f'  Skipping existing post: {title}')
                continue

            post = Post(
                title=title,
                slug=slug,
                excerpt=f"This is a short excerpt for dummy post {i}. It gives a brief overview of the content.",
                content=f"<p>This is the rich text content for dummy post {i}.</p><p>It can contain <strong>bold text</strong>, <em>italic text</em>, and even <a href=\"#\">links</a>.</p><p>Images will be handled separately.</p>",
                category=random.choice(all_categories),
                author=random.choice(users),
                is_published=random.choice([True, False]),
                published_date=timezone.make_aware(datetime.strptime(f'202{random.randint(3, 5)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}T{random.randint(9, 17):02d}:{random.randint(0, 59):02d}:00', '%Y-%m-%dT%H:%M:%S')),
                order=i
            )
            post.save()

            # Add random tags
            num_tags = random.randint(1, min(4, len(all_tags)))
            post.tags.set(random.sample(all_tags, num_tags))

            # Download and attach a featured image
            try:
                image_url = f"https://picsum.photos/seed/{random.randint(1, 1000)}/1200/800"
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    image_filename = f"featured_post_{i}.webp"
                    post.featured_image.save(image_filename, ContentFile(response.content), save=True)
                    self.stdout.write(f'  Attached featured image to post: {title}')
                else:
                    self.stdout.write(self.style.WARNING(f'  Failed to download image for {title}: Status {response.status_code}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error downloading image for {title}: {e}'))
            
            # Create some PostImage instances for the gallery
            num_gallery_images = random.randint(0, 3)
            for j in range(num_gallery_images):
                try:
                    gallery_image_url = f"https://picsum.photos/seed/{random.randint(1001, 2000)}/800/600"
                    response = requests.get(gallery_image_url, stream=True)
                    if response.status_code == 200:
                        gallery_image_filename = f"post_{i}_gallery_{j}.webp"
                        post_image = PostImage(post=post, caption=f"Gallery image {j+1} for {title}")
                        post_image.image_file.save(gallery_image_filename, ContentFile(response.content), save=True)
                        self.stdout.write(f'    Attached gallery image {j+1} to post: {title}')
                    else:
                        self.stdout.write(self.style.WARNING(f'    Failed to download gallery image for {title}: Status {response.status_code}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Error downloading gallery image for {title}: {e}'))

            self.stdout.write(f'  Created post: {title}')

        self.stdout.write(self.style.SUCCESS('Dummy data generation complete!'))
