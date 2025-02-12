from multiprocessing import Value

from database.realm.RealmDatabaseManager import *

WORLD_SESSIONS = []
CURRENT_SESSIONS = Value('i', 0)

# Storing players and sessions by different parameters to keep searches O(1)
# TODO Find better way to do this?
PLAYERS_BY_GUID = {}
PLAYER_BY_NAME = {}
SESSION_BY_GUID = {}
SESSION_BY_NAME = {}


class WorldSessionStateHandler(object):

    @staticmethod
    def add(session):
        if session not in WORLD_SESSIONS:
            CURRENT_SESSIONS.value += 1
            WORLD_SESSIONS.append(session)

    @staticmethod
    def push_active_player_session(session):
        # This is filled upon player successful login (in-world).
        PLAYERS_BY_GUID[session.player_mgr.guid] = session.player_mgr
        PLAYER_BY_NAME[session.player_mgr.player.name.lower()] = session.player_mgr
        SESSION_BY_GUID[session.player_mgr.guid] = session
        SESSION_BY_NAME[session.player_mgr.player.name.lower()] = session

    @staticmethod
    def pop_active_player(player_mgr):
        # Flushed when player leaves the world.
        if player_mgr.player.name in PLAYER_BY_NAME:
            PLAYER_BY_NAME.pop(player_mgr.player.name.lower())
        if player_mgr.guid in PLAYERS_BY_GUID:
            PLAYERS_BY_GUID.pop(player_mgr.guid)

        if player_mgr.player.name in SESSION_BY_NAME:
            SESSION_BY_NAME.pop(player_mgr.player.name.lower())
        if player_mgr.guid in SESSION_BY_GUID:
            SESSION_BY_GUID.pop(player_mgr.guid)

    @staticmethod
    def remove(session):
        if session in WORLD_SESSIONS:
            CURRENT_SESSIONS.value -= 1
            WORLD_SESSIONS.remove(session)
        if session.player_mgr:
            WorldSessionStateHandler.pop_active_player(session.player_mgr)

    @staticmethod
    def disonnect_old_session(new_session):
        if not new_session or not new_session.account_mgr:
            return

        for session in WORLD_SESSIONS:
            if session.account_mgr and session.account_mgr.account.id == new_session.account_mgr.account.id:
                session.disconnect()
                break

    @staticmethod
    def get_world_sessions():
        return list(WORLD_SESSIONS)

    @staticmethod
    def get_process_shared_session_number():
        return CURRENT_SESSIONS.value

    @staticmethod
    def get_session_by_account_id(account_id):
        for session in WORLD_SESSIONS:
            if session.account_mgr and session.account_mgr.account.id == account_id:
                return session
        return None

    @staticmethod
    def get_session_by_character_guid(character_guid):
        return SESSION_BY_GUID.get(character_guid)

    @staticmethod
    def get_session_by_character_name(character_name):
        return SESSION_BY_NAME.get(character_name.lower())
    
    @staticmethod
    def find_player_by_guid(guid_to_search):
        return PLAYERS_BY_GUID.get(guid_to_search)

    @staticmethod
    def find_player_by_name(name_to_search):
        return PLAYER_BY_NAME.get(name_to_search.lower())

    @staticmethod
    def update_players():
        for session in WORLD_SESSIONS:
            if session.player_mgr and session.player_mgr.online:
                if not session.player_mgr.update_lock:
                    session.player_mgr.update()

    @staticmethod
    def save_characters():
        try:
            for session in WorldSessionStateHandler.get_world_sessions():
                if session.player_mgr and session.player_mgr.online:
                    WorldSessionStateHandler.save_character(session.player_mgr)
        except AttributeError:
            pass

    @staticmethod
    def save_character(player_mgr):
        try:
            player_mgr.sync_player()
            RealmDatabaseManager.character_update(player_mgr.player)
        except AttributeError:
            pass
