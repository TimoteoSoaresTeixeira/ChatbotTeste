# actions/actions.py

import yaml
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from unidecode import unidecode

class ActionExplicarRemedio(Action):
    def name(self) -> Text:
        return "action_explicar_remedio"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            with open('data/expliqueMec.yml', 'r', encoding='utf-8') as file:
                dados_yaml = yaml.safe_load(file)
                base_de_remedios = dados_yaml.get("explicacoes", {})
        except Exception as e:
            print(f"Erro ao ler expliqueMec.yml: {e}")
            dispatcher.utter_message(text="Desculpe, estou com problemas para aceder à minha base de dados agora.")
            return []

        remedio_extraido = next(tracker.get_latest_entity_values("remedio"), None)
        if not remedio_extraido:
            dispatcher.utter_message(response="utter_remedio_nao_identificado")
            return []

        remedio_usuario_normalizado = unidecode(remedio_extraido).lower().strip()
        explicacao_encontrada = None
        nome_original_encontrado = None

        for nome_original_db, explicacao_db in base_de_remedios.items():
            nome_db_normalizado = unidecode(str(nome_original_db)).lower().strip()
            if remedio_usuario_normalizado == nome_db_normalizado:
                explicacao_encontrada = explicacao_db
                nome_original_encontrado = nome_original_db
                break

        if explicacao_encontrada:
            nome_formatado = str(nome_original_encontrado).capitalize()
            dispatcher.utter_message(
                text=f"Claro! O medicamento {nome_formatado} serve para o seguinte:\n{explicacao_encontrada}"
            )
        else:
            dispatcher.utter_message(response="utter_explicacao_nao_encontrada", remedio=remedio_extraido)
        return []
