from datetime import datetime, timedelta, timezone
import io
import json
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
        test_data = [
            {
                "name": "annes_bot.py",
                "code": factories.bot_code("randobot")
            },
            {
                "name": "brads_bot.py",
                "code": "from __future__ import braces"
            }
        ]
        factories.create_bot(self.user, **(test_data[0]))
        brad = factories.create_user("brad@example.com", "Brad Example")
        factories.create_bot(brad, **(test_data[1]))

        request = self.factory.get("")
        request.user = self.user
        result = views.download_bots_code(request)

        self.assertEqual(result["Content-Type"], "application/zip")
        self.assertEqual(
            result["Content-Disposition"],
            "attachment; filename=bots.zip"
        )

        # test that we can process response as a zipfile
        result_buffer = io.BytesIO(result.getvalue())
        with zipfile.ZipFile(result_buffer, "r") as zf:
            self.assertEqual(zf.namelist(), ["annes_bot.py", "brads_bot.py"])
            for bot in test_data:
                with zf.open(bot["name"]) as test_file:
                    self.assertEqual(
                        io.TextIOWrapper(test_file).read(),
                        bot["code"]
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
        test_data = [
            {
                "name": "annes_bot.py",
                "code": factories.bot_code("randobot")
            },
            {
                "name": "brads_bot.py",
                "code": "from __future__ import braces"
            }
        ]
        factories.create_bot(self.user, **(test_data[0]))
        brad = factories.create_user("brad@example.com", "Brad Example")
        factories.create_bot(brad, **(test_data[1]))

        request = self.factory.get("")
        request.META["HTTP_AUTHORIZATION"] = "TOKEN"
        result = views.api_download_bots_code(request)

        default_maxDiff = self.maxDiff
        self.maxDiff = None

        print(len(json.loads(result.content)))
        self.assertEqual(
            json.loads(result.content),
            test_data
        )

        self.maxDiff = default_maxDiff

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
