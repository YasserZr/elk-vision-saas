from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class AlertListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # TODO: Fetch alerts from MongoDB
        return Response({
            'alerts': [],
        })
