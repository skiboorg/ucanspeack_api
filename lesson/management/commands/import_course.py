import os
import json
import re
import requests
from urllib.parse import urlparse
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from lesson.models import (
    Course, Level, Lesson, Module, ModuleBlock,
    Video, Phrase, LessonItem, DictionaryGroup, DictionaryItem
)

BASE_DOMAIN = "https://platform.ucanspeak.ru"




def normalize_url(url: str) -> str:
    if not url:
        return None

    url = url.strip()

    # если относительный путь
    if url.startswith("/"):
        url = BASE_DOMAIN + url

    # если без схемы
    elif not url.startswith("http://") and not url.startswith("https://"):
        url = BASE_DOMAIN + "/" + url.lstrip("/")

    # убираем #t=0.1 и прочие якоря
    url = url.split("#")[0]

    return url

def filefield_is_valid(field):
    """
    Проверяет:
    - есть ли путь в БД
    - существует ли файл
    - размер > 0
    """

    if not field:
        print('not field')
        return False
    print('fn',field.name)
    try:
        if not field.name:
            print('not field.name')
            return False

        path = field.path

        if not os.path.exists(path):
            print('not os.path.exists')
            return False

        if os.path.getsize(path) == 0:
            print('os.path.getsize(path) == 0')
            return False

        return True
    except Exception:
        print('Exception')
        return False

def download_file_if_needed(model_instance, field_name, url):
    """
    Скачивает файл ТОЛЬКО если поле пустое
    """
    if not url:
        return False

    # если файл уже есть — не качаем
    field = getattr(model_instance, field_name)
    print(field)
    print(url,filefield_is_valid(field))
    if filefield_is_valid(field):
        # файл уже нормальный
        return False
    print(model_instance)

    url = normalize_url(url)

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ Ошибка скачивания: {url} | {e}")
        return False

    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or "file.bin"

    field.save(filename, ContentFile(r.content), save=True)
    return True

def download_file(url):
    if not url:
        return None, None

    url = normalize_url(url)

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ Ошибка скачивания: {url} | {e}")
        return None, None

    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)

    if not filename:
        filename = "file.bin"

    return filename, ContentFile(r.content)


