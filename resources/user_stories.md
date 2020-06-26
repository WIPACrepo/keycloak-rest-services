# User Stories

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

Approval workflow:
- new user record
- inst approval record
- inst approval action
- user added to Keycloak
- user added to inst
- email to create new password

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

Workflow:
- inst approval record
- inst approval action
- user added to inst
 
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

Workflow:
- inst approval record
- inst removal record
- inst approval action
- user added to new inst
- user removed from old inst

### Institution PI removes user

User left institution, action by PI.

PI's view workflow
- log in
- load admin dashboard
- go to instutition page
- submit request

Worflow:
- user removed from old inst 

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

Workflow:
- group approval record
- group approval action
- user added to group

### User asks to leave group

User view workflow:
- log in
- land on user dashboard
- click delete button next to group
- confirm request

Workflow:
- user removed from group

### Group admin adds user to group

Group admin's view workflow
- log in
- load admin dashboard
- go to group page
- go to group user add page
- approve request

Workflow:
- user added to group

### Group admin removes user from group

Group admin's view workflow
- log in
- load admin dashboard
- go to group page
- click delete button next to user
- confirm request

Workflow:
- user removed from group


