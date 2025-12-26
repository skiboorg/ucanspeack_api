import os
import json
import re
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from lesson.models import (
    Course, Level, Lesson, Module, ModuleBlock,
    Video, Phrase, LessonItem, DictionaryGroup, DictionaryItem
)

class Command(BaseCommand):
    help = "Импорт курса из локальной папки"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Путь к папке курса (с course_info.json)")

    def handle(self, *args, **options):
        course_path = options["path"]

        if not os.path.exists(course_path):
            self.stderr.write(f"Папка {course_path} не найдена")
            return

        course_info_path = os.path.join(course_path, "course_info.json")
        if not os.path.exists(course_info_path):
            self.stderr.write("course_info.json не найден")
            return

        with open(course_info_path, "r", encoding="utf-8") as f:
            levels_data = json.load(f)

        course_title = os.path.basename(course_path)
        course, _ = Course.objects.get_or_create(title=course_title, defaults={"slug": slugify(course_title)})
        self.stdout.write(f"Курс: {course.title}")

        for level_data in levels_data:
            level_title = level_data["title"]
            level_slug = level_data.get("title_slug") or slugify(level_title)
            level_folder = os.path.join(course_path, level_slug)

            if not os.path.exists(level_folder):
                self.stderr.write(f"Папка уровня не найдена: {level_folder}")
                continue

            level, _ = Level.objects.get_or_create(
                course=course,
                title=level_title,
                defaults={
                    "slug": level_slug,
                    "description": level_data.get("description"),
                    "url": level_data.get("url"),
                }
            )
            self.stdout.write(f"Уровень: {level.title}")

            lessons_json_path = os.path.join(level_folder, f"{level_slug}.json")
            if not os.path.exists(lessons_json_path):
                self.stderr.write(f"lessons JSON не найден: {lessons_json_path}")
                continue

            with open(lessons_json_path, "r", encoding="utf-8") as f:
                lessons_data = json.load(f)

            lessons_folder = os.path.join(level_folder, "lessons")
            if not os.path.exists(lessons_folder):
                self.stderr.write(f"Папка lessons не найдена: {lessons_folder}")
                continue

            for lesson_data in lessons_data:
                lesson_title = lesson_data["title"]
                lesson_slug = lesson_data.get("title_slug") or slugify(lesson_title)
                lesson_short_description = lesson_data.get("short_description") or slugify(lesson_title)
                lesson_folder = os.path.join(lessons_folder, lesson_slug)

                if not os.path.exists(lesson_folder):
                    self.stderr.write(f"Папка урока не найдена: {lesson_folder}")
                    continue

                lesson, _ = Lesson.objects.get_or_create(
                    level=level,
                    title=lesson_title,
                    short_description=lesson_short_description,
                    defaults={
                        "slug": lesson_slug,
                        "url": lesson_data.get("url"),
                        "mp3": lesson_data.get("mp3"),
                    }
                )
                self.stdout.write(f"Урок: {lesson.title}")

                # --- Словарь ---
                dict_path = os.path.join(lesson_folder, "dictionary.json")
                if os.path.exists(dict_path):
                    with open(dict_path, "r", encoding="utf-8") as f:
                        dictionary = json.load(f)
                    for group_name, items in dictionary.items():
                        group, _ = DictionaryGroup.objects.get_or_create(
                            lesson=lesson,
                            title=group_name
                        )
                        for item in items:
                            DictionaryItem.objects.create(
                                group=group,
                                text_ru=item.get("ru"),
                                text_en=item.get("en"),
                                sound=item.get("sound")
                            )

                # --- Модули ---
                for file in os.listdir(lesson_folder):
                    if not file.endswith(".json") or file == "dictionary.json":
                        continue

                    module_path = os.path.join(lesson_folder, file)
                    with open(module_path, "r", encoding="utf-8") as f:
                        module_data = json.load(f)

                    match = re.search(r"\[([^\]]+)\]", file)
                    if match:
                        mod_title = match.group(1)  # берём то, что внутри скобок
                        index, _, _ = file.partition("_")
                    else:
                        # fallback, если скобок нет
                        index, _, mod_title = file.partition("_")
                        mod_title = mod_title.replace(".json", "").replace("_", " ").strip()

                    # index, _, mod_title = file.partition("_")
                    # mod_title = mod_title.replace(".json", "").replace("_", " ").strip()
                    module, _ = Module.objects.get_or_create(
                        lesson=lesson,
                        title=mod_title,
                        defaults={"index": index.strip()}
                    )

                    # --- Блоки модуля ---
                    for i, block_data in enumerate(module_data):
                        if not isinstance(block_data, dict):
                            continue

                        block = ModuleBlock.objects.create(
                            module=module,
                            sorting=int(block_data.get("sorting", i)),
                            caption=block_data.get("caption"),
                            type3_content=block_data.get("type3_content", [])
                        )

                        # --- Фразы ---
                        for item in block_data.get("items", []):
                            LessonItem.objects.create(
                                block=block,
                                text_ru=item.get("ru"),
                                text_en=item.get("en"),
                                sound=item.get("sound")
                            )

                        # --- Видео ---
                        for vid_data in block_data.get("videos", []):
                            video = Video.objects.create(
                                block=block,  # привязываем к ModuleBlock
                                video_src=vid_data.get("video_src")
                            )
                            print('phrases',vid_data.get("phrases", []))
                            for phrase_data in vid_data.get("phrases", []):
                                Phrase.objects.create(
                                    video=video,  # привязываем к видео
                                    start_time=phrase_data.get("start_time"),
                                    end_time=phrase_data.get("end_time"),
                                    text_en=phrase_data.get("text_en"),
                                    text_ru=phrase_data.get("text_ru"),
                                    sound=phrase_data.get("sound")
                                )

        self.stdout.write(self.style.SUCCESS("Импорт завершён успешно!"))
