from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AccessPass


class AccessPassListCreateView(generics.ListCreateAPIView):
    queryset = AccessPass.objects.all()
    permission_classes = [IsAuthenticated]


class AccessPassDetailView(generics.RetrieveAPIView):
    queryset = AccessPass.objects.all()
    permission_classes = [IsAuthenticated]


class AccessPassValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pass_id = request.data.get("pass_id")

        try:
            access_pass = AccessPass.objects.get(id=pass_id)
        except AccessPass.DoesNotExist:
            return Response(
                {"detail": "Pass not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not access_pass.is_valid():
            return Response(
                {"detail": "Pass is not valid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Pass is valid."},
            status=status.HTTP_200_OK,
        )
