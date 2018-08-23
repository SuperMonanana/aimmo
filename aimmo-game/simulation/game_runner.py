import time
import threading

from communicator import Communicator
from simulation_runner import ConcurrentSimulationRunner

TURN_TIME = 2


class GameRunner(threading.Thread):
    def __init__(self, worker_manager, game_state, end_turn_callback, django_api_url):
        super(GameRunner, self).__init__()
        self.worker_manager = worker_manager
        self.game_state = game_state
        self.communicator = Communicator(django_api_url=django_api_url,
                                         completion_url=django_api_url + 'complete/')
        self.end_turn_callback = end_turn_callback
        self.simulation_runner = ConcurrentSimulationRunner(communicator=self.communicator,
                                                            game_state=game_state)

    def get_users_to_add(self, game_metadata):
        def player_is_new(_player):
            return _player['id'] not in self.worker_manager.player_id_to_worker.keys()

        return [player['id'] for player in game_metadata['users'] if player_is_new(player)]

    def get_users_to_delete(self, game_metadata):
        def player_in_worker_manager_but_not_metadata(pid):
            return pid not in [player['id'] for player in game_metadata['users']]

        return [player_id for player_id in self.worker_manager.player_id_to_worker.keys()
                if player_in_worker_manager_but_not_metadata(player_id)]

    def update_main_user(self, game_metadata):
        self.game_state.main_avatar_id = game_metadata['main_avatar']

    def get_game_state_for_workers(self):
        player_id_to_game_state = {}
        for player_id, avatar_wrapper in self.game_state.avatar_manager.avatars_by_id.iteritems():
            player_id_to_game_state[player_id] = self.game_state.serialise_for_worker(avatar_wrapper)

        return player_id_to_game_state

    def update_workers(self):
        game_metadata = self.communicator.get_game_metadata()['main']

        users_to_add = self.get_users_to_add(game_metadata)
        users_to_delete = self.get_users_to_delete(game_metadata)

        self.worker_manager.add_workers(users_to_add)
        self.worker_manager.delete_workers(users_to_delete)
        self.game_state.add_avatars(users_to_add)
        self.game_state.delete_avatars(users_to_delete)
        self.worker_manager.update_worker_codes(game_metadata['users'])

        self.update_main_user(game_metadata)
        player_id_to_game_state = self.get_game_state_for_workers()
        self.worker_manager.fetch_all_worker_data(player_id_to_game_state)

    def update_simulation(self, player_id_to_serialised_actions):
        self.simulation_runner.run_single_turn(player_id_to_serialised_actions)
        self.end_turn_callback()

    def run(self):
        while True:
            self.update_workers()
            self.update_simulation(self.worker_manager.get_player_id_to_serialised_actions())
            self.worker_manager.clear_logs()
            time.sleep(TURN_TIME)
