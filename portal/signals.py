from django.contrib.auth.models import User
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        role = Profile.ROLE_ADMIN if instance.is_superuser else Profile.ROLE_STUDENT
        Profile.objects.create(
            user=instance,
            role=role,
            full_name=instance.get_full_name() or instance.username,
        )
        return

    profile, _ = Profile.objects.get_or_create(
        user=instance,
        defaults={
            'role': Profile.ROLE_ADMIN if instance.is_superuser else Profile.ROLE_STUDENT,
            'full_name': instance.get_full_name() or instance.username,
        },
    )
    if instance.is_superuser and profile.role != Profile.ROLE_ADMIN:
        profile.role = Profile.ROLE_ADMIN
        profile.save(update_fields=['role'])


@receiver(post_migrate)
def ensure_seed_admin(sender, **kwargs):
    if sender.name != 'portal':
        return

    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@exam.org',
            'is_staff': True,
            'is_superuser': True,
        },
    )
    if created:
        user.set_password('Admin@9999')
        user.save()
    elif not user.is_superuser:
        user.is_staff = True
        user.is_superuser = True
        user.set_password('Admin@9999')
        user.save()
