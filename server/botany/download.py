import io
import re
import zipfile

from .models import Bot


def get_bots():
    def increment_name(name):
        file_name, file_extension = name.rsplit(".", 1)

        match = re.match(r".+(\(d+\))", file_name)
        if match is None:
            return f"{file_name} (1).{file_extension}"

        num = int(match.group(1)) + 1
        return f"{file_name} ({num}).{file_extension}"

    bots_info = Bot.objects.filter(
        state__in=["active", "house"]
    ).values_list("name", "code")

    bots_to_return = {}
    for name, code in bots_info:
        while name in bots_to_return:
            name = increment_name(name)
        bots_to_return[name] = code

    return bots_to_return.items()

def download_active_bots():
    bots = get_bots()

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "x") as zip_file:
        for name, code in bots:
            zip_file.writestr(name, code)

    return zip_buffer
