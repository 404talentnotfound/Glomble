from videos.models import Video, Comment
from .models import Creator

def update_funds():
    creators = Creator.objects.all()

    creator_scores = {}

    for i in creators:
        profile = i.profile
        follower_count = profile.followers.count()

        videos = Video.objects.filter(uploader=profile)
        total_video_views = sum([video.views.count() for video in videos])
        total_video_likes = sum([video.likes.count() for video in videos])
        total_video_dislikes = sum([video.dislikes.count() for video in videos])

        comments = Comment.objects.filter(commenter=profile)
        total_comments = Comment.objects.filter(post__uploader=profile).count()
        total_comment_likes = sum([comment.likes.count() for comment in comments])

        if total_video_likes + total_video_dislikes > 0:
            like_dislike_ratio = total_video_likes / (total_video_likes + total_video_dislikes)
        else:
            like_dislike_ratio = 1

        engagement_score = (
            follower_count * 0.3 +
            total_video_views * 0.15 +
            total_video_likes * 0.25 +
            total_comment_likes * 0.05 +
            like_dislike_ratio * 0.15 +
            total_comments * 0.1
        )

        creator_scores[profile] = engagement_score

    total_score = sum(creator_scores.values())
    
    if total_score == 0:
        return {profile: 0 for profile in creators}

    profile_percentages = {
        profile: (score / total_score) * 100
        for profile, score in creator_scores.items()
    }
    for i, j in enumerate(profile_percentages.keys()):
        creator = Creator.objects.get(profile=j)
        creator.percentage_share = list(profile_percentages.values())[i]
        creator.save()