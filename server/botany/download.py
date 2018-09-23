import io
import zipfile

from .models import Bot


def get_bots():
    return Bot.objects.filter(
        state__in=["active", "house"]
    ).values_list("name", "code")


def download_active_bots():
    bots = get_bots()

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "x") as zip_file:
        for name, code in bots:
            zip_file.writestr(name, code)

    return zip_buffer
