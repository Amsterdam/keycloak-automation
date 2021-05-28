import os
import sys
import argparse
import logging
import csv
import yaml

from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakGetError
from settings import kc_base_url, kc_realm, kc_username, kc_password

logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthorizationManager:
    checkmode = False
    _group_lookup = None

    def __init__(self):
        self.admin = KeycloakAdmin(
            server_url=kc_base_url,
            username=kc_username,
            password=kc_password,
            realm_name=kc_realm,
            verify=True
        )

    def get_group_lookup(self):
        """ Create a dictionary that maps group name to group id """
        if not self._group_lookup:
            groups = self.admin.get_groups()
            self._group_lookup = dict()
            for group in groups:
                logger.info(f'group name: {group["name"]}')
                self._group_lookup[group['name']] = group['id']
        return self._group_lookup

    def get_users_current_state(self, group_lookup):
        """
        Create a dictionary thats maps username to a set of
        the names of the groups that the user is currently a member of
        """
        users_current = dict()

        for group_name in group_lookup:
            group_id = group_lookup[group_name]
            members = self.admin.get_group_members(group_id)
            for member in members:
                username = member['username']
                if username == 'kc_username' or username.startswith('service-account-'):
                    logger.info(f'Skipping {username}')
                    continue
                if not username in users_current:
                    users_current[username] = set()
                users_current[username].add(group_name)
        return users_current

    def get_users_desired_state(self, path_to_csv):
        """
        Read input from csv and output a dictionary that maps username to a set of
        the names of the groups that the user is a member of
        """
        users_desired = {}
        with open(path_to_csv) as csv_file:
            csv_reader = csv.DictReader(csv_file, skipinitialspace=True, delimiter=',')
            for row in csv_reader:
                users_desired[row['username']] = set(row['groups'].split(';'))
        return users_desired

    def export_users_current_csv(self, users_current):
        """
        Export usernames and the groups that the user is a member of, in csv format:
        user001, group001;group002
        """
        print('username, groups')
        users_current_sorted = dict(sorted(users_current.items()))
        for user in users_current_sorted:
            groups = ';'.join(users_current[user])
            print(f'{user}, {groups}')

    def export_groups_and_roles(self, outputfile):
        """
        Export the groups and the realm roles attached to the group as a yaml file.
        This only exports the groups and roles as such, not the members of the group.
        """
        export = {'groups': []}
        groups = self.admin.get_groups()
        for group in groups:
            group['roles'] = self.admin.get_group_realm_roles(group['id'])
            export['groups'].append(group)
        if outputfile:
            with open(outputfile, 'w') as file:
                yaml.dump(export, file)
        else:
            yaml.dump(export, sys.stdout)

    def import_groups_and_roles(self, inputfile):
        """
        Import the groups and the realm roles attached to the group from a yaml file.
        This only imports groups and roles as such, not the members of the group.
        """
        with open(inputfile) as f:
            groups_data = yaml.load(f, Loader=yaml.FullLoader)
        for group in groups_data['groups']:
            realm_roles = []
            for role in group['roles']:
                role_repr = self.create_role_if_not_exists(role)
                realm_roles.append(role_repr)
            del group['id']
            del group['roles']
            self.admin.create_group(group, None, True)
            group_id = self.get_group_id_by_group_name(group['name'])
            self.admin.assign_group_realm_roles(group_id, realm_roles)

    def create_role_if_not_exists(self, role):
        """
        Create a realm role if it does not exist yet
        """
        try:
            role_repr = self.admin.get_realm_role(role['name'])
        except KeycloakGetError as e:
            # sketchy error handling.. create role if it doesn't exist
            if '404' in str(e):
                del role['containerId']
                del role['id']
                self.admin.create_realm_role(role)
                role_repr = self.admin.get_realm_role(role['name'])
        return role_repr

    def get_group_id_by_group_name(self, group_name):
        group_path = f'/{group_name}'
        group = self.admin.get_group_by_path(group_path)
        if not group:
            logger.warning(f'Group {group_name} not found')
            return False
        return group['id']

    def export_group_members(self, group_name):
        """
        Make an export of all members of a group (username only)
        """
        group_id = self.get_group_id_by_group_name(group_name)
        members = self.admin.get_group_members(group_id)
        print(group_name)
        for member in members:
            username = member['username']
            print(f'- {username}')

    def get_user_groups(self, username, state_lookup):
        """
        Return the set of groups that user is a member of from the lookup
        """
        if username not in state_lookup:
            return set()
        return state_lookup[username]

    def add_user_to_groups(self, user, add_to_groups):
        username = user['username']
        for group_name in add_to_groups:
            logger.info(f'Add {username} to group {group_name}')
            try:
                group_id = self.get_group_lookup()[group_name]
            except KeyError:
                logger.warning(f'Group unknown: {group_name}')
            else:
                self.add_user_to_group(user['id'], group_id)

    def remove_user_from_groups(self, user, remove_from_groups):
        username = user['username']
        for group_name in remove_from_groups:
            logger.info(f'Remove {username} from group {group_name}')
            try:
                group_id = self.get_group_lookup()[group_name]
            except KeyError:
                logger.warning(f'Group unknown: {group_name}')
            else:
                self.remove_user_from_group(user['id'], group_id)

    def add_user_to_group(self, user_id, group_id):
        if not self.checkmode:
            self.admin.group_user_add(user_id, group_id)

    def remove_user_from_group(self, user_id, group_id):
        if not self.checkmode:
            self.admin.group_user_remove(user_id, group_id)

    def get_to_desired_state(self, path_to_csv):
        """
        Read in a csv with desired user group memberships.
        Compare to the current state and change it to the desired state
        """
        logger.info(f'Get user groups in desired state')
        logger.info(f'Base url: {kc_base_url}')
        logger.info(f'Realm: {kc_realm}')
        logger.info(f'Username: {kc_username}')

        group_lookup = self.get_group_lookup()
        users_current_state = self.get_users_current_state(group_lookup)
        users_desired_state = self.get_users_desired_state(path_to_csv)

        # make list of all usernames that are either in the current or desired set
        users_list = [*users_current_state] + [*users_desired_state]
        users_list = list(set(users_list))  # make users list unique and sorted
        users_list.sort()

        for username in users_list:
            # exclude service accounts and this admin user
            if username == 'kc_username' or username.startswith('service-account-'):
                logger.info(f'Skipping {username}')
                continue
            current_groups = self.get_user_groups(username, users_current_state)
            desired_groups = self.get_user_groups(username, users_desired_state)
            
            remove_from_groups = current_groups - desired_groups
            add_to_groups = desired_groups - current_groups
            if not remove_from_groups and not add_to_groups:
                # Nothing to do for this user
                continue

            logger.info(f'Get user id for {username}')
            user_id = self.admin.get_user_id(username)
            if user_id is None:
                logger.warning(f'User unknown: {username}')
                continue

            user = {
                'id': user_id,
                'username': username
            }
            self.remove_user_from_groups(user, remove_from_groups)
            self.add_user_to_groups(user, add_to_groups)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', help='Command to execute')
    parser.add_argument('-i', '--inputfile', help='Input file to process')
    parser.add_argument('-o', '--outputfile', help='Output file to write to')
    parser.add_argument('-c', '--checkmode', help='Run in check mode', action='store_true')
    parser.add_argument('-n', '--name', help='Name of entity')
    args = parser.parse_args()
    cmd = args.cmd
    inputfile = args.inputfile
    outputfile = args.outputfile
    
    AuthorizationManager = AuthorizationManager()

    logger.info(f'Connected to realm {kc_realm}')

    if args.checkmode:
        logger.info('Running in checkmode')
        AuthorizationManager.checkmode = True

    available_cmds = ['execute', 'exportcsv', 'export_group_members',
                      'export_groups_and_roles', 'import_groups_and_roles']

    if not cmd in available_cmds:
        print(f'Invalid command: {cmd}')
        print('Available commands: ')
        for c in available_cmds:
            print(f'- {c}')
        sys.exit()

    if cmd == 'execute':
        AuthorizationManager.get_to_desired_state(inputfile)
    if cmd == 'exportcsv':
        group_lookup = AuthorizationManager.get_group_lookup()
        users_current = AuthorizationManager.get_users_current_state(group_lookup)
        AuthorizationManager.export_users_current_csv(users_current)
    if cmd == 'export_group_members':
        if not args.name:
            sys.exit('Please provide a group name to export')
        AuthorizationManager.export_group_members(args.name)
    if cmd == 'export_groups_and_roles':
        AuthorizationManager.export_groups_and_roles(outputfile)
    if cmd == 'import_groups_and_roles':
        AuthorizationManager.import_groups_and_roles(inputfile)

