from rest_framework import viewsets, permissions, response, exceptions, mixins, parsers

from space_and_beauty.pagination import RestFrameworkPaginationMixin
from . import serializers, models


class UserProfileViewSet(viewsets.GenericViewSet):
    """
    Endpoint for retrieving and updating a user profile.
    Supports GET (list) and PATCH (partial update) with image upload.
    """
    permission_classes = (
        permissions.IsAuthenticated,
    )
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)

    serializer_class = serializers.UserProfileSerializers

    def get_object(self):
        if not hasattr(self.request.user, "userprofile"):
            raise exceptions.NotFound({"detail": "User profile not found"})
        return self.request.user.userprofile

    def list(self, request):
        user = request.user

        if not hasattr(user, "userprofile"):
            raise exceptions.NotFound({"detail": "User profile not found"})

        serializer = self.get_serializer(user.userprofile).data

        return response.Response(serializer)

    def create(self, request):
        """Legacy endpoint kept for compatibility – forwards to PATCH behavior."""
        return self.partial_update(request)

    def partial_update(self, request, *args, **kwargs):
        """Handle profile updates, including image uploads via multipart/form-data."""
        if not request.user.is_authenticated:
            raise exceptions.NotAuthenticated({"detail": "Authentication credentials were not provided."})
        user = request.user
        if not hasattr(user, "userprofile"):
            raise exceptions.NotFound({"detail": "User profile not found"})
        serializer = self.get_serializer(user.userprofile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data)


class UserAddressViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin, mixins.CreateModelMixin):
    """
    use this endpoint to do following operations
    1. Create a Address
    2. Update a user Address
    3. List all user Address
    """

    permission_classes = (
        permissions.IsAuthenticated,
    )

    model = models.Address
    serializer_class = serializers.AddressSerializer

    def get_queryset(self):
        if not hasattr(self.request.user, "userprofile"):
            raise exceptions.NotFound()
        return self.model.objects.filter(user=self.request.user.userprofile)


class UserPointsHistoryViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """
    use this endpoint to do list user's point history details
    """
    permission_classes = (
        permissions.IsAuthenticated,
    )
    pagination_class = RestFrameworkPaginationMixin

    serializer_class = serializers.UserPointsHistorySerializers

    def get_queryset(self):
        if not hasattr(self.request.user, "userprofile"):
            raise exceptions.NotFound()
        return models.UserPointsHistory.objects.filter(user=self.request.user.userprofile).order_by("-created_on")