"""
Management command to update hot scores for all posts
Run this periodically (every hour) with a cron job or task scheduler
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from basic.models import Post


class Command(BaseCommand):
    help = 'Update hot scores for all posts (Reddit-style ranking)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Only update posts from last N days (default: 30)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timezone.timedelta(days=days)

        # Update posts from last N days
        posts = Post.objects.filter(created_at__gte=cutoff_date)
        total = posts.count()

        self.stdout.write(f"Updating hot scores for {total} posts from last {days} days...")

        updated = 0
        for post in posts.iterator():
            post.update_hot_score()
            updated += 1

            if updated % 100 == 0:
                self.stdout.write(f"  Progress: {updated}/{total}")

        self.stdout.write(
            self.style.SUCCESS(f"✓ Successfully updated {updated} post hot scores")
        )
