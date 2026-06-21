"""
Upload views for the Bond Discovery Engine.

This module contains the API endpoint used to upload a CSV bond universe file.
The uploaded file is validated and stored as the local csv_provider source.

Endpoint:
    POST /api/discover-bonds/upload-csv/

Expected multipart field:
    file
"""

from rest_framework import parsers, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bonds.discovery.csv_upload_service import (
    CSVUploadError,
    validate_and_store_uploaded_csv,
)


class BondUniverseCSVUploadAPIView(APIView):
    """
    Upload and replace the CSV bond universe used by csv_provider.

    Authentication:
        Required.

    Request:
        multipart/form-data with field:
            file: .csv file

    Response:
        Upload summary.
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        """
        Handle CSV upload request.
        """
        uploaded_file = request.FILES.get("file")

        try:
            upload_summary = validate_and_store_uploaded_csv(uploaded_file)
        except CSVUploadError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "CSV bond universe uploaded successfully.",
                "upload": upload_summary,
            },
            status=status.HTTP_200_OK,
        )