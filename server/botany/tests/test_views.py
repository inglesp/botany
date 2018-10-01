from datetime import datetime, timedelta, timezone
import io
import json
from unittest.mock import patch
import zipfile

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import override_settings, TestCase, RequestFactory

from botany import views
from botany.tests import factories


@override_settings(
    BOTANY_TOURNAMENT_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1)
)
class DownloadBotsCodeViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = factories.create_user("anne@example.com", "Anne Example")

    def test_download_bots_code_view(self):
        request = self.factory.get("")
        request.user = self.user

        file_name = "test.txt"
        file_content = "test test test"

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "x") as zip_file:
            zip_file.writestr(file_name, file_content)

        with patch("botany.views.get_active_bots") as get_active_bots:
            get_active_bots.return_value = zip_buffer

            result = views.download_bots_code(request)

        # finally test some things

        self.assertEqual(zip_buffer.getvalue(), result.getvalue())
        self.assertEqual(result["Content-Type"], "application/zip")
        self.assertEqual(
            result["Content-Disposition"],
            "attachment; filename=bots.zip"
        )

        # test that we can process response as a zipfile
        result_buffer = io.BytesIO(result.getvalue())
        with zipfile.ZipFile(result_buffer, "r") as zf:
            self.assertEqual(zf.namelist(), ["test.txt"])
            with zf.open("test.txt") as test_file:
                self.assertEqual(
                    io.TextIOWrapper(test_file).read(),
                    "test test test"
                )

    def test_cannot_download_bots_code_anonymously(self):
        request = self.factory.get("")
        request.user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            views.download_bots_code(request)

    @override_settings(
        BOTANY_TOURNAMENT_CLOSE_AT=datetime.now(
            timezone.utc) + timedelta(days=1)
    )
    def test_cannot_download_bots_code_before_tournament_ends(self):
        request = self.factory.get("")
        request.user = self.user

        with self.assertRaises(Http404):
            views.download_bots_code(request)


@override_settings(
    BOTANY_TOURNAMENT_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1)
)
class APIDownloadBotsCodeViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = factories.create_user("anne@example.com", "Anne Example")
        self.user.api_token = "TOKEN"
        self.user.save()

    def test_api_download_bots_code_view(self):
        request = self.factory.get("")
        request.META["HTTP_AUTHORIZATION"] = "TOKEN"

        bots_data = [{"name": "test.py", "code": "test test"}]

        with patch("botany.views.get_active_bots_for_api") as get_active_bots:
            get_active_bots.return_value = bots_data

            result = views.api_download_bots_code(request)

        self.assertEqual(json.loads(result.content), bots_data)

    @override_settings(
        BOTANY_TOURNAMENT_CLOSE_AT=datetime.now(
            timezone.utc) + timedelta(days=1)
    )
    def test_cannot_download_bots_code_via_api_before_tournament_ends(self):
        request = self.factory.get("")
        request.META["HTTP_AUTHORIZATION"] = "TOKEN"

        response = views.api_download_bots_code(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content.decode("utf-8"),
            "Unable to download bots while tournament is still in progress"
        )
