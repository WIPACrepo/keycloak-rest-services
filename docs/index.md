---
hide:
  - toc
---

# Home

Docs and examples on how to use the automated IceCube account workflow system.

## Quick Links

* [New user registration](new_user)
* [User login](user_login)
* [Password Reset](pwd_reset)
* [Changing institutions](inst_move)
* [Group Membership](group_join)

## System Details

The IceCube account system is composed of multiple parts.  Central to
this is [Keycloak](https://keycloak.icecube.wisc.edu/auth/realms/IceCube/account/),
which is the source of truth for the system and contains all user and
group information.

We also have a web application for easier account actions,
[User Management](https://user-management.icecube.aq/).  This is especially
useful for institution leaders and group administrators, to approve
requests for membership or directly add/remove users.
