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

