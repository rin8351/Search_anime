import json
import os
from openai import OpenAI
from typing import Literal
from pydantic import BaseModel
import time
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Структура для структурированного ответа
class AnimeAnalysis(BaseModel):
    hero: Literal["male", "female", "unknown"]
    violence: Literal["да", "нет"]
    mystical: Literal["да", "нет"]
    love_vibes: Literal["да", "нет"]
    approximateage: str

def analyze_anime_with_ai(title: str, description: str, client: OpenAI) -> dict:
    """
    Анализирует аниме с помощью AI API
    
    Args:
        title: Название аниме
        description: Описание аниме
        client: Клиент OpenAI API
        
    Returns:
        dict с ключами hero и violence
    """
    prompt = f"""Прочитай описание аниме и ответь на вопросы:

Название аниме: {title}

Описание: {description}

Вопросы:
1. Кто в главной роли? Определи пол главного героя/героини:
   - male (если главный герой - парень/мужчина)
   - female (если главная героиня - девушка/женщина)
   - unknown (если непонятно, несколько главных героев разного пола, или информации недостаточно)

2. Есть ли в сюжете жестокость и насилие?
   - да (ТОЛЬКО если явно упоминаются: сражения, убийства, войны, боевые действия, физическое насилие)
   - нет (смерть персонажа, трагедия, болезнь, несчастный случай БЕЗ упоминания насилия = НЕТ)

3. Есть ли в сюжете мистика или волшебство?
   - да (если есть упоминания о магии, сверхъестественном, мистике, волшебстве)
   - нет (если такого не упоминается)

4. Что является ОСНОВОЙ сюжета?
   - да (если ГЛАВНЫЙ фокус - это развитие романтических отношений между персонажами)
   - нет (если основа - карьера, хобби, спорт, работа, учёба, приключения, а романтика идёт фоном или условием)

5. Укажи возраст одного главного героя/героини если он есть в описании. 
Если нет- оцени примерно в виде цифры или диапазона исходя из сюжета, поступков героев, наличия работы, школы, университета. 

Проанализируй описание внимательно и дай структурированный ответ."""

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # Можно изменить на gpt-4o или другую модель
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу аниме. Отвечай точно и структурированно."},
                {"role": "user", "content": prompt}
            ],
            response_format=AnimeAnalysis,
            temperature=0.3
        )
        
        result = completion.choices[0].message.parsed
        return {
            "hero": result.hero,
            "violence": result.violence,
            "mystical": result.mystical,
            "love_vibes": result.love_vibes,
            "approximateage": result.approximateage
        }
    
    except Exception as e:
        print(f"Ошибка при анализе '{title}': {e}")
        return {
            "hero": "unknown",
            "violence": "нет",
            "mystical": "нет",
            "love_vibes": "нет",
            "approximateage": "unknown"
        }

def process_anime_database(input_file: str, output_file: str, api_key: str):
    """
    Обрабатывает базу данных аниме с помощью AI
    
    Args:
        input_file: Путь к входному JSON файлу
        output_file: Путь к выходному JSON файлу
        api_key: API ключ OpenAI
    """
    # Инициализация клиента OpenAI
    client = OpenAI(api_key=api_key)
    
    # Загрузка данных
    print(f"Загрузка данных из {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        anime_data = json.load(f)
    
    total_anime = len(anime_data)
    print(f"Найдено {total_anime} аниме для анализа\n")
    
    # Обработка каждого аниме
    processed_count = 0
    for title, anime_info in anime_data.items():
        processed_count += 1
        print(f"[{processed_count}/{total_anime}] Анализируем: {title}")
        
        # Получаем описание
        description = anime_info.get('description', '')
               
        # Анализируем с помощью AI
        analysis = analyze_anime_with_ai(title, description, client)
        
        # Добавляем результаты анализа
        anime_info['hero'] = analysis['hero']
        anime_info['violence'] = analysis['violence']
        anime_info['mystical'] = analysis['mystical']
        anime_info['love_vibes'] = analysis['love_vibes']
        anime_info['approximateage'] = analysis['approximateage']
        print(f"  ✓ Герой: {analysis['hero']}, Жестокость: {analysis['violence']}, Мистика: {analysis['mystical']}, Любовь: {analysis['love_vibes']}, Возраст: {analysis['approximateage']}")
        
        # Небольшая задержка, чтобы не превышать лимиты API
        time.sleep(0.5)
        
        # Сохраняем промежуточные результаты каждые 10 аниме
        if processed_count % 10 == 0:
            print(f"\n💾 Сохранение промежуточных результатов...")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(anime_data, f, ensure_ascii=False, indent=2)
    
    # Финальное сохранение
    print(f"\n✅ Анализ завершен! Сохранение результатов в {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(anime_data, f, ensure_ascii=False, indent=2)

    
def main():
    # Настройки
    input_file = "data/processed/filtered_romantic.json"
    output_file = "data/processed/filtered_with_ai.json"
    
    # Получение API ключа из переменных окружения
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠️ API ключ не найден!")
        print("Пожалуйста, создайте файл .env и добавьте:")
        print("OPENAI_API_KEY=your_api_key_here")
        return
    
    # Обработка базы данных
    process_anime_database(input_file, output_file, api_key)

if __name__ == "__main__":
    main()


