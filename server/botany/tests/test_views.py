from datetime import datetime, timedelta, timezone
import io
from unittest.mock import patch
import zipfile

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import override_settings, TestCase, RequestFactory

from botany import actions, views


@override_settings(
    BOTANY_TOURNAMENT_CLOSE_AT=datetime.now(timezone.utc) - timedelta(days=1)
)
class DownloadBotsCodeViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = actions.create_user("anne@example.com", "Anne Example")

    def test_download_bots_code_view(self):
        request = self.factory.get("")
        request.user = self.user

        file_name = "test.txt"
        file_content = "test test test"

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "x") as zip_file:
            zip_file.writestr(file_name, file_content)

        with patch("botany.views.download_active_bots") as download_bots:
            download_bots.return_value = zip_buffer

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

        response = views.download_bots_code(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content.decode("utf-8"),
            "Unable to download bots while tournament is still in progress"
        )