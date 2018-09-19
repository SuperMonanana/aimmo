import logging

from eventlet.greenpool import GreenPool
from concurrent.futures import ThreadPoolExecutor

from ..worker import Worker

LOGGER = logging.getLogger(__name__)


class _WorkerManagerData(object):
    """
    This class is thread safe
    """

    def __init__(self, user_codes):
        self._user_codes = user_codes

    def set_code(self, player):
        self._user_codes[player['id']] = player['code']

    def get_code(self, player_id):
        return self._user_codes[player_id]


class WorkerManager(object):
    """
    Methods of this class must be thread safe unless explicitly stated.
    """
    def __init__(self, port=5000):
        self._data = _WorkerManagerData({})
        self._pool = GreenPool(size=3)
        self.executor = ThreadPoolExecutor()
        self.future_workers = []
        self.player_id_to_worker = {}
        self.port = port

    def get_code(self, player_id):
        return self._data.get_code(player_id)

    def fetch_all_worker_data(self, player_id_to_game_state):
        for player_id, worker in self.player_id_to_worker.iteritems():
            worker.fetch_data(player_id_to_game_state[player_id])

    def get_player_id_to_serialised_actions(self):
        return {player_id: self.player_id_to_worker[player_id].serialised_action for player_id in self.player_id_to_worker}

    def clear_logs(self):
        for worker in self.player_id_to_worker.values():
            worker.log = None

    def create_worker(self, player_id):
        raise NotImplementedError

    def remove_worker(self, player_id):
        raise NotImplementedError

    def update_code(self, player):
        self._data.set_code(player)

    def add_new_worker(self, player_id):
        worker_url_base = self.create_worker(player_id)
        self.player_id_to_worker[player_id] = Worker('{}/turn/'.format(worker_url_base))

    def _parallel_map(self, func, iterable_args):
        return list(self._pool.imap(func, iterable_args))
    
    def _worker_added(self, player_id, on_worker_added):
        def future_callback(future_worker):
            print("PLAYER_ID IN WORKER ADDED: {}".format(player_id))
            if future_worker.cancelled():
                return
            elif future_worker.done():
                worker_url_base = future_worker.result()
                self.player_id_to_worker[player_id] = Worker('{}/turn/'.format(worker_url_base))
                self.future_workers.remove(player_id)
                print("FUTURE WORKERS: {}".format(self.future_workers))
                on_worker_added(player_id)

        return future_callback


    def add_workers(self, users_to_add, on_user_added):
        for user in users_to_add:
            future_worker = self.executor.submit(self.create_worker, user)
            self.future_workers.append(user)
            future_worker.add_done_callback(self._worker_added(user, on_user_added))

    def delete_workers(self, players_to_delete):
        self._parallel_map(self.delete_worker, players_to_delete)

    def delete_worker(self, player):
        del self.player_id_to_worker[player]
        self.remove_worker(player)

    def update_worker_codes(self, players):
        self._parallel_map(self.update_code, players)
