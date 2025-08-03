import yaml
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset

# --- FUNÇÃO AUXILIAR PARA CARREGAR E LIMPAR OS DADOS ---
# Isto evita repetir código e garante que os dados são carregados da mesma forma.
def carregar_base_remedios():
    with open('data/expliqueMec.yml', 'r', encoding='utf-8') as file:
        dados_yaml = yaml.safe_load(file)
        # AQUI ESTÁ A CORREÇÃO PRINCIPAL:
        # Acessamos a "gaveta" 'explicacoes' antes de ler os itens.
        base_de_remedios = dados_yaml.get('explicacoes', {})
        
        # Normalizamos os nomes dos remédios para a busca funcionar sempre.
        return {str(k).strip().lower(): v for k, v in base_de_remedios.items()}

class ActionAdicionarRemedio(Action):
    def __init__(self):
        self.db_remedios = carregar_base_remedios()

    def name(self) -> Text:
        return "action_adicionar_remedio"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        remedio_entity = next(tracker.get_latest_entity_values("remedio"), None)

        if not remedio_entity:
            dispatcher.utter_message(response="utter_remedio_nao_identificado")
            return []

        remedio_normalizado = remedio_entity.strip().lower()

        if remedio_normalizado not in self.db_remedios:
            dispatcher.utter_message(response="utter_remedio_nao_existe", remedio=remedio_entity)
            return []

        remedios_list = tracker.get_slot("remedios_list") or []

        if remedio_normalizado not in remedios_list:
            remedios_list.append(remedio_normalizado)
            dispatcher.utter_message(response="utter_remedio_adicionado", remedio=remedio_entity.capitalize())
        else:
            dispatcher.utter_message(response="utter_remedio_ja_adicionado", remedio=remedio_entity.capitalize())

        return [SlotSet("remedios_list", remedios_list)]

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

class ActionExplicarRemedio(Action):
    def __init__(self):
        self.db_remedios = carregar_base_remedios()

    def name(self) -> Text:
        return "action_explicar_remedio"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        remedio_entity = next(tracker.get_latest_entity_values("remedio"), None)

        if not remedio_entity:
            dispatcher.utter_message(response="utter_remedio_nao_identificado")
            return []

        remedio_normalizado = remedio_entity.strip().lower()
        explicacao = self.db_remedios.get(remedio_normalizado)

        if explicacao:
            resposta = f"Claro! O medicamento {remedio_entity.capitalize()} serve para o seguinte:\n\n{explicacao}"
            dispatcher.utter_message(text=resposta)
        else:
            dispatcher.utter_message(response="utter_explicacao_nao_encontrada", remedio=remedio_entity)

        return []

class ActionVerificarInteracoes(Action):
    def __init__(self):
        with open('data/interacoes.yml', 'r', encoding='utf-8') as file:
            self.db_interacoes = yaml.safe_load(file).get('interacoes', [])

    def name(self) -> Text:
        return "action_verificar_interacoes"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        remedios_list = tracker.get_slot("remedios_list")

        if not remedios_list or len(remedios_list) < 2:
            dispatcher.utter_message(response="utter_interacao_lista_insuficiente")
            return []

        interacoes_encontradas = []
        for i in range(len(remedios_list)):
            for j in range(i + 1, len(remedios_list)):
                remedio1 = remedios_list[i]
                remedio2 = remedios_list[j]

                for interacao in self.db_interacoes:
                    pair = set(interacao['pair'])
                    if set([remedio1, remedio2]) == pair:
                        interacoes_encontradas.append(
                            f"- **Risco entre {remedio1.capitalize()} e {remedio2.capitalize()}:** {interacao['risco']}"
                        )

        if not interacoes_encontradas:
            dispatcher.utter_message(response="utter_sem_interacoes")
        else:
            texto_interacoes = "\n".join(interacoes_encontradas)
            dispatcher.utter_message(response="utter_interacoes_encontradas", interacoes=texto_interacoes)

        return []

class ActionResetarLista(Action):
    def name(self) -> Text:
        return "action_resetar_lista"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="Ok, a sua lista de medicamentos foi limpa.")
        return [AllSlotsReset()]
