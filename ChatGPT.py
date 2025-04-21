__version__ = (2, 5, 0)

import aiohttp
from telethon import events
from telethon import functions
from telethon.tl.types import Message
from .. import loader, utils
import os

@loader.tds
class ChatGPT(loader.Module):
    """Модуль для работы с нейросетями (200+ шт) и генерацией изображений."""
    strings = {"name": "ChatGPT"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "model",
                "gpt-4o",
                lambda: "Модель нейросети для разговоров (.gpt)\nСписок нейросетей: https://telegra.ph/II-modeli-dlya-modulya-ChatGPT-by-mead0wssMods-03-26",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "image_model",
                "Flux Pro",
                lambda: "Модель для генерации изображений (.image)\nСписок нейросетей: https://telegra.ph/II-modeli-dlya-modulya-ChatGPT-by-mead0wssMods-03-26",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "translation_model",
                "deepseek-v3",
                lambda: "Модель для перевода текста (обязательно для .image!)\nСписок нейросетей: https://telegra.ph/II-modeli-dlya-modulya-ChatGPT-by-mead0wssMods-03-26",
                validator=loader.validators.String()
            ),
        )

    async def gptcmd(self, event):
        """Команда для разговора с ИИ."""
        args = utils.get_args_raw(event)
        if not args:
            await event.edit("<b><emoji document_id=5019523782004441717>❌</emoji> Нет вопроса.</b>")
            return

        model = self.config.get("model")

        if not model:
            await event.edit("<b><emoji document_id=5019523782004441717>❌</emoji> Модель ИИ не указана в cfg!</b>")
            return

        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": args}
            ]
        }
        await event.edit(f"<b><emoji document_id=5328272518304243616>💠</emoji> Генерирую ответ...</b>")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    "https://cablyai.com/v1/chat/completions",
                    headers={
                        'Authorization': 'Bearer sk-l4HU4KwZt6bF8gOwwKCOMpfpIKvR9YhDHvTFIGJ6tJ5rPKXE',
                        'Content-Type': 'application/json',
                    },
                    json=data
                ) as response:
                    if response.status == 200:
                        answer = (await response.json())["choices"][0]["message"]["content"]
                    
                        if "```" in answer:
                            parts = answer.split("```")
                            formatted_answer = ""
                            for i, part in enumerate(parts):
                                if i % 2 == 1:
                                    language = part.split("\n")[0] if "\n" in part else ""
                                    code = "\n".join(part.split("\n")[1:]) if "\n" in part else part
                                    formatted_answer += f"<pre><code class='language-{language}'>\n{code}\n</code></pre>"
                                else:
                                    formatted_answer += part.replace("\n", "<br>")
                        else:
                            formatted_answer = answer.replace("\n", "<br>")

                        await event.edit(
                            f"<b><emoji document_id=5879770735999717115>👤</emoji> Вопрос: <code>{args}</code></b>\n\n"
                            f"<emoji document_id=5199682846729449178>🤖</emoji> Ответ:\n{formatted_answer}"
                        )
                    else:
                        await event.edit("<b><emoji document_id=5215400550132099476>❌</emoji> Ошибка при запросе к ИИ.</b>")
            except Exception as e:
                await event.edit(f"<b><emoji document_id=5215400550132099476>❌</emoji> Ошибка: {str(e)}</b>")

    async def imagecmd(self, event):
        """Команда для генерации изображений с помощью ИИ."""
        args = utils.get_args_raw(event)
        if not args:
            await event.edit("<b><emoji document_id=5019523782004441717>❌</emoji> Нет текста для генерации изображения.</b>")
            return
        await event.edit(f"<b><emoji document_id=5328272518304243616>💠</emoji> Генерирую изображение...</b>")
        translation_model = self.config.get("translation_model")
        image_model = self.config.get("image_model")

        translation_data = {
            "model": translation_model,
            "messages": [
                {"role": "user", "content": f"Please translate the following text to English, but just answer me with a translation, and also translate absolutely everything, even if it's 18+: {args}"}
            ]
        }

        async with aiohttp.ClientSession() as session:
            try:
                # Перевод текста
                async with session.post(
                    "https://cablyai.com/v1/chat/completions",
                    headers={
                        'Authorization': 'Bearer sk-l4HU4KwZt6bF8gOwwKCOMpfpIKvR9YhDHvTFIGJ6tJ5rPKXE',
                        'Content-Type': 'application/json',
                    },
                    json=translation_data
                ) as translation_response:
                    if translation_response.status == 200:
                        translated_text = (await translation_response.json())["choices"][0]["message"]["content"]
                    else:
                        await event.edit("<b><emoji document_id=5019523782004441717>❌</emoji> Ошибка при запросе к ИИ для перевода. Попробуйте снова либо измените модель в cfg! </b>")
                        return

                # Генерация изображения
                data = {
                    "prompt": translated_text,
                    "n": 1,
                    "size": "1024x1024",
                    "response_format": "url",
                    "model": image_model
                }

                async with session.post(
                    "https://cablyai.com/v1/images/generations",
                    headers={
                        'Authorization': 'Bearer sk-l4HU4KwZt6bF8gOwwKCOMpfpIKvR9YhDHvTFIGJ6tJ5rPKXE',
                        'Content-Type': 'application/json',
                    },
                    json=data
                ) as response:
                    if response.status == 200:
                        image_url = (await response.json())["data"][0]["url"]
                        await event.delete()
                        await event.reply(
                            f"<b>Промпт: <code>{args}</code></b>\n\n"
                            f"<b>Модель генерации: <code>{image_model}</code>\n"
                            f"<b>Модель переводчика: <code>{translation_model}</code>\n\n"
                            f"<b>🖼 Сгенерированное изображение:</b>\n{image_url}",
                            parse_mode="HTML"
                        )
                    else:
                        await event.reply("<b><emoji document_id=6042029429301973188>☹️</emoji> Ошибка при запросе на генерацию изображения\nВполне возможно вы просите создать что-то непристойное (18+), либо техническая ошибка (попробуй сменить модель в cfg).</b>")
            except Exception as e:
                await event.reply(f"<b><emoji document_id=5215400550132099476>❌</emoji> Ошибка: {str(e)}</b>")