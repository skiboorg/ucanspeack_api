import json
import os
from django.core.management.base import BaseCommand
import requests
from urllib.parse import urlparse
from django.utils.text import slugify
from django.core.files.base import ContentFile
from train.models import Course, Level, Topic, AudioFile, Phrase
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

class Command(BaseCommand):
    help = 'Импорт курса из папки с levels.json'

    def handle(self, *args, **options):
        course_dir = input("Введите путь к папке курса (где лежит levels.json): ").strip()
        levels_json_path = os.path.join(course_dir, "levels.json")

        if not os.path.exists(levels_json_path):
            self.stdout.write(self.style.ERROR(f"Файл {levels_json_path} не найден"))
            return

        # Название курса берём из имени папки
        course_name = os.path.basename(os.path.abspath(course_dir))
        course_slug = slugify(course_name)

        course, created = Course.objects.get_or_create(
            slug=course_slug,
            defaults={"name": course_name}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Создан курс: {course.name}"))
        else:
            self.stdout.write(self.style.WARNING(f"Курс уже существует: {course.name}"))

        # Загружаем уровни
        with open(levels_json_path, encoding="utf-8") as f:
            levels_data = json.load(f)
        x=1
        for lvl_data in levels_data:
            lvl_name = lvl_data.get("name") or "Unnamed Level"
            lvl_slug = lvl_data.get("slug") or slugify(lvl_name)
            lvl_desc = lvl_data.get("description")
            lvl_url = lvl_data.get("url")
            lvl_icon = lvl_data.get("icon")

            # level, _ = Level.objects.get_or_create(
            #     course=course,
            #     slug=lvl_slug,
            #     order=x,
            #     defaults={
            #         "name": lvl_name,
            #         "description": lvl_desc,
            #         "url": lvl_url,
            #         "icon": lvl_icon
            #     }
            # )

            level, created = Level.objects.get_or_create(
                course=course,
                slug=lvl_slug,
                defaults={
                    "name": lvl_name,
                    "description": lvl_desc,
                    "url": lvl_url,
                    "icon": lvl_icon,
                    "order": x
                }
            )
            if not created:
                # Обновляем нужные поля
                level.name = lvl_name
                level.description = lvl_desc
                level.url = lvl_url
                level.icon = lvl_icon
                level.order = x
                level.save()

            x += 1
            self.stdout.write(self.style.SUCCESS(f"  Уровень: {level.name}"))

            # Папка с уроками внутри уровня
            level_dir = os.path.join(course_dir, lvl_data.get("slug"))

            if not os.path.exists(level_dir):
                self.stdout.write(self.style.WARNING(f"Папка уровня '{lvl_name}' не найдена"))
                continue
            x = 1
            # Перебираем все подпапки уровня
            for lesson_folder in os.listdir(level_dir):
                lesson_dir = os.path.join(level_dir, lesson_folder)
                if not os.path.isdir(lesson_dir):
                    continue

                lessons_json_path = os.path.join(lesson_dir, "levels.json")
                if not os.path.exists(lessons_json_path):
                    self.stdout.write(self.style.WARNING(f"   levels.json для урока в {lesson_dir} не найден"))
                    continue

                # читаем урок
                with open(lessons_json_path, encoding="utf-8") as f:
                    lesson_data = json.load(f)

                # lesson_data - это один урок
                topic_name = lesson_data.get("name") or "Unnamed Topic"
                topic_slug = lesson_data.get("slug") or slugify(topic_name)
                topic_desc = lesson_data.get("description", "")
                topic_url = lesson_data.get("url", "")
                topic_order = lesson_data.get("order", "")

                topic, created = Topic.objects.get_or_create(
                    level=level,
                    slug=topic_slug,
                    defaults={
                        "name": topic_name,
                        "description": topic_desc,
                        "url": topic_url,
                        "order": topic_order.split('/')[1],
                        "order_txt": topic_order
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"    Тема создана: {topic.name}"))
                    x+=1
                else:
                    self.stdout.write(self.style.WARNING(f"    Тема уже существует: {topic.name}"))

                # Audio files
                for audio_data in lesson_data.get("audio_files", []):
                    audio_name = audio_data.get("name")
                    audio_slug = audio_data.get("slug") or slugify(audio_name)
                    af,_=AudioFile.objects.get_or_create(
                        topic=topic,
                        slug=audio_slug,
                        defaults={
                            "name": audio_name,
                            "mp3": audio_data.get("mp3"),
                            "description": audio_data.get("description"),
                            "order": audio_data.get("order")
                        }
                    )
                    download_file_if_needed(af, "file", audio_data.get("mp3"))

                # Phrases
                for phrase_data in lesson_data.get("phrases", []):
                    phrase,_=Phrase.objects.get_or_create(
                        topic=topic,
                        text_ru=phrase_data.get("text_ru"),
                        text_en=phrase_data.get("text_en"),
                        defaults={
                            "sound": phrase_data.get("mp3"),
                            "order": int(phrase_data.get("order"))
                        }
                    )
                    download_file_if_needed(phrase, "file", phrase_data.get("mp3"))

        self.stdout.write(self.style.SUCCESS("✅ Импорт курса завершён!"))
