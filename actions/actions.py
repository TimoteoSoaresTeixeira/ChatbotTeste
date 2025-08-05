# actions/actions.py

import yaml
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset
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
            dispatcher.utter_message(text=f"Claro! O medicamento {nome_formatado} serve para o seguinte:\n{explicacao_encontrada}")
        else:
            dispatcher.utter_message(response="utter_explicacao_nao_encontrada", remedio=remedio_extraido)
        return []

class ActionAdicionarRemedio(Action):
    def name(self) -> Text:
        return "action_adicionar_remedio"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        remedio_entity = next(tracker.get_latest_entity_values("remedio"), None)
        if not remedio_entity:
            dispatcher.utter_message(response="utter_remedio_nao_identificado")
            return []

        remedio_normalizado = unidecode(remedio_entity).lower().strip()
        lista_atual = tracker.get_slot("remedios_list") or []
        nova_lista = lista_atual.copy()

        if remedio_normalizado not in [unidecode(r).lower().strip() for r in nova_lista]:
            nova_lista.append(remedio_entity.strip())
            dispatcher.utter_message(response="utter_remedio_adicionado", remedio=remedio_entity.strip().capitalize())
        else:
            dispatcher.utter_message(response="utter_remedio_ja_adicionado", remedio=remedio_entity.strip().capitalize())
        return [SlotSet("remedios_list", nova_lista)]

class ActionListarRemedios(Action):
    def name(self) -> Text:
        return "action_listar_remedios"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        remedios_list = tracker.get_slot("remedios_list")
        if not remedios_list:
            dispatcher.utter_message(response="utter_lista_vazia")
        else:
            lista_formatada = "\n".join([f"- {remedio.capitalize()}" for remedio in remedios_list])
            dispatcher.utter_message(response="utter_listar_remedios", lista_remedios=lista_formatada)
        return []

class ActionVerificarInteracoes(Action):
    def name(self) -> Text:
        return "action_verificar_interacoes"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        remedios_list = tracker.get_slot("remedios_list")
        if not remedios_list or len(remedios_list) < 2:
            dispatcher.utter_message(response="utter_interacao_lista_insuficiente")
            return []

        try:
            with open('data/interacoes.yml', 'r', encoding='utf-8') as file:
                db_interacoes = yaml.safe_load(file).get('interacoes', [])
        except FileNotFoundError:
            dispatcher.utter_message(text="Desculpe, não tenho um ficheiro de interações para consultar no momento.")
            return []

        remedios_normalizados = [unidecode(r).lower().strip() for r in remedios_list]
        interacoes_encontradas = []

        for i in range(len(remedios_normalizados)):
            for j in range(i + 1, len(remedios_normalizados)):
                remedio1_norm = remedios_normalizados[i]
                remedio2_norm = remedios_normalizados[j]
                for interacao in db_interacoes:
                    pair_norm = {unidecode(p).lower().strip() for p in interacao['pair']}
                    if {remedio1_norm, remedio2_norm} == pair_norm:
                        remedio1_original = remedios_list[i]
                        remedio2_original = remedios_list[j]
                        interacoes_encontradas.append(f"- **Risco entre {remedio1_original.capitalize()} e {remedio2_original.capitalize()}:** {interacao['risco']}")

        if not interacoes_encontradas:
            dispatcher.utter_message(response="utter_sem_interacoes")
        else:
            texto_interacoes = "\n".join(interacoes_encontradas)
            dispatcher.utter_message(response="utter_interacoes_encontradas", interacoes=texto_interacoes)
        return []

# A classe ActionResetarLista foi removida daqui.
