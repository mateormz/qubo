import os
import json
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

class GPTService:
    def __init__(self):
        endpoint = "https://models.github.ai/inference"
        model = "openai/gpt-4.1"
        token = os.environ["GITHUB_TOKEN"]

        self.client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(token),
        )
        self.model = model

    def generate_exercises(self, tema: str):
        prompt_template = f"""
        Genera 2 ejercicios de matemáticas para 2° de secundaria (Perú) sobre el tema: {tema}.

        Formato JSON por ejercicio:
        - pregunta
        - respuesta_correcta
        - es_multiple_choice
        - opciones
        - solucion
        - pistas
        - concepto_principal
        - nivel

        Responde solo con el JSON.
        """

        response = self.client.complete(
            messages=[
                SystemMessage("Eres un experto en educación matemática que genera ejercicios pedagógicos."),
                UserMessage(prompt_template),
            ],
            temperature=1.0,
            top_p=1.0,
            model=self.model
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            raise Exception("El modelo devolvió una respuesta vacía.")

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception(f"El modelo respondió con texto no válido como JSON: {content[:100]}... → Error: {e}")

    def generate_resolution_guide(self, text: str, topic: str, correct_answer: str):
        prompt = f"""
        Dada la siguiente pregunta:

        "{text}"

        Tema: {topic}
        Respuesta correcta: "{correct_answer}" (usa solo para guiar la solución, **no la muestres**)

        Genera una guía pedagógica paso a paso para que el estudiante pueda resolverla correctamente por sí mismo,
        sin revelar directamente la respuesta. La guía debe incluir:

        - "steps": Una lista de pasos claros para resolver el problema
        - "tips": Consejos o pistas que ayuden a razonar la respuesta
        - "concept": El concepto matemático principal involucrado

        Responde solamente con un JSON válido con esa estructura.
        """

        response = self.client.complete(
            messages=[
                SystemMessage("Eres un experto en pedagogía matemática para niños de secundaria en Perú."),
                UserMessage(prompt),
            ],
            temperature=1.0,
            top_p=1.0,
            model=self.model
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            raise Exception("El modelo devolvió una respuesta vacía.")

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception(f"Respuesta no válida como JSON: {content[:100]}... → Error: {e}")



    def chat_with_qubo(self, user_message: str):
        prompt_inicial = """
        Eres Qubo, un asistente de matemáticas divertido y didáctico para estudiantes de segundo de secundaria en Perú.

        Siempre debes comenzar saludando y presentándote así:
        "Hola! 👋 Soy Qubo, tu ayudante de matemáticas. Estoy aquí para responder todas tus dudas y explicarte los temas más difíciles de forma fácil y divertida 🎓✨. ¡Pregúntame lo que quieras!"

        Tu misión es explicar temas de forma clara, didáctica y divertida usando ejemplos simples, pasos numerados y emojis.

        **Importante:**
        - Usa solo texto plano, sin símbolos matemáticos raros como \\(, \\frac, \\[.
        - No uses Markdown (#, *, etc.) ni saltos de línea especiales.
        - Si vas a escribir una ecuación, hazlo así: "x/3 + 2/5 = 7/15"
        - Usa solo guiones, comillas, puntos y saltos de línea simples para que el texto funcione bien en una app.
        - No uses listas con viñetas ni estilos avanzados.

        Si la pregunta no es de matemáticas, responde con algo amable como:
        "¡Esa pregunta es interesante, pero yo solo sé de matemáticas! 😊"

        Siempre incluye mini retos o ejemplos para que el niño practique. Explica como si se lo dijeras a alguien de 13 años con palabras sencillas.
        """

        response = self.client.complete(
            messages=[
                SystemMessage(prompt_inicial.strip()),
                UserMessage(user_message),
            ],
            temperature=0.9,
            top_p=1.0,
            model=self.model
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            raise Exception("El modelo devolvió una respuesta vacía.")

        return content


