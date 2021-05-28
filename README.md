# keycloak-automation
Automation tooling for [Keycloak](https://www.keycloak.org/)

## Introduction
This repository provides some tooling to automate various tasks for Keycloak. Still in alpha state. Currently there is support for:
- importing and exporting group membership configuration
- importing and exporting groups and associated realm roles

**Note**: the users in the group membership configuration should be existing users. Non existing users are skipped, with a warning.

## Usage
```python
# Process an input csv file of desired user group memberships
# and add/remove users to/from groups accordingly.
python admin.py execute -i <inputfile>

# The same as above, but in check mode, do not actually change anything
python admin.py execute -i <inputfile> -c

# Export users and the groups they are a member of as csv (only usernames)
python admin.py exportcsv

# Export the members of a group (only usernames)
python admin.py exportgroup -n <group name>

# Export groups and associated realm roles as a yaml file
python admin.py export_groups_and_roles -o <outputfile>

# Import groups and associated realm roles from a yaml file
python admin.py import_groups_and_roles -i <inputfile>
```

### Structure of the group memberships csv file:
```csv
username, groups
user1, group_a;group_b
user2, group_a;group_b;group_c
user3, group_b
user4, group_c
etc..
```

## Configuration
The module expects a url to your Keycloak installation, a realm and credentials of a user with realm admin privileges. Currently these need to be configured as env vars, see env_example.sh.
