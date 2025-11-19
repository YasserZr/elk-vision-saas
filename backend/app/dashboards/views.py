from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class DashboardListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # TODO: Fetch dashboards from MongoDB
        return Response({
            'dashboards': [],
        })
