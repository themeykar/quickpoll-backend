from django.db.models import Count
from rest_framework import serializers

from .models import Option, Poll, Vote


# ── Read-only serializers (responses) ──────────────────────────────────

class OptionResultSerializer(serializers.ModelSerializer):
    """Option with its aggregate vote count — used in public poll responses."""

    vote_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Option
        fields = ['id', 'text', 'vote_count']


class PollResultSerializer(serializers.ModelSerializer):
    """Public poll data — never exposes admin_token."""

    options = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ['id', 'question', 'is_closed', 'options']

    def get_options(self, poll):
        options = (
            poll.options
            .annotate(vote_count=Count('votes'))
            .order_by('order')
        )
        return OptionResultSerializer(options, many=True).data


class PollCreatedSerializer(PollResultSerializer):
    """Returned only on creation — includes the admin_token."""

    class Meta(PollResultSerializer.Meta):
        fields = PollResultSerializer.Meta.fields + ['admin_token']


# ── Write serializers (request validation) ─────────────────────────────

class PollCreateSerializer(serializers.Serializer):
    """Validates the POST body for creating a new poll."""

    question = serializers.CharField(max_length=300)
    options = serializers.ListField(
        child=serializers.CharField(max_length=200),
        min_length=2,
        max_length=6,
    )

    def validate_question(self, value):
        if not value.strip():
            raise serializers.ValidationError('Question must not be empty.')
        return value.strip()

    def validate_options(self, value):
        cleaned = []
        for idx, text in enumerate(value):
            text = text.strip()
            if not text:
                raise serializers.ValidationError(
                    f'Option {idx + 1} must not be empty.'
                )
            cleaned.append(text)
        return cleaned

    def create(self, validated_data):
        option_texts = validated_data.pop('options')
        poll = Poll.objects.create(question=validated_data['question'])
        Option.objects.bulk_create([
            Option(poll=poll, text=text, order=idx)
            for idx, text in enumerate(option_texts)
        ])
        return poll


class VoteCreateSerializer(serializers.Serializer):
    """Validates the POST body for casting a vote."""

    option_id = serializers.IntegerField()
    voter_id = serializers.CharField(max_length=64)
    voter_name = serializers.CharField(max_length=100)

    def validate_voter_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('Voter name must not be empty.')
        return value.strip()


class PollCloseSerializer(serializers.Serializer):
    """Validates the POST body for closing a poll."""

    admin_token = serializers.CharField()
