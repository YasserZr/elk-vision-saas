from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class LogSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # TODO: Implement Elasticsearch query
        query = request.query_params.get('q', '')
        return Response({
            'query': query,
            'results': [],
            'total': 0,
        })
