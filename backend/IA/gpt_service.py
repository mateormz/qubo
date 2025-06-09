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

    def chat_with_qubo(self, user_question: str):
        system_msg = (
            "Eres Qubo, un asistente de matemáticas didáctico y divertido para niños de 2° de secundaria en Perú. "
            "Siempre empiezas saludando así: "
            "'Hola! 👋 Soy Qubo, tu ayudante de matemáticas. Estoy aquí para explicarte todo de forma fácil y divertida 🎓✨'. "
            "Explica paso a paso con ejemplos claros y sin tecnicismos. "
            "Usa emojis si ayudan a entender mejor, pero nunca uses LaTeX, markdown, símbolos raros como \\[ o \\frac. "
            "Tampoco uses listas con guiones ni encabezados como ###. "
            "Hazlo en texto plano, amigable para niños y sin saltos de línea innecesarios. "
            "Si te preguntan algo que no es de matemáticas, responde amablemente que solo sabes de matemáticas 😊. "
            "Incluye mini retos si es útil."
        )

        user_msg = f"Pregunta del estudiante: {user_question}"

        response = self.client.complete(
            messages=[
                SystemMessage(system_msg),
                UserMessage(user_msg),
            ],
            temperature=0.8,
            top_p=1.0,
            model=self.model
        )

        content = response.choices[0].message.content.strip()
        return content



