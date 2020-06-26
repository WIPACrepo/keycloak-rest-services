# User Stories

* [Institutional Changes](#institutional-changes)
    * [New user](#new-user)
    * [Second institution](#second-institution)
    * [Changing institution](#changing-institution)
    * [Institution PI removes user](#institution-pi-removes-user)
* [Group Changes](#group-changes)
    * [User asks to join group](#user-asks-to-join-group)
    * [User asks to leave group](#user-asks-to-leave-group)
    * [Group admin adds user to group](#group-admin-adds-user-to-group)
    * [Group admin removes user from group](#group-admin-removes-user-from-group)

## Institutional Changes

### New user

Register a new user that does not exist in the system.

User view workflow:
- load registration page
- submit registration

PI's view workflow:
- get email with link to request
- load request page
- approve request

REST workflow:
- get institution list:
    - Keycloak - get inst groups
- submit registration:
    - Keycloak - user does not already exist
    - DB - put new user record
    - DB - put inst approval record
- PI request page
    - DB - get inst approval record
- PI approval
    - DB - get inst approval record
    - DB - get new user record
    - Keycloak - user creation
    - Keycloak - user added to inst group
    - DB - delete inst approval record
    - DB - delete new user record
    - Email - to user: successful registration, create new password

### Second institution

Add authenticated user to another institution.

User view workflow:
- log in
- land on user dashboard
- go to "add institution" page
- submit request

PI's view workflow
- get email with link to request
- load request page
- approve request

REST workflow:
- get institution list:
    - Keycloak - get inst groups
- submit request:
    - DB - put inst approval record
- PI request page
    - DB - get inst approval record
- PI approval
    - DB - get inst approval record
    - Keycloak - user added to inst group
    - DB - delete inst approval record
    - Email - to user: inst approval

### Changing institution

User is moving from one institution to another.

User view workflow:
- log in
- land on user dashboard
- go to "change institution" page
- submit request

PI's view workflow
- get email with link to request
- load request page
- approve request

REST workflow:
- get institution list:
    - Keycloak - get inst groups
- submit request:
    - DB - put inst removal record
    - DB - put inst approval record
- PI request page
    - DB - get inst approval record
- PI approval
    - DB - get inst approval record
    - DB - get inst removal record
    - Keycloak - user added to new inst group
    - Keycloak - user removed from old inst group
    - DB - delete inst approval record
    - DB - delete inst removal record
    - Email - to user: inst approval

### Institution PI removes user

User left institution, action by PI.

PI's view workflow
- log in
- load admin dashboard
- go to instutition page
- click delete button next to user
- confirm request

REST workflow:
- PI institution page
    - Keycloak - get members of inst
- removal request
    - Keycloak - user removed from inst group

## Group Changes

### User asks to join group

User view workflow:
- log in
- land on user dashboard
- go to "add group" page
- select group from list
- submit request

Group admin's view workflow
- get email with link to request
- load request page
- approve request

REST workflow:
- add group page
    - Keycloak - get list of (public) groups
- group request
    - DB - put group approval record
- Admin group request page
    - DB - get group approval record
- Admin group approval
    - Keycloak - add user to group
    - DB - delete group approval record
    - Email - to user: group approval

### User asks to leave group

User view workflow:
- log in
- land on user dashboard
- click delete button next to group
- confirm request

REST Workflow:
- group removal request
    - Keycloak - remove user from group

### Group admin adds user to group

Group admin's view workflow
- log in
- load admin dashboard
- go to group page
- go to group user add page
- approve request

REST Workflow:
- Admin group page
    - Keycloak - get users in group and experiment
- Admin group approval
    - Keycloak - add user to group

### Group admin removes user from group

Group admin's view workflow
- log in
- load admin dashboard
- go to group page
- click delete button next to user
- confirm request

REST Workflow:
- Admin group page
    - Keycloak - get users in group and experiment
- Admin group removal
    - Keycloak - remove user from group
