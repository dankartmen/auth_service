from app import models, schemas
from sqlalchemy.orm import Session

initial_exercises = [
    {
        "title": "Изометрическое напряжение мышц",
        "general_description": "Укрепление мышц без движения в суставе",
        "injury_specific_info": {
            "Перелом конечностей": "Позволяет сохранять мышечный тонус без риска смещения отломков. Рекомендовано в период иммо>            "Эндопротезирование сустава": "Подготовка мышц к нагрузкам после операции. Снижает риск послеоперационных осложнени>        },
        "suitable_for": ["Перелом конечностей", "Эндопротезирование сустава"],
        "max_pain_level": 3,
        "steps": [
            "Напрягите мышцы конечности на 5-7 секунд",
            "Расслабьтесь на 10 секунд",
            "Повторите 10 раз для каждой группы мышц"
        ],
        "tags": ["Без движения", "Начальная стандия"],
        "image_url": "https://alfagym.ru/wp-content/uploads/0/f/7/0f7116f26b4589c244b0dbea5a85868f.png"
    },
    {
        "title": "Нейропластическая гимнастика",
        "general_description": "Восстановление нейромышечного контроля",
        "injury_specific_info": {
            "Инсульт": "Стимулирует нейропластичность мозга через повторяющиеся движения. Помогает восстановить утраченные двигательные функции.",
            "Черепно-мозговая травма": "Улучшает межполушарное взаимодействие. Снижает спастичность мышц после длительной иммобилизациию"
        },
        "suitable_for": ["Инсульт", "Черепно-мозговая травма"],
        "max_pain_level": 2,
        "steps": [
            "Перекрестные движения рук и ног",
            "Зеркальное рисование обеими руками",
            "Упражнения с балансирочной подушкой"
        ],
        "tags": ["Неврология", "Реабилитация"],
        "image_url": "https://fs-thb02.getcourse.ru/fileservice/file/thumbnail/h/f7cf7029e510f783d145a7dfbf012b3a.jpg/s/f1200x/a/27502/sc/236"
    },
    {
        "title": "Пассивная разработка сустава",
        "general_description": "Восстановление подвижности после иммобилизации",
        "suitable_for": ["Разрыв связок", "Эндопротезирование сустава"],
        "max_pain_level": 4,
        "steps": [
            "Медленные сгибания/разгибания в суставе с помощью инструктора или здоровой конечности",
            "По 10 повторений в каждом направлении",
            "2 сеанса в день"
        ],
        "tags": ["Восстановление амплитуды"],
        "image_url": "https://www.garant.ru/files/4/4/1198144/pict159-71833482.png"
    },
    {
        "title": "Дыхательная гимнастика",
        "general_description": "Профилактика осложнений после операции на позвоночнике. Помощь при восстановлении после инсульта",
        "suitable_for": ["Операция на позвоночнике", "Инсульт"],
        "max_pain_level": 2,
        "steps": [
            "Глубокий вдох через нос в течении 4 секунд",
            "Медленный выдох через рот в течении 6 секунд",
            "10 циклов 3 раза в день"
        ],
        "tags": ["Дыхание", "Профилактика"],
        "image_url": "https://avatars.dzeninfra.ru/get-zen_doc/271828/pub_66878cc2e419264ab4d17cea_668791de1cbd0d0f23a4b89e/scale_1200"
    },
    {
        "title": "Тренировка мелкой моторики",
        "general_description": "Восстановление после инсульта",
        "suitable_for": ["Инсульт"],
        "max_pain_level": 3,
        "steps": [
            "Собирание мелких предметов пальцами",
            "Рисование на песке",
            "Растегивание и застегивание пуговиц",
            "15 минут 2 раза в день"
        ],
        "tags": ["Моторика", "Реабилитация"],
        "image_url": "https://www.maam.ru/upload/blogs/detsad-242319-1488213676.jpg"
    },
    {
        "title": "Растяжка ахиллова сухожилия",
        "general_description": "Восстановление после разрыва",
        "suitable_for": ["Разрыв ахиллова сухожилия"],
        "max_pain_level": 5,
        "steps": [
            "Встаньте лицом к стене, руки на груди",
            "Больню ногу оставить назад",
            "Медленно сгибать колени до чувства натяжения",
            "Удерживать 30 секунд, 5 подходов"
        ],
        "tags": ["Растяжка", "Восстановление"],
        "image_url": "https://zdorovko.info/wp-content/uploads/2016/01/rastyajka_ahillovogo_suhojyliya_vozle_stenki.jpg"
    },
    {
        "title": "Стабилизация плечевого сустава",
        "general_description": "После вывиха плеча",
        "suitable_for": ["Вывих плеча"],
        "max_pain_level": 4,
        "steps": [
            "Использование эластичной ленты",
            "Наружная и внутренняя ротация плеча",
            "15 повторений в 3 подхода с контролем амлитуды"
        ],
        "tags": ["Стабильность", "Реабилитация"],
        "image_url": "https://4youngmama.ru/wp-content/uploads/7/9/c/79cb777bbd1047ee0d583746b1edc5e6.jpeg"
    },
    {
        "title": "Восстановление мышц живота",
        "general_description": "После кесарева сечения",
        "suitable_for": ["Кесарево сечение"],
        "max_pain_level": 3,
        "steps": [
            "Лежа на спине с согнутыми коленями, медленно напрягайте мышцы тазового дна",
            "Удерживайте напряжение 5 seconds, 10 повторений",
            "3 раза в день"
        ],
        "tags": ["Послеродовой период", "Мышцы кора"],
        "image_url": "https://mens-physic.ru/images/2021/04/img_16193987794077-1-1024x576.jpg"
    },
    {
        "title": "Дыхание с сопротивлением",
        "general_description": "После абдоминальных операций",
        "suitable_for": ["Аппендэктомия", "Лапароскопические операции"],
        "max_pain_level": 2,
        "steps": [
            "Используйте дыхательный тренажер",
            "Медленный вдох через сопротивление",
            "10 повторений каждые 2 часа",
            "Следите за болевыми ощущениями!"
        ],
        "tags": ["Дыхание", "Реабилитация"],
        "image_url": "https://avatars.mds.yandex.net/i?id=f6ecad553610d5c32bea670c60233dc2-4231472-images-thumbs&n=13"
    },
    {
        "title": "Аквааэробика",
        "general_description": "Помощь при артрите",
        "suitable_for": ["Артрит"],
        "max_pain_level": 3,
        "steps": [
            "Легкие упражнения в бассейне",
            "Медленные махи ногами",
            "Круговые движения суставами",
            "30 минут 3 раза в неделю"
        ],
        "tags": ["Бассейн", "Низкая нагрузка"],
        "image_url": "https://sun9-18.userapi.com/impg/BV58GjcI4fD0jdhBF-8IPvJOGBCOHeTF1jpZDA/un1NfC95nn4.jpg?size=800x800&quality=95&sign=1576edc505725521e370b5641c3f0356&c_uniq_tag=mjAsPQMNyIJ5oIhm54UIyC5GJ8N"
    },
    {
        "title": "Баланс-терапия",
        "general_description": "При рассеяннос склерозе",
        "suitable_for": ["Рассеянный склероз"],
        "max_pain_level": 2,
        "steps": [
            "Встаньте у опоры",
            "Перенос веса тела с ноги на ногу",
            "Удерживайте равновесие на одной ноге",
            "10 минут дважды в день"
        ],
        "tags": ["Баланс", "Координация"],
        "image_url": "https://i.pinimg.com/originals/3b/1d/cb/3b1dcbdb6afa51ca53a25f0706a6983e.jpg"
    }
]
def init_db(db: Session):
    if db.query(models.Exercise).count() > 0:
        return
    for exercise_data in initial_exercises:
        db_exercise = models.Exercise(**exercise_data)
        db.add(db_exercise)

    db.commit()

if __name__ == "__main__":
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()

