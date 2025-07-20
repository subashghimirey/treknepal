from rest_framework import generics, permissions
from rest_framework.response import Response
from treknepal.treks.models import TimsApplication
from treknepal.treks.serializers import TimsApplicationSerializer


class TimsApplicationListCreateView(generics.ListCreateAPIView):
    queryset = TimsApplication.objects.all()
    serializer_class = TimsApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user = self.request.user
        return TimsApplication.objects.filter(user=user)


class TimsApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TimsApplication.objects.all()
    serializer_class = TimsApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return TimsApplication.objects.filter(user=user)
