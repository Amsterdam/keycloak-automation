# keycloak-automation
Automation tooling for [Keycloak](https://www.keycloak.org/)

## Introduction
This repository provides some tooling to automate various tasks for Keycloak. Still in alpha state. Currently there is support for:
- exporting users and the groups they belong to
- processing an input file with users and the groups they should belong to and configure a Keycloak realm accordingly

**Note**: the only thing the script does is add (or remove) existing users to (or from) existing groups. It does not create any users or groups.

## Usage
```python
# Process an input csv file of users and groups and add/remove users to/from groups accordingly.
python admin.py execute -i <inputfile>

# Process an input csv file of users and groups, in check mode
python admin.py execute -i <inputfile> -c

# Export users and the groups they belong to as csv (only usernames)
python admin.py exportcsv

# Export the users in a group (only usernames)
python admin.py exportgroup -n <group name>
```

### Structure of the csv file:
```csv
username, groups
user1, group_a;group_b
user2, group_a;group_b;group_c
user3, group_b
user4, group_c
etc..
```

## Configuration
The script expects an url to your Keycloak installation, a realm and credentials of a user with realm admin privileges. Currently these need to be configured as env vars, see env_example.sh.
