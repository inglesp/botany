from datetime import datetime, timedelta, timezone
import io
from unittest.mock import patch
import zipfile

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import override_settings, TestCase, RequestFactory

from botany import views
from botany.tests import factories


YESTERDAY = datetime.now(timezone.utc) - timedelta(days=1)
TOMORROW = datetime.now(timezone.utc) + timedelta(days=1)


@override_settings(BOTANY_TOURNAMENT_CLOSE_AT=TOMORROW)
class APISubmitViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = factories.create_user("anne@example.com", "Anne Example")
        self.user.api_token = "TOKEN"
        self.user.save()

    def test_request_with_valid_token_receives_200(self):
        data = {
            "bot_name": "bot.py",
            "bot_code": factories.bot_code("randobot")
        }

        request = self.factory.post("", data=data)
        request.META["HTTP_AUTHORIZATION"] = "TOKEN"

        response = views.api_submit(request)

        self.assertEqual(response.status_code, 200)

    def test_request_with_invalid_token_receives_401(self):
        request = self.factory.post("")
        request.META["HTTP_AUTHORIZATION"] = "WRONG-TOKEN"

        response = views.api_submit(request)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.content.decode("utf-8"),
            "Invalid API token"
        )


class DownloadBotsCodeBaseTestCase(TestCase):
    # Base test case for all download views

    def setUp(self):
        self.factory = RequestFactory()
        self.user = factories.create_user("anne@example.com", "Anne Example")
        self.test_data = [
            {
                "name": "annes_bot.py",
                "code": factories.bot_code("randobot")
            },
            {
                "name": "brads_bot.py",
                "code": "from __future__ import braces"
            }
        ]
        factories.create_bot(self.user, **(self.test_data[0]))
        brad = factories.create_user("brad@example.com", "Brad Example")
        factories.create_bot(brad, **(self.test_data[1]))


@override_settings(BOTANY_TOURNAMENT_CLOSE_AT=YESTERDAY)
class DownloadBotsCodeHelperFunctionTest(DownloadBotsCodeBaseTestCase):

    def test_download_bots_code_helper_function(self):
        result = views._download_bots_code()

        self.assertEqual(result["Content-Type"], "application/zip")
        self.assertEqual(
            result["Content-Disposition"],
            "attachment; filename=bots.zip"
        )

        # test that we can process response as a zipfile
        result_buffer = io.BytesIO(result.getvalue())
        with zipfile.ZipFile(result_buffer, "r") as zf:
            self.assertCountEqual(
                zf.namelist(), ["annes_bot.py", "brads_bot.py"]
            )
            for bot in self.test_data:
                with zf.open(bot["name"]) as test_file:
                    self.assertEqual(
                        io.TextIOWrapper(test_file).read(),
                        bot["code"]
                    )


@override_settings(BOTANY_TOURNAMENT_CLOSE_AT=YESTERDAY)
class DownloadBotsCodeViewTest(DownloadBotsCodeBaseTestCase):

    def test_download_bots_code_view(self):
        request = self.factory.get("")
        request.user = self.user

        with patch("botany.views._download_bots_code") as _download_bots_code:
            _download_bots_code.return_value = \
                "Return value of _download_bots_code"

            result = views.download_bots_code(request)

        self.assertEqual(
            result,
            "Return value of _download_bots_code"
        )

    def test_cannot_download_bots_code_anonymously(self):
        request = self.factory.get("")
        request.user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            views.download_bots_code(request)

    @override_settings(BOTANY_TOURNAMENT_CLOSE_AT=TOMORROW)
    def test_cannot_download_bots_code_before_tournament_ends(self):
        request = self.factory.get("")
        request.user = self.user

        with self.assertRaises(Http404):
            views.download_bots_code(request)


@override_settings(BOTANY_TOURNAMENT_CLOSE_AT=YESTERDAY)
class APIDownloadBotsCodeViewTest(DownloadBotsCodeBaseTestCase):

    def setUp(self):
        super().setUp()
        self.user.api_token = "TOKEN"
        self.user.save()

    def test_api_download_bots_code_view(self):
        request = self.factory.get("")
        request.META["HTTP_AUTHORIZATION"] = "TOKEN"

        with patch("botany.views._download_bots_code") as _download_bots_code:
            _download_bots_code.return_value = \
                "Return value of _download_bots_code"

            result = views.api_download_bots_code(request)

        self.assertEqual(
            result,
            "Return value of _download_bots_code"
        )

    def test_request_with_invalid_token_receives_401(self):
        request = self.factory.get("")
        request.META["HTTP_AUTHORIZATION"] = "WRONG-TOKEN"

        response = views.api_download_bots_code(request)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.content.decode("utf-8"),
            "Invalid API token"
        )

    @override_settings(BOTANY_TOURNAMENT_CLOSE_AT=TOMORROW)
    def test_cannot_download_bots_code_via_api_before_tournament_ends(self):
        request = self.factory.get("")
        request.META["HTTP_AUTHORIZATION"] = "TOKEN"

        response = views.api_download_bots_code(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content.decode("utf-8"),
            "Unable to download bots until tournament is complete"
        )
