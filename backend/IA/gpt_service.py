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
        Genera 20 ejercicios de matemáticas para 2° de secundaria (Perú) sobre el tema: {tema}.

        Requisitos:
        1. Formato JSON:
        - 6 ejercicios fáciles
        - 7 ejercicios medios
        - 7 ejercicios difíciles

        2. Estructura cada ejercicio con:
        - pregunta
        - respuesta_correcta
        - es_multiple_choice
        - opciones
        - solucion
        - pistas
        - concepto_principal
        - nivel

        Usa contexto peruano. Responde solo con el JSON.
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
        return json.loads(content)
