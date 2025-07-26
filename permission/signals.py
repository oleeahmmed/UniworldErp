from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

# @receiver(post_save, sender=User)
# def deactivate_new_user(sender, instance, created, **kwargs):
#     # যদি নতুন ইউজার তৈরি হয়, তাহলে `is_active` ফিল্ডটি False সেট করুন
#     if created and instance.is_active:  # Check if user is created and active by default
#         instance.is_active = True
#         instance.save()
