import os
import random
import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError, transaction
from datetime import datetime, timedelta

from posts.models import Category, Tag, Post, PostImage

User = get_user_model()


class Command(BaseCommand):
    help = 'Generates dummy data: 6 parent categories, 6 sub categories per parent, 10 posts per sub category'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories and posts before generating new ones',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Generating dummy data for categories and posts...'))

        # Clear existing data if requested
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing posts and categories...'))
            Post.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing data.'))

        # 1. Create or get a user
        if not User.objects.exists():
            self.stdout.write('Creating a dummy user...')
            User.objects.create_superuser(
                'dummyadmin', 'dummy@example.com', 'password123'
            )
        user = User.objects.first()

        # 2. Create 6 parent categories
        self.stdout.write('Creating 6 parent categories...')
        parent_categories_data = [
            {'name': 'Technology', 'description': 'Latest technology trends and innovations', 'image_seed': 100},
            {'name': 'Health & Wellness', 'description': 'Health tips, fitness, and wellness advice', 'image_seed': 200},
            {'name': 'Travel', 'description': 'Travel guides, destinations, and tips', 'image_seed': 300},
            {'name': 'Food & Cooking', 'description': 'Recipes, cooking tips, and food culture', 'image_seed': 400},
            {'name': 'Lifestyle', 'description': 'Lifestyle tips, fashion, and daily living', 'image_seed': 500},
            {'name': 'Education', 'description': 'Educational content, learning resources, and tutorials', 'image_seed': 600},
        ]

        parent_categories = []
        for i, data in enumerate(parent_categories_data):
            category, created = Category.objects.get_or_create(
                name=data['name'],
                defaults={
                    'slug': slugify(data['name']),
                    'description': data['description'],
                    'order': i + 1,
                    'is_active': True
                }
            )

            # Download and attach category image if it doesn't have one
            if not category.category_image:
                try:
                    image_url = f"https://picsum.photos/seed/{data['image_seed']}/1200/800"
                    response = requests.get(image_url, timeout=10, stream=True)
                    if response.status_code == 200:
                        image_filename = f"category_{slugify(data['name'])}.webp"
                        category.category_image.save(image_filename, ContentFile(response.content), save=True)
                        self.stdout.write(f'  ✓ Created parent category: {category.name} (with image)')
                    else:
                        self.stdout.write(f'  ✓ Created parent category: {category.name} (image download failed)')
                except Exception as e:
                    self.stdout.write(f'  ✓ Created parent category: {category.name} (image error: {str(e)[:50]})')
            else:
                if created:
                    self.stdout.write(f'  ✓ Created parent category: {category.name}')
                else:
                    self.stdout.write(f'  - Using existing parent category: {category.name}')

            parent_categories.append(category)

        # 3. Create 6 sub categories for each parent
        self.stdout.write('\nCreating 6 sub categories for each parent...')
        subcategories_templates = [
            ['Web Development', 'Mobile Apps', 'AI & Machine Learning', 'Cybersecurity', 'Cloud Computing', 'Data Science'],
            ['Fitness', 'Nutrition', 'Mental Health', 'Yoga & Meditation', 'Weight Loss', 'Healthy Recipes'],
            ['Destinations', 'Travel Tips', 'Adventure Travel', 'Budget Travel', 'Luxury Travel', 'Travel Photography'],
            ['Recipes', 'Baking', 'Vegetarian', 'International Cuisine', 'Cooking Tips', 'Food Reviews'],
            ['Fashion', 'Home Decor', 'Personal Finance', 'Productivity', 'Relationships', 'Self Improvement'],
            ['Programming', 'Mathematics', 'Science', 'Languages', 'Business Skills', 'Creative Arts'],
        ]

        all_subcategories = []
        for parent_idx, parent_cat in enumerate(parent_categories):
            self.stdout.write(f'\n  Creating subcategories for: {parent_cat.name}')
            subcategory_names = subcategories_templates[parent_idx]

            for sub_idx, sub_name in enumerate(subcategory_names):
                category, created = Category.objects.get_or_create(
                    name=sub_name,
                    parent=parent_cat,
                    defaults={
                        'slug': slugify(f"{parent_cat.name}-{sub_name}"),
                        'description': f'{sub_name} under {parent_cat.name}',
                        'order': sub_idx + 1,
                        'is_active': True
                    }
                )

                # Download and attach category image if it doesn't have one
                if not category.category_image:
                    try:
                        # Use unique seed based on parent and subcategory index
                        image_seed = (parent_idx + 1) * 1000 + (sub_idx + 1) * 100
                        image_url = f"https://picsum.photos/seed/{image_seed}/1200/800"
                        response = requests.get(image_url, timeout=10, stream=True)
                        if response.status_code == 200:
                            image_filename = f"category_{slugify(parent_cat.name)}_{slugify(sub_name)}.webp"
                            category.category_image.save(image_filename, ContentFile(response.content), save=True)
                            self.stdout.write(f'    ✓ Created subcategory: {sub_name} (with image)')
                        else:
                            self.stdout.write(f'    ✓ Created subcategory: {sub_name} (image download failed)')
                    except Exception as e:
                        if created:
                            self.stdout.write(f'    ✓ Created subcategory: {sub_name} (image error)')
                        else:
                            self.stdout.write(f'    - Using existing subcategory: {sub_name}')
                else:
                    if created:
                        self.stdout.write(f'    ✓ Created subcategory: {sub_name}')
                    else:
                        self.stdout.write(f'    - Using existing subcategory: {sub_name}')

                all_subcategories.append(category)

        # 4. Create tags
        self.stdout.write('\nCreating tags...')
        tag_names = [
            "Technology", "Health", "Travel", "Food", "Lifestyle", "Education",
            "Tips", "Guide", "Tutorial", "Review", "News", "Trending"
        ]
        all_tags = []
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name, defaults={'slug': slugify(name)})
            all_tags.append(tag)
            if created:
                self.stdout.write(f'  ✓ Created tag: {tag.name}')

        # 5. Create 10 posts for each sub category
        self.stdout.write('\nCreating 10 posts for each sub category...')
        total_posts = len(all_subcategories) * 10
        post_count = 0

        for subcategory in all_subcategories:
            self.stdout.write(f'\n  Creating posts for: {subcategory.name} (under {subcategory.parent.name})')

            for post_num in range(1, 11):
                post_count += 1
                title = f"{subcategory.name} - Article {post_num}"
                base_slug = slugify(f"{subcategory.name}-article-{post_num}")

                # Ensure unique slug
                slug = base_slug
                counter = 1
                while Post.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                # Check if post already exists (by slug)
                if Post.objects.filter(slug=slug).exists():
                    self.stdout.write(f'    - Skipping existing post: {title}')
                    continue

                # Generate content
                excerpt = f"Discover insights about {subcategory.name.lower()}. This article covers important aspects and provides valuable information."
                content = f"""
                <h2>Introduction</h2>
                <p>Welcome to this comprehensive guide on {subcategory.name.lower()}. In this article, we'll explore various aspects and provide you with practical insights.</p>

                <h2>Key Points</h2>
                <ul>
                    <li>Important aspect one related to {subcategory.name.lower()}</li>
                    <li>Important aspect two that you should know</li>
                    <li>Practical tips and recommendations</li>
                    <li>Common mistakes to avoid</li>
                </ul>

                <h2>Detailed Information</h2>
                <p>This section provides in-depth information about {subcategory.name.lower()}. Whether you're a beginner or experienced, you'll find valuable content here.</p>

                <h2>Conclusion</h2>
                <p>We hope this article has been helpful. Stay tuned for more content about {subcategory.name.lower()} and related topics.</p>
                """

                # Random published date within last 6 months
                days_ago = random.randint(0, 180)
                published_date = timezone.now() - timedelta(days=days_ago)

                # Create post without saving first to avoid ID conflicts
                try:
                    with transaction.atomic():
                        post = Post(
                            title=title,
                            slug=slug,
                            excerpt=excerpt,
                            content=content,
                            category=subcategory,
                            author=user,
                            is_published=random.choice([True, True, True, False]),  # 75% published
                            published_date=published_date if random.choice([True, True, False]) else None,
                            order=post_num,
                            meta_title=f"{title} - {subcategory.parent.name}",
                            meta_description=excerpt
                        )
                        # Save without processing image first
                        post.save()

                        # Add random tags (2-4 tags)
                        num_tags = random.randint(2, min(4, len(all_tags)))
                        post.tags.set(random.sample(all_tags, num_tags))

                        # Download and attach featured image
                        try:
                            # Use different image seeds for variety
                            seed = random.randint(1, 10000)
                            image_url = f"https://picsum.photos/seed/{seed}/1200/800"
                            response = requests.get(image_url, timeout=10, stream=True)
                            if response.status_code == 200:
                                image_filename = f"{slugify(subcategory.name)}_post_{post_num}.webp"
                                # Save image without triggering another full save
                                post.featured_image.save(image_filename, ContentFile(response.content), save=False)
                                # The Post model's save() will handle image processing
                                post.save()
                                self.stdout.write(f'    ✓ Created post {post_num}/10: {title} (with image)')
                            else:
                                self.stdout.write(self.style.WARNING(f'    ⚠ Post {post_num}/10: {title} (image download failed)'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'    ✗ Error downloading image for {title}: {e}'))

                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(f'    ✗ IntegrityError creating post {title}: {e}'))
                    # Try to continue with next post
                    continue
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    ✗ Error creating post {title}: {e}'))
                    continue

                # Create 2-4 gallery images for some posts (30% chance)
                if random.random() < 0.3:
                    num_gallery_images = random.randint(2, 4)
                    for gallery_num in range(num_gallery_images):
                        try:
                            gallery_seed = random.randint(10001, 20000)
                            gallery_image_url = f"https://picsum.photos/seed/{gallery_seed}/800/600"
                            response = requests.get(gallery_image_url, timeout=10, stream=True)
                            if response.status_code == 200:
                                gallery_filename = f"{slugify(subcategory.name)}_post_{post_num}_gallery_{gallery_num}.webp"
                                post_image = PostImage(
                                    post=post,
                                    caption=f"Gallery image {gallery_num + 1} for {title}"
                                )
                                post_image.image_file.save(gallery_filename, ContentFile(response.content), save=True)
                        except Exception as e:
                            pass  # Silently skip gallery image errors

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\n✓ Dummy data generation complete!'))
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  - Parent Categories: {len(parent_categories)}')
        self.stdout.write(f'  - Sub Categories: {len(all_subcategories)}')
        self.stdout.write(f'  - Posts Created: {Post.objects.count()}')
        self.stdout.write(f'  - Tags: {len(all_tags)}')
        self.stdout.write('='*60)