class Command(BaseCommand):
    help = "Импорт курса с автоскачиванием всех файлов"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Путь к папке курса")

    def handle(self, *args, **options):
        course_path = options["path"]

        if not os.path.exists(course_path):
            self.stderr.write(f"Папка не найдена: {course_path}")
            return

        course_info_path = os.path.join(course_path, "course_info.json")
        if not os.path.exists(course_info_path):
            self.stderr.write("course_info.json не найден")
            return

        with open(course_info_path, "r", encoding="utf-8") as f:
            levels_data = json.load(f)

        course_title = os.path.basename(course_path)
        course, _ = Course.objects.get_or_create(
            title=course_title,
            defaults={"slug": slugify(course_title)}
        )

        self.stdout.write(self.style.SUCCESS(f"📘 Курс: {course.title}"))



        for level_data in levels_data:
            level_title = level_data["title"]
            level_slug = level_data.get("title_slug") or slugify(level_title)

            level, _ = Level.objects.get_or_create(
                course=course,
                title=level_title,
                defaults={
                    "slug": level_slug,
                    "description": level_data.get("description"),
                    "url": level_data.get("url"),
                }
            )

            self.stdout.write(self.style.SUCCESS(f"  📗 Уровень: {level.title}"))

            lessons_json_path = os.path.join(course_path, level_slug, f"{level_slug}.json")

            if not os.path.exists(lessons_json_path):
                self.stderr.write(f"JSON не найден: {lessons_json_path}")
                continue

            with open(lessons_json_path, "r", encoding="utf-8") as f:
                lessons_data = json.load(f)

            lessons_folder = os.path.join(course_path, level_slug, "lessons")



            for lesson_data in lessons_data:
                lesson_title = lesson_data["title"]
                lesson_slug = lesson_data.get("title_slug") or slugify(lesson_title)

                lesson_folder = os.path.join(lessons_folder, lesson_slug)
                table_json_path = os.path.join(lesson_folder, "table_1.json")

                table_image_base64 = None

                if os.path.exists(table_json_path):
                    with open(table_json_path, "r", encoding="utf-8") as f:
                        table_data = json.load(f)
                        table_image_base64 = table_data.get("image_base64")

                lesson, _ = Lesson.objects.get_or_create(
                    level=level,
                    title=lesson_title,
                    defaults={
                        "table": table_image_base64,
                        "slug": lesson_slug,
                        "url": lesson_data.get("url"),
                        "short_description": lesson_data.get("short_description"),
                        "mp3": lesson_data.get("mp3"),
                    }
                )

                self.stdout.write(self.style.SUCCESS(f"    📙 Урок: {lesson.title}"))

                # # --- MP3 урока ---
                # if lesson_data.get("mp3") and not lesson.file:
                #     filename, content = download_file(lesson_data["mp3"])
                #     if content:
                #         lesson.file.save(filename, content, save=True)
                download_file_if_needed(lesson, "file", lesson_data.get("mp3"))



                dict_path = os.path.join(lessons_folder, lesson_slug, "dictionary.json")
                if os.path.exists(dict_path):
                    with open(dict_path, "r", encoding="utf-8") as f:
                        dictionary = json.load(f)

                    for group_name, items in dictionary.items():
                        group, _ = DictionaryGroup.objects.get_or_create(
                            lesson=lesson,
                            title=group_name
                        )

                        for item in items:
                            di,_ = DictionaryItem.objects.get_or_create(
                                group=group,
                                text_ru=item.get("ru"),
                                text_en=item.get("en"),
                                sound=item.get("sound")
                            )

                            # if item.get("sound"):
                            #     filename, content = download_file(item["sound"])
                            #     if content:
                            #         di.file.save(filename, content, save=True)
                            download_file_if_needed(di, "file", item.get("sound"))



                lesson_folder = os.path.join(lessons_folder, lesson_slug)

                for file in os.listdir(lesson_folder):
                    if not file.endswith(".json") or file == "dictionary.json":
                        continue

                    module_path = os.path.join(lesson_folder, file)

                    with open(module_path, "r", encoding="utf-8") as f:
                        module_data = json.load(f)

                    match = re.search(r"\[([^\]]+)\]", file)
                    if match:
                        mod_title = match.group(1)
                        index, _, _ = file.partition("_")
                    else:
                        index, _, mod_title = file.partition("_")
                        mod_title = mod_title.replace(".json", "").replace("_", " ")

                    mod_title_clean = mod_title.strip()

                    # ❌ пропускаем ненужные модули
                    if mod_title_clean.lower() == "видео" or index.strip().lower() == "table":
                        print("⏭ Пропущен модуль:", file)
                        continue

                    module, _ = Module.objects.get_or_create(
                        lesson=lesson,
                        title=mod_title_clean,
                        index=index.strip()
                    )



                    for i, block_data in enumerate(module_data):
                        if not isinstance(block_data, dict):
                            continue
                        block,_ = ModuleBlock.objects.get_or_create(
                            module=module,
                            sorting=int(block_data.get("sorting", i)),
                            caption=block_data.get("caption"),
                            type3_content=block_data.get("type3_content", "")
                        )



                        for item in block_data.get("items", []):
                            li,_ = LessonItem.objects.get_or_create(
                                block=block,
                                text_ru=item.get("ru"),
                                text_en=item.get("en"),
                                sound=item.get("sound")
                            )

                            # if item.get("sound"):
                            #     filename, content = download_file(item["sound"])
                            #     if content:
                            #         li.file.save(filename, content, save=True)
                            download_file_if_needed(li, "file", item.get("sound"))



                        for vid in block_data.get("videos", []):
                            video,_ = Video.objects.get_or_create(
                                block=block,
                                video_number=vid.get("video_number"),
                                video_src=vid.get("video_src"),
                            )

                            # if vid.get("video_src"):
                            #     filename, content = download_file(vid["video_src"])
                            #     if content:
                            #         video.file.save(filename, content, save=True)
                            download_file_if_needed(video, "file", vid.get("video_src"))



                            for phrase_data in vid.get("phrases", []):
                                phrase,_ = Phrase.objects.get_or_create(
                                    video=video,
                                    start_time=phrase_data.get("start_time"),
                                    end_time=phrase_data.get("end_time"),
                                    text_en=phrase_data.get("text_en"),
                                    text_ru=phrase_data.get("text_ru"),
                                    sound=phrase_data.get("sound")
                                )

                                # if phrase_data.get("sound"):
                                #     filename, content = download_file(phrase_data["sound"])
                                #     if content:
                                #         phrase.file.save(filename, content, save=True)
                                download_file_if_needed(phrase, "file", phrase_data.get("sound"))

        self.stdout.write(self.style.SUCCESS("✅ Импорт полностью завершён!"))
