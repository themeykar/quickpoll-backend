from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import IntegrityError
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Poll, Vote
from .serializers import (
    PollCloseSerializer,
    PollCreatedSerializer,
    PollCreateSerializer,
    PollResultSerializer,
    VoteCreateSerializer,
)


class PollListCreateView(APIView):
    """
    POST /api/polls/ — create a new poll.
    """

    def post(self, request):
        serializer = PollCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        poll = serializer.save()
        return Response(
            PollCreatedSerializer(poll).data,
            status=status.HTTP_201_CREATED,
        )


class PollDetailView(APIView):
    """
    GET /api/polls/{id}/ — fetch a poll's public data.
    """

    def get(self, request, pk):
        poll = get_object_or_404(Poll, pk=pk)
        return Response(PollResultSerializer(poll).data)


class PollVoteView(APIView):
    """
    POST /api/polls/{id}/vote/ — cast a vote on a poll.
    """

    def post(self, request, pk):
        poll = get_object_or_404(Poll, pk=pk)

        # Reject if poll is already closed
        if poll.is_closed:
            return Response(
                {'detail': 'This poll is closed. Voting is no longer allowed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Ensure the option belongs to *this* poll
        try:
            option = poll.options.get(pk=data['option_id'])
        except poll.options.model.DoesNotExist:
            return Response(
                {'detail': 'The selected option does not belong to this poll.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the vote, catching the unique_together violation
        try:
            Vote.objects.create(
                poll=poll,
                option=option,
                voter_id=data['voter_id'],
                voter_name=data['voter_name'],
            )
        except IntegrityError:
            return Response(
                {'detail': 'This voter has already voted on this poll.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Return updated poll data with fresh vote counts
        poll_data = PollResultSerializer(poll).data

        # Broadcast to WebSocket subscribers
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'poll_{poll.pk}',
            {'type': 'poll_update', 'data': poll_data},
        )

        return Response(poll_data, status=status.HTTP_201_CREATED)


class PollCloseView(APIView):
    """
    POST /api/polls/{id}/close/ — close voting on a poll.
    """

    def post(self, request, pk):
        serializer = PollCloseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin_token = serializer.validated_data['admin_token']

        # Look up by both pk AND admin_token so we never reveal whether
        # a poll exists when the token is wrong.
        try:
            poll = Poll.objects.get(pk=pk, admin_token=admin_token)
        except Poll.DoesNotExist:
            return Response(
                {'detail': 'Forbidden.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        poll.is_closed = True
        poll.save(update_fields=['is_closed'])

        poll_data = PollResultSerializer(poll).data

        # Broadcast to WebSocket subscribers
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'poll_{poll.pk}',
            {'type': 'poll_update', 'data': poll_data},
        )

        return Response(poll_data)
