# Ficheiro: actions/actions.py

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import yaml

# --- CARREGAR AS NOSSAS BASES DE CONHECIMENTO ---
try:
    with open('expliqueMec.yml', 'r', encoding='utf-8') as f:
        EXPLICacoes_DB = yaml.safe_load(f).get('explicacoes', {})
except FileNotFoundError:
    print("AVISO: Ficheiro 'expliqueMec.yml' não encontrado. A função de explicação não irá funcionar.")
    EXPLICacoes_DB = {}

try:
    with open('interacoes.yml', 'r', encoding='utf-8') as f:
        INTERACOES_DB = yaml.safe_load(f).get('interacoes', [])
except FileNotFoundError:
    print("AVISO: Ficheiro 'interacoes.yml' não encontrado. A verificação de interações não irá funcionar.")
    INTERACOES_DB = []

# ---------------------------------------------------

class ActionAdicionarRemedio(Action):
    def name(self) -> Text:
        return "action_adicionar_remedio"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        remedio_novo = next(tracker.get_latest_entity_values("remedio"), None)
        if not remedio_novo:
            dispatcher.utter_message(response="utter_pedir_remedio")
            return []
        lista_atual = tracker.get_slot("lista_remedios") or []
        if remedio_novo.lower() not in [remedio.lower() for remedio in lista_atual]:
            lista_atual.append(remedio_novo.title())
        dispatcher.utter_message(response="utter_remedio_adicionado", remedio=remedio_novo.title())
        return [SlotSet("lista_remedios", lista_atual)]

class ActionListarRemedios(Action):
    def name(self) -> Text:
        return "action_listar_remedios"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lista_remedios = tracker.get_slot("lista_remedios")
        if not lista_remedios:
            dispatcher.utter_message(response="utter_lista_vazia")
        else:
            mensagem = "Esta é a sua lista de medicamentos atual:\n"
            for remedio in lista_remedios:
                mensagem += f"- {remedio}\n"
            dispatcher.utter_message(text=mensagem)
        return []

class ActionVerificarInteracoes(Action):
    def name(self) -> Text:
        return "action_verificar_interacoes"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        lista_remedios = tracker.get_slot("lista_remedios")
        dispatcher.utter_message(response="utter_verificando")
        if not lista_remedios or len(lista_remedios) < 2:
            dispatcher.utter_message(text="Preciso de pelo menos dois medicamentos na sua lista para poder verificar as interações.")
            return []
        remedios_utilizador = {r.lower() for r in lista_remedios}
        conflitos_encontrados = []
        for interacao in INTERACOES_DB:
            nomes_interacao = set(interacao['nomes'])
            if nomes_interacao.issubset(remedios_utilizador):
                conflitos_encontrados.append(interacao['descricao'])
        if conflitos_encontrados:
            dispatcher.utter_message(text="Encontrei as seguintes interações potenciais na sua lista:")
            for conflito in conflitos_encontrados:
                dispatcher.utter_message(text=conflito)
        else:
            dispatcher.utter_message(text="✅ Verificação concluída. Não encontrei nenhuma interação grave conhecida entre os medicamentos da sua lista. Lembre-se sempre de consultar um profissional de saúde.")
        return []

class ActionResetarLista(Action):
    def name(self) -> Text:
        return "action_resetar_lista"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet("lista_remedios", [])]

# --- NOSSA NOVA AÇÃO ---
class ActionExplicarRemedio(Action):
    def name(self) -> Text:
        return "action_explicar_remedio"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        remedio_perguntado = next(tracker.get_latest_entity_values("remedio"), None)
        if not remedio_perguntado:
            dispatcher.utter_message(text="Desculpe, não entendi sobre qual remédio você quer saber.")
            return []
        
        # Procura a explicação na nossa base de dados (convertendo para minúsculas)
        explicacao = EXPLICacoes_DB.get(remedio_perguntado.lower())
        
        if explicacao:
            dispatcher.utter_message(text=explicacao)
        else:
            dispatcher.utter_message(response="utter_remedio_nao_encontrado", remedio=remedio_perguntado.title())
            
        return []
