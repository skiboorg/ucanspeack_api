from lesson.models import Lesson, Module, LessonItem, Phrase, DictionaryItem, OrthographyItem
from train.models import Topic, AudioFile, Phrase as TrainerPhrase

SEARCH_CONFIG = [
    {
        "key": "lessons",
        "model": Lesson,
        "fields": ["title"],
        "values": ["id", "title", "slug"],
    },
    {
        "key": "modules",
        "model": Module,
        "fields": ["title"],
        "values": ["id", "title", "lesson_id"],
    },
    {
        "key": "lesson_items",
        "model": LessonItem,
        "fields": ["text_ru", "text_en"],
        "values": ["id", "text_ru", "text_en", "block_id"],
    },
    {
        "key": "phrases",
        "model": Phrase,
        "fields": ["text_ru", "text_en"],
        "values": ["id", "text_ru", "text_en", "video_id"],
    },
    {
        "key": "dictionary",
        "model": DictionaryItem,
        "fields": ["text_ru", "text_en"],
        "values": ["id", "text_ru", "text_en", "group_id"],
    },
    {
        "key": "orthography",
        "model": OrthographyItem,
        "fields": ["ru_text", "en_text"],
        "values": ["id", "ru_text", "en_text", "lesson_id"],
    },
    {
        "key": "trainer_topics",
        "model": Topic,
        "fields": ["name"],
        "values": ["id", "name", "slug", "level_id"],
    },
    {
        "key": "trainer_audio",
        "model": AudioFile,
        "fields": ["name"],
        "values": ["id", "name", "topic_id"],
    },
    {
        "key": "trainer_phrases",
        "model": TrainerPhrase,
        "fields": ["text_ru", "text_en"],
        "values": ["id", "text_ru", "text_en", "topic_id"],
    },
]
