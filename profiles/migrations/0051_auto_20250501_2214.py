from django.db import migrations

def migrate_jsonfield_to_model(apps, schema_editor):
    Profile = apps.get_model('profiles', 'Profile')
    ProfileRating = apps.get_model('profiles', 'ProfileRating')
    User = apps.get_model('auth', 'User')

    for profile in Profile.objects.all():
        if not profile.ratings:
            continue
        for user_id, rating in profile.ratings.items():
            try:
                user = User.objects.get(id=int(user_id))
                ProfileRating.objects.update_or_create(
                    rater=user,
                    rated_profile=profile,
                    defaults={'rating': rating}
                )
            except User.DoesNotExist:
                continue
        ratings = ProfileRating.objects.filter(rated_profile=profile)
        if ratings.exists():
            average = sum(r.rating for r in ratings) / ratings.count()
            profile.rating = average
        else:
            profile.rating = 5
            profile.save()

class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0050_alter_profile_recommendations_left_and_more'),  # adjust if needed
    ]

    operations = [
        migrations.RunPython(migrate_jsonfield_to_model),
    ]
